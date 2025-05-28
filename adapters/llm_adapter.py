class LLMAdapter:
    def __init__(self, model_name="gpt-4"):
        self.model_name = model_name

    def call(self, prompt: str) -> str:
        # OpenAI API 또는 HuggingFace Inference 등 연동
        print(f"📤 Prompt: {prompt}")
        return "모의 응답: 상승 60%, 보합 20%, 하락 20%"
