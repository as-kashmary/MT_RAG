from sentence_transformers import SentenceTransformer
import os
from huggingface_hub import InferenceClient


class HFInferenceEmbeddings:
    def __init__(self, model: str, api_key: str):
        self.client = InferenceClient(
            provider="hf-inference",
            api_key=api_key
        )
        self.model = model

    def embed_documents(self, texts):
        # HF Inference API can accept a single string or a list
        results = []
        for t in texts:
            embeddings = self.client.feature_extraction(
                t,
                model=self.model
            )
            results.append(embeddings.tolist())
        return results

    # optional but useful
    def embed_query(self, text):
        query_vector = self.client.feature_extraction(
            text,
            model=self.model
        )

        return query_vector.tolist()
