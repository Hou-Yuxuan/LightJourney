# -*- coding: utf-8 -*-
"""测试 ai_service — JSON 解析容错 / DeepSeek 调用"""
import json
from unittest.mock import patch, MagicMock

import pytest

from services.ai_service import extract_json_from_text, call_deepseek, call_deepseek_json


class TestExtractJsonFromText:
    """JSON 提取容错"""

    def test_direct_parse_array(self):
        text = json.dumps([{"title": "熊猫基地", "budget": 55}])
        result = extract_json_from_text(text)
        assert result == [{"title": "熊猫基地", "budget": 55}]

    def test_direct_parse_object(self):
        text = json.dumps({"copywriting": "今天真开心"})
        result = extract_json_from_text(text)
        assert result == {"copywriting": "今天真开心"}

    def test_extract_from_code_block_json_tag(self):
        text = '好的，这是规划：\n```json\n[{"title":"熊猫基地"}]\n```'
        result = extract_json_from_text(text)
        assert result == [{"title": "熊猫基地"}]

    def test_extract_from_code_block_no_tag(self):
        text = '```\n[{"title":"熊猫基地"}]\n```'
        result = extract_json_from_text(text)
        assert result == [{"title": "熊猫基地"}]

    def test_extract_array_from_text(self):
        text = '这是为您规划的行程：\n[{"title":"熊猫基地","budget":55}]\n祝您旅途愉快！'
        result = extract_json_from_text(text)
        assert result == [{"title": "熊猫基地", "budget": 55}]

    def test_extract_object_from_text(self):
        text = '生成文案如下：\n{"copywriting":"今天很开心"}\n请查收'
        result = extract_json_from_text(text)
        assert result == {"copywriting": "今天很开心"}

    def test_extract_nested_array(self):
        text = '行程包含多条：\n[{"name":"A","tags":["美食","自然"]},{"name":"B"}]\n完毕'
        result = extract_json_from_text(text)
        assert len(result) == 2
        assert result[0]["name"] == "A"

    def test_extract_nested_object(self):
        text = '{"trip":{"title":"熊猫基地","details":{"budget":55}}}'
        result = extract_json_from_text(text)
        assert result["trip"]["details"]["budget"] == 55

    def test_prefer_code_block_over_loose_text(self):
        text = '建议去成都。\n```json\n[{"title":"熊猫基地"}]\n```\n另外也可以考虑[宽窄巷子]'
        result = extract_json_from_text(text)
        assert result == [{"title": "熊猫基地"}]

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="返回为空"):
            extract_json_from_text("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="返回为空"):
            extract_json_from_text("   \n\t  ")

    def test_no_json_raises(self):
        with pytest.raises(ValueError, match="无法解析为 JSON"):
            extract_json_from_text("这不是 JSON，只是普通文本。")


class TestCallDeepseek:
    """DeepSeek API 调用 — 通过 mock _make_request"""

    @patch("services.ai_service._make_request")
    def test_successful_call(self, mock_request):
        mock_request.return_value = "你好，这是生成的文案"

        with patch("services.ai_service.DEEPSEEK_API_KEY", "sk-test-key"):
            result = call_deepseek("你是助手", "帮我写文案")
            assert result == "你好，这是生成的文案"

    @patch("services.ai_service.httpx.Client")
    def test_retry_on_failure(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.post.side_effect = [
            Exception("Connection timeout"),
            MagicMock(
                status_code=200,
                json=lambda: {"choices": [{"message": {"content": "重试成功"}}]},
            ),
        ]
        mock_client_cls.return_value = mock_client

        with patch("services.ai_service.DEEPSEEK_API_KEY", "sk-test-key"):
            with patch("services.ai_service.AI_MAX_RETRIES", 1):
                result = call_deepseek("prompt", "message")
                assert result == "重试成功"
                assert mock_client.post.call_count == 2

    @patch("services.ai_service.httpx.Client")
    def test_retry_exhausted(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.post.side_effect = Exception("timeout")
        mock_client_cls.return_value = mock_client

        with patch("services.ai_service.DEEPSEEK_API_KEY", "sk-test-key"):
            with patch("services.ai_service.AI_MAX_RETRIES", 1):
                with pytest.raises(RuntimeError, match="超时"):
                    call_deepseek("prompt", "message")
                assert mock_client.post.call_count == 2

    @patch("services.ai_service.httpx.Client")
    def test_retry_exhausted_other_error(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.post.side_effect = Exception("Internal server error")
        mock_client_cls.return_value = mock_client

        with patch("services.ai_service.DEEPSEEK_API_KEY", "sk-test-key"):
            with patch("services.ai_service.AI_MAX_RETRIES", 1):
                with pytest.raises(RuntimeError, match="AI 服务调用失败"):
                    call_deepseek("prompt", "message")

    def test_missing_api_key(self):
        with patch("services.ai_service.DEEPSEEK_API_KEY", ""):
            with pytest.raises(ValueError, match="API Key 未配置"):
                call_deepseek("prompt", "message")

    def test_placeholder_api_key(self):
        with patch("services.ai_service.DEEPSEEK_API_KEY", "sk-your-api-key-here"):
            with pytest.raises(ValueError, match="API Key 未配置"):
                call_deepseek("prompt", "message")

    @patch("services.ai_service._make_request")
    def test_empty_response(self, mock_request):
        mock_request.return_value = ""

        with patch("services.ai_service.DEEPSEEK_API_KEY", "sk-test-key"):
            result = call_deepseek("prompt", "message")
            assert result == ""

    @patch("services.ai_service._make_request")
    def test_none_response(self, mock_request):
        """当 _make_request 返回空字符串时正确处理"""
        mock_request.return_value = ""

        with patch("services.ai_service.DEEPSEEK_API_KEY", "sk-test-key"):
            result = call_deepseek("prompt", "message")
            assert result == ""


class TestCallDeepseekJson:
    """组合调用 + JSON 解析"""

    @patch("services.ai_service.call_deepseek")
    def test_returns_parsed_json(self, mock_call):
        mock_call.return_value = json.dumps([{"title": "熊猫基地"}])

        with patch("services.ai_service.DEEPSEEK_API_KEY", "sk-test-key"):
            result = call_deepseek_json("system", "user")
            assert result == [{"title": "熊猫基地"}]

    @patch("services.ai_service.call_deepseek")
    def test_handles_wrapped_json(self, mock_call):
        mock_call.return_value = '```json\n[{"title":"宽窄巷子"}]\n```'

        with patch("services.ai_service.DEEPSEEK_API_KEY", "sk-test-key"):
            result = call_deepseek_json("system", "user")
            assert result == [{"title": "宽窄巷子"}]
