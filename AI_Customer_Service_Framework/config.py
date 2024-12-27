# Configuration for the AI customer service
import os

# Retrieve API key from environment variable
GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY")

# Model settings
MODEL_NAME = "gemini-pro" # or another suitable model

# Knowledge base settings
KNOWLEDGE_BASE_PATH = "data"

# Prompt settings
PROMPT_TEMPLATE_PATH = "data/prompts.json"