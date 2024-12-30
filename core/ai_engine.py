import google.generativeai as genai
from config import GEMINI_API_KEY, MODEL_NAME

class AIEngine:
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(MODEL_NAME)

    def generate_response(self, prompt, user_input):
        """Generates a response from the AI model.

        Args:
            prompt (str): The formatted prompt.
            user_input (str): The user's input.

        Returns:
            str: The AI model's response.
        """
        try:
            full_prompt = f"{prompt}\nUser: {user_input}\nAI:"
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            print(f"Error generating response: {e}")
            return "An error occurred while generating the response."