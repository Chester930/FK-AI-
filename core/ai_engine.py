import google.generativeai as genai
from config import (
    GEMINI_API_KEY, 
    MODEL_NAME,
    MODEL_TEMPERATURE,
    MODEL_TOP_P,
    MAX_OUTPUT_TOKENS
)

class AIEngine:
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        
        # 設定模型參數
        generation_config = {
            "temperature": MODEL_TEMPERATURE,
            "top_p": MODEL_TOP_P,
            "max_output_tokens": MAX_OUTPUT_TOKENS,
        }
        
        self.model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            generation_config=generation_config
        )

    def generate_response(self, prompt):
        """Generates a response from the AI model.

        Args:
            prompt (str): The complete formatted prompt.

        Returns:
            str: The AI model's response.
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error generating response: {e}")
            return "An error occurred while generating the response."
        