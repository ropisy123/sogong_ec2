from openai import OpenAI
import os

class LLMAdapter:
    def __init__(self, model_name="gpt-4o"):
        self.model_name = model_name
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def call(self, prompt: str) -> str:
        print(f"📤 Prompt: {prompt}")
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "당신은 거시경제, 국제정세, 금융시장 전반을 분석하는 전문가입니다. "
                            "경제 지표뿐만 아니라 정치 리스크, 중앙은행 정책, 글로벌 수급, "
                            "시장 참여자의 심리, 지정학적 사건, 그리고 기술 혁신까지 종합적으로 고려하여 "
                            "글로벌 자산 흐름과 투자 전략을 신중하고 전문적으로 분석하세요."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=512
            )
            answer = response.choices[0].message.content.strip()
            print(f"📥 Response: {answer}")
            return answer
        except Exception as e:
            print(f"❌ OpenAI API Error: {e}")
            return "API 호출 중 오류 발생"
