# -*- coding: utf-8 -*-
"""LightJourney Skill2 — 行程文案生成

复用项目已有的 DeepSeek API 封装和 Prompt 模板，
增加质量评分层，确保文案适合社交分享。

用法：
    from writer import run
    result = run(trip_data={"title": "熊猫基地", "city": "成都", ...})
    print(result["copywriting"])   # AI 生成的口语化文案
    print(result["score"])         # 质量评分
"""

import sys
import os

# 确保能导入 backend 模块
_skill_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_skill_dir, "..", "..", ".."))
_backend_dir = os.path.join(_project_root, "backend")
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from services.ai_service import call_deepseek
from prompts.copywriting import SKILL2_SYSTEM_PROMPT, build_copywriting_user_message


# ---- 质量评分 ----

def score_copy(text: str) -> dict:
    """
    对生成的文案做质量评分：100 分起扣。

    检测维度：
    - 字数 / 句数
    - emoji 使用
    - 词汇丰富度
    - 情感表达
    """
    errors = []
    warnings = []
    infos = []
    score = 100

    if not text or not text.strip():
        errors.append({"level": "ERROR", "item": "输入为空", "detail": "文案内容为空"})
        return {
            "score": 0, "passed": False, "conditional": False,
            "errors": errors, "warnings": warnings, "infos": infos,
            "verdict": "拒绝 — 文案为空",
        }

    stripped = text.strip()

    # ---- 句数检查 ----
    sentences = [s.strip() for s in stripped.replace("！", "。").replace("！", "。").replace("?", "。").split("。") if s.strip()]
    sentence_count = len(sentences)

    if sentence_count < 3:
        warnings.append({"level": "WARNING", "item": "句数过少",
                          "detail": f"仅 {sentence_count} 句，建议 4-6 句"})
    elif sentence_count > 8:
        infos.append({"level": "INFO", "item": "句数偏多",
                       "detail": f"共 {sentence_count} 句，朋友圈建议 4-6 句"})

    # ---- 字数检查 ----
    char_count = len(stripped)
    if char_count < 30:
        warnings.append({"level": "WARNING", "item": "字数过少",
                          "detail": f"仅 {char_count} 字，过于简短"})
    elif char_count > 300:
        infos.append({"level": "INFO", "item": "字数偏多",
                       "detail": f"{char_count} 字，朋友圈建议精简"})

    # ---- emoji 检查 ----
    emoji_count = sum(1 for c in stripped if ord(c) > 0x1F000 or (0x2600 <= ord(c) <= 0x27BF))
    if emoji_count == 0:
        infos.append({"level": "INFO", "item": "缺少 emoji",
                       "detail": "建议添加 1-2 个贴切的表情符号增加亲和力"})
    elif emoji_count > 3:
        warnings.append({"level": "WARNING", "item": "emoji 过多",
                          "detail": f"使用了 {emoji_count} 个 emoji，建议控制在 1-2 个"})

    # ---- 词汇重复检测 ----
    words = stripped.replace("，", " ").replace("。", " ").replace("！", " ").split()
    if len(words) > 10:
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.5:
            warnings.append({"level": "WARNING", "item": "词汇重复",
                              "detail": f"词汇多样性仅 {unique_ratio:.0%}，文案可能显得平淡"})

    # ---- 套话检测 ----
    cliches = ["值得一去", "流连忘返", "美不胜收", "风景如画", "不虚此行",
               "太美了", "太好玩了", "强烈推荐", "一定要来"]
    found_cliches = [c for c in cliches if c in stripped]
    if found_cliches:
        infos.append({"level": "INFO", "item": "套话提醒",
                       "detail": f"含常见套话: {', '.join(found_cliches)}，建议用具体感受替代"})

    # ---- 计算最终评分 ----
    for e in errors:
        score -= 30
    for w in warnings:
        score -= 10
    for i in infos:
        score -= 3
    score = max(0, score)

    has_error = len(errors) > 0
    passed = score >= 80 and not has_error
    conditional = 60 <= score <= 79 and not has_error

    return {
        "score": score,
        "passed": passed,
        "conditional": conditional,
        "errors": errors,
        "warnings": warnings,
        "infos": infos,
        "verdict": (
            "通过" if passed
            else (f"有条件通过 — {len(warnings)} 项建议" if conditional
            else "拒绝 — 存在严重问题需重新生成")
        ),
    }


