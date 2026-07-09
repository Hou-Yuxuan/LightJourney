# -*- coding: utf-8 -*-
"""AI 服务 — DeepSeek API 调用封装（httpx 直连，兼容内部网关 SSL）"""
import json
import re
import logging
import time

import httpx

from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

logger = logging.getLogger(__name__)

# 超时与重试配置
AI_TIMEOUT_SECONDS = 30
AI_MAX_RETRIES = 1

# Chat Completions 端点
CHAT_URL = f"{DEEPSEEK_BASE_URL.rstrip('/')}/v1/chat/completions"


def _make_request(messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096) -> str:
    """
    发送 HTTP 请求到推理网关，返回模型回复文本。

    内部网关使用自签名证书，跳过 SSL 验证。
    """
    if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == "sk-your-api-key-here":
        raise ValueError("DeepSeek API Key 未配置，请检查 .env 文件中的 DEEPSEEK_API_KEY")

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    last_error = None
    for attempt in range(AI_MAX_RETRIES + 1):
        try:
            with httpx.Client(verify=False, timeout=AI_TIMEOUT_SECONDS) as client:
                resp = client.post(
                    CHAT_URL,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                        "Content-Type": "application/json",
                    },
                )

            if resp.status_code != 200:
                error_detail = resp.json().get("error", {}).get("message", resp.text[:200])
                raise RuntimeError(f"API 返回错误 ({resp.status_code}): {error_detail}")

            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return content.strip() if content else ""

        except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError) as e:
            last_error = e
            logger.warning(f"DeepSeek API 连接失败 (attempt {attempt + 1}/{AI_MAX_RETRIES + 1}): {e}")
            if attempt < AI_MAX_RETRIES:
                time.sleep(1)
        except Exception as e:
            last_error = e
            logger.warning(f"DeepSeek API 调用失败 (attempt {attempt + 1}/{AI_MAX_RETRIES + 1}): {e}")
            if attempt < AI_MAX_RETRIES:
                time.sleep(1)

    error_msg = str(last_error) if last_error else "未知错误"
    if any(kw in error_msg.lower() for kw in ["timeout", "connect", "timed out"]):
        raise RuntimeError("AI 服务响应超时，请稍后重试")
    raise RuntimeError(f"AI 服务调用失败：{error_msg}")


def call_deepseek(system_prompt: str, user_message: str, temperature: float = 0.7) -> str:
    """
    调用 DeepSeek API，返回原始文本内容。

    Args:
        system_prompt: 系统提示词
        user_message: 用户消息
        temperature: 采样温度，默认 0.7

    Returns:
        API 返回的文本内容

    Raises:
        RuntimeError: API 调用失败
        ValueError: API Key 未配置
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    return _make_request(messages, temperature)


def extract_json_from_text(text: str) -> list | dict:
    """
    从 DeepSeek 返回的文本中提取 JSON。

    容错策略（按优先级）：
    1. 直接解析整个文本
    2. 正则匹配提取 ```json ... ``` 代码块
    3. 正则匹配提取最外层 [...] 或 {...}
    4. 以上均失败则抛出 ValueError
    """
    text = text.strip() if text else ""

    if not text:
        raise ValueError("AI 返回为空，请检查网络后重试")

    # 策略 1：直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 策略 2：提取 markdown 代码块中的 JSON
    code_block_pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
    matches = re.findall(code_block_pattern, text, re.DOTALL)
    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue

    # 策略 3：提取最外层 [...] 或 {...}
    array_match = re.search(r'\[.*\]', text, re.DOTALL)
    if array_match:
        try:
            return json.loads(array_match.group(0))
        except json.JSONDecodeError:
            pass

    object_match = re.search(r'\{.*\}', text, re.DOTALL)
    if object_match:
        try:
            return json.loads(object_match.group(0))
        except json.JSONDecodeError:
            pass

    preview = text[:200] + "..." if len(text) > 200 else text
    raise ValueError(f"AI 返回格式异常，无法解析为 JSON。返回内容预览：{preview}")


def call_deepseek_json(system_prompt: str, user_message: str, temperature: float = 0.7) -> list | dict:
    """
    调用 DeepSeek API 并直接返回解析好的 JSON。

    组合 call_deepseek + extract_json_from_text。
    """
    raw_text = call_deepseek(system_prompt, user_message, temperature)
    return extract_json_from_text(raw_text)
