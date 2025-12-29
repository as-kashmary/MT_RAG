# from langchain_huggingface import HuggingFaceEmbeddings

# class LocalEmbeddings:
#     def __init__(self, model_name):
#         self.model_name = model_name
#         self.model = HuggingFaceEmbeddings(model_name=model_name)

#     def embed_documents(self, texts):
#         return self.model.embed_documents(texts)

#     def embed_query(self, text):
#         return self.model.embed_query(text)
    

from langchain_huggingface import HuggingFaceEmbeddings
from src.logging.logging import get_logger

logger = get_logger("local_embeder")


class LocalEmbeddings:
    def __init__(self, model_name):
        self.model_name = model_name
        self.model = None  # <-- lazy

    def _load_model(self):
        if self.model is None:
            logger.info(f"[LocalEmbeddings] Loading model: {self.model_name}")
            self.model = HuggingFaceEmbeddings(model_name=self.model_name)

    def embed_documents(self, texts):
        self._load_model()
        return self.model.embed_documents(texts)
    
    def embed_text(self, text):
        self._load_model()
        return self.model.embed_text(text)

    def embed_query(self, text):
        self._load_model()
        return self.model.embed_query(text)
