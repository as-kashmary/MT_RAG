# 1) Download the multilingual-e5 embedding model via SentenceTransformer
from sentence_transformers import SentenceTransformer

embed_model = SentenceTransformer("intfloat/multilingual-e5-large-instruct")
embed_model.save("models/multilingual-e5-large-instruct")