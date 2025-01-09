import json
import os
from config import PROMPT_TEMPLATE_PATH

class PromptManager:
    def __init__(self, filepath=PROMPT_TEMPLATE_PATH):
        self.filepath = filepath
        self.common_prompt_path = os.path.join(os.path.dirname(filepath), "common_prompt.txt")
        self.prompts = self.load_prompts()
        self.common_prompt = self.load_common_prompt()

    def load_common_prompt(self):
        """Loads the common prompt from a separate file."""
        try:
            with open(self.common_prompt_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            print(f"Warning: Common prompt file not found at {self.common_prompt_path}")
            return ""

    def load_prompts(self):
        """Loads role-specific prompts from JSON file."""
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Prompts file not found at {self.filepath}")
            return {}

    def get_prompt(self, role_name):
        """Retrieves a combined prompt (common + role-specific) by role name.

        Args:
            role_name (str): The name of the role.

        Returns:
            str: The combined prompt template, or a default message if not found.
        """
        role_prompt = self.prompts.get(role_name, "")
        
        if not self.common_prompt and not role_prompt:
            return "No prompt found."
            
        return f"{self.common_prompt}\n\n{role_prompt}".strip()