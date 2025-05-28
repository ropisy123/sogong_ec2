import unittest
from unittest.mock import patch, Mock
from adapters.llm_adapter import LLMAdapter


class TestLLMAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = LLMAdapter(
            model_name="gpt-4",
            base_url="https://api.fake.com/v1/chat/completions",
            headers={"Authorization": "Bearer test", "Content-Type": "application/json"}
        )

    @patch("adapters.llm_adapter.requests.post")
    def test_call_beta_returns_text(self, mock_post):
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Sample response"}}]
        }
        mock_post.return_value = mock_response

        result = self.adapter.call_beta("Hello")
        self.assertEqual(result, "Sample response")

    @patch("adapters.llm_adapter.requests.post")
    def test_call_beta_returns_json(self, mock_post):
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"key": "value"}'}}]
        }
        mock_post.return_value = mock_response

        result = self.adapter.call_beta("Hello", return_json=True)
        self.assertEqual(result, {"key": "value"})

    @patch("adapters.llm_adapter.requests.post")
    def test_call_raw_handles_exception(self, mock_post):
        mock_post.side_effect = Exception("Connection error")
        result = self.adapter._call_raw("Test")
        self.assertEqual(result, "")

    def test_parse_json_with_invalid_json(self):
        invalid_output = "{'key': 'unquoted}"
        result = self.adapter._parse_json(invalid_output)
        self.assertIsNone(result)

    def test_extract_json_block_from_codeblock(self):
        wrapped = "```json\n{\"foo\": \"bar\"}\n```"
        result = self.adapter._extract_json_block(wrapped)
        self.assertEqual(result, '{"foo": "bar"}')

    def test_extract_json_block_without_backticks(self):
        plain_json = '{"foo": "bar"}'
        result = self.adapter._extract_json_block(plain_json)
        self.assertEqual(result, '{"foo": "bar"}')


if __name__ == "__main__":
    unittest.main()
