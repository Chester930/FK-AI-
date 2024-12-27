from config import KNOWLEDGE_BASE_PATH

class KnowledgeBase:
    def __init__(self, filepath=KNOWLEDGE_BASE_PATH):
        self.filepath = filepath
        self.data = self.load_data()

    def load_data(self):
        """Loads data from the knowledge base file."""
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            print(f"Error: Knowledge base file not found at {self.filepath}")
            return ""

    def search(self, query):
        """Searches the knowledge base for a query.

        Args:
            query (str): The search query.

        Returns:
            str: The relevant portion of the knowledge base, or a message
                 indicating that no relevant information was found.
        """
        # Placeholder for a more sophisticated search implementation
        if query.lower() in self.data.lower():
            return self.data # Placeholder: returns the entire data
        else:
            return "No relevant information found in the knowledge base."