import json
from config import PROMPT_TEMPLATE_PATH

class PromptManager:
    def __init__(self, filepath=PROMPT_TEMPLATE_PATH):
        self.filepath = filepath
        self.prompts = self.load_prompts()

    def load_prompts(self):
        """Loads prompts from a JSON file."""
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Prompts file not found at {self.filepath}")
            return {}

    def get_prompt(self, prompt_name):
        """Retrieves a prompt by its name.

        Args:
            prompt_name (str): The name of the prompt.

        Returns:
            str: The prompt template, or a default message if not found.
        """
        return self.prompts.get(prompt_name, "No prompt found.")