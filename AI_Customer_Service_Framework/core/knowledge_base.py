from config import KNOWLEDGE_BASE_PATH
import re

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
        """Searches the knowledge base for a query using regular expressions.

        Args:
            query (str): The search query.

        Returns:
            str: A relevant portion of the knowledge base, or a message
                 indicating that no relevant information was found.
        """
        if not self.data:
            return "Knowledge base is empty."

        # 使用正規表達式進行全文搜尋，並設定為忽略大小寫
        matches = re.findall(r".*?" + re.escape(query) + r".*?", self.data, re.IGNORECASE)
        if matches:
            # 只返回前 3 個匹配項，避免回應過長
            return "\n".join(matches[:3])
        else:
            return "No relevant information found in the knowledge base."