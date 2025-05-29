import requests
import json
import time

from core.config import settings

class LLMAdapter:
    def __init__(
        self,
        model_name: str = settings.llm_model_name,
        base_url: str = settings.llm_base_url,
        headers: dict = None
    ):
        self.model_name = model_name
        self.base_url = base_url
        self.headers = headers or {
            "Authorization": f"Bearer {settings.llm_api_key}",
            "Content-Type": "application/json"
        }

    def call_beta(self, prompt: str, return_json: bool = False):
        content = self._call_raw(prompt)
        if not return_json:
            return content
        return self._parse_json(content)

    def _call_raw(self, prompt: str) -> str:
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,         # ✅ 예측 안정성 최우선 → 무조건 고정
            "top_p": 1.0,               # ✅ 확률 기반 완전 출력 (0.0 temp와 함께 쓰면 안정적)
            "frequency_penalty": 0.0,   # ✅ 예측에는 반복 억제 불필요 (불확실성 도입 가능)
            "presence_penalty": 0.0,    # ✅ 예측에선 주제 탈선 방지
            "max_tokens": 1500          # ⛳ 유지 가능 (요약 포함 시 1200 이상 추천)
        }

        try:
            res = requests.post(self.base_url, headers=self.headers, json=payload)
            res.raise_for_status()
            time.sleep(1.2)  # 1~1.5초 정도가 무난
            return res.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print("[ERROR] LLM API 호출 실패:", e)
            return ""

    def _parse_json(self, output: str) -> dict | None:
        cleaned = self._extract_json_block(output)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            try:
                fallback = cleaned.replace("'", '"')
                return json.loads(fallback)
            except json.JSONDecodeError as e:
                print("[ERROR] JSON 파싱 실패:", e)
                print("[원본 응답]:", cleaned[:500])
                return None

    def _extract_json_block(self, output: str) -> str:
        if "```" in output:
            output = output.split("```")[-2].strip()
        if output.lower().startswith("json"):
            output = output[4:].strip()
        return output.strip()
