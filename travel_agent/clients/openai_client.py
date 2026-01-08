from openai import OpenAI


class OpenaiClientWrapper:
    def __init__(self,api_key:str,base_url:str,model_id:str):
        self.client = OpenAI(api_key=api_key,base_url=base_url)
        self.model =model_id
        
    def generate(self, prompt: str, system_prompt: str) -> str:

        print("calling LLM...")
        try:
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False
            )
            answer = response.choices[0].message.content
            print("LLM Responsed")
            return answer
        except Exception as e:
            print(f"Error when calling LLM API: {e}")
            return "Error when calling LLM API"
        