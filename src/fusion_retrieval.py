from rank_bm25 import BM25Okapi
from typing import List
from langchain_core.documents.base import Document
import numpy as np

from src.vector_store import query_pinecone


def create_bm25_index(documents: List[Document]) -> BM25Okapi:
    """
    Create a BM25 index from the given documents.

    BM25 (Best Matching 25) is a ranking function used in information retrieval.
    It's based on the probabilistic retrieval framework and is an improvement over TF-IDF.

    Args:
    documents (List[Document]): List of documents to index.

    Returns:
    BM25Okapi: An index that can be used for BM25 scoring.
    """
    # Tokenize each document by splitting on whitespace
    # This is a simple approach and could be improved with more sophisticated tokenization
    print(f"Creating BM25 index for {len(documents)} documents...")
    tokenized_docs = [doc.split() for doc in documents]
    print(f"Tokenized {len(tokenized_docs)} documents for BM25 indexing.")
    return BM25Okapi(tokenized_docs)


def fusion_retrieval(documents, bm25, query: str,namespace, k: int = 5, alpha: float = 0.5) -> List[Document]:
    """
    Perform fusion retrieval combining keyword-based (BM25) and vector-based search.

    Args:
    vectorstore (VectorStore): The vectorstore containing the documents.
    bm25 (BM25Okapi): Pre-computed BM25 index.
    query (str): The query string.
    k (int): The number of documents to retrieve.
    alpha (float): The weight for vector search scores (1-alpha will be the weight for BM25 scores).

    Returns:
    List[Document]: The top k documents based on the combined scores.
    """
    
    epsilon = 1e-8

    # Step 1: Get all documents from the vectorstore
    all_docs = documents

    # Step 2: Perform BM25 search
    bm25_scores = bm25.get_scores(query.split())

    # Step 3: Perform vector search
    vector_results= query_pinecone(query, namespace=namespace, top_k=len(all_docs))
    # print(f"Vector search returned {len(vector_results['matches'])} matches.")
    
    # Step 4: Normalize scores
    vector_scores = np.array([doc[1] for doc in vector_results])
    vector_scores = 1 - (vector_scores - np.min(vector_scores)) / (np.max(vector_scores) - np.min(vector_scores) + epsilon)

    bm25_scores = (bm25_scores - np.min(bm25_scores)) / (np.max(bm25_scores) -  np.min(bm25_scores) + epsilon)

    # Step 5: Combine scores
    combined_scores = alpha * vector_scores + (1 - alpha) * bm25_scores  

    # Step 6: Rank documents
    sorted_indices = np.argsort(combined_scores)[::-1]
    
    # Step 7: Return top k documents        
    return [all_docs[i] for i in sorted_indices[:k]]


def fusion(documents: List[Document], query: str, namespace: str):
    bm25= create_bm25_index(documents)
    results= fusion_retrieval(documents, bm25, query, namespace, k=5, alpha=0.5)
    return results