def generate_copy(trip_data: dict, same_day_trips: list[dict] | None = None) -> dict:
    """
    调用 AI 生成 4-6 句口语化朋友圈文案。

    Args:
        trip_data: 目标行程，至少含 title, city, date。
                   完整字段：title, description, city, date, start_time, end_time
        same_day_trips: 当天同城所有行程（可选，用于上下文串联）

    Returns:
        {
            "copywriting": "今天在成都暴走两万步…",
            "score": 90,
            "passed": True,
            "verdict": "通过",
            "errors": [], "warnings": [], "infos": []
        }
    """
    # 输入校验
    if not trip_data or not isinstance(trip_data, dict):
        errors = [{"level": "ERROR", "item": "输入为空", "detail": "行程数据为空或格式错误"}]
        return {
            "copywriting": "",
            "score": 0, "passed": False, "conditional": False,
            "errors": errors, "warnings": [], "infos": [],
            "verdict": "拒绝 — 输入为空",
        }

    # 处理字符串输入（从 JSON 解析）
    if isinstance(trip_data, str):
        import json
        try:
            trip_data = json.loads(trip_data)
        except json.JSONDecodeError:
            # 当做纯文本行程描述
            trip_data = {"title": trip_data[:50], "description": trip_data, "city": "", "date": ""}

    same_day = same_day_trips or [trip_data]

    user_message = build_copywriting_user_message(trip_data, same_day)

    try:
        raw_text = call_deepseek(SKILL2_SYSTEM_PROMPT, user_message, temperature=0.8)
    except Exception as e:
        errors = [{"level": "ERROR", "item": "AI 调用失败", "detail": str(e)}]
        return {
            "copywriting": "",
            "score": 0, "passed": False, "conditional": False,
            "errors": errors, "warnings": [], "infos": [],
            "verdict": f"拒绝 — AI 调用失败: {str(e)[:100]}",
        }

    score_result = score_copy(raw_text)

    return {
        "copywriting": raw_text,
        **score_result,
    }


# ---- 便捷入口 ----
def run(trip_data: dict, same_day_trips: list[dict] | None = None) -> dict:
    """生成行程文案便捷入口，与 generate_copy 相同。"""
    return generate_copy(trip_data, same_day_trips)


# ---- 命令行入口 ----
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="LightJourney 行程文案生成")
    parser.add_argument("--trip", required=True, help="目标行程 JSON 字符串或 JSON 文件路径")
    parser.add_argument("--context", default=None, help="同天其他行程 JSON 数组（可选）")
    args = parser.parse_args()

    # 解析 trip 参数
    trip_str = args.trip
    if trip_str.strip().endswith(".json"):
        with open(trip_str, "r", encoding="utf-8-sig") as f:
            trip_data = json.load(f)
    else:
        # 容错：PowerShell 单引号处理
        try:
            trip_data = json.loads(trip_str)
        except json.JSONDecodeError:
            # 尝试把单引号替换为双引号后重试
            trip_data = json.loads(trip_str.replace("'", '"'))

    # 解析 context 参数
    same_day = None
    if args.context:
        ctx_str = args.context
        if ctx_str.strip().endswith(".json"):
            with open(ctx_str, "r", encoding="utf-8-sig") as f:
                same_day = json.load(f)
        else:
            try:
                same_day = json.loads(ctx_str)
            except json.JSONDecodeError:
                same_day = json.loads(ctx_str.replace("'", '"'))

    result = run(trip_data, same_day)

    print(f"\n{'='*50}")
    print(f"行程: {trip_data.get('title', '未知')} | 评分: {result['score']}/100 | {result['verdict']}")
    print(f"{'='*50}")
    # 安全打印：Windows GBK 终端可能无法打印 emoji
    _text = result.get("copywriting", "(空)")
    try:
        print(_text)
    except UnicodeEncodeError:
        print(_text.encode("gbk", errors="replace").decode("gbk"))

    if result.get("warnings"):
        print(f"\n⚠️ 警告:")
        for w in result["warnings"]:
            print(f"  - {w['detail']}")
    if result.get("infos"):
        print(f"\n💡 建议:")
        for i in result["infos"]:
            print(f"  - {i['detail']}")
