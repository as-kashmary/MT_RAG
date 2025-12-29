from typing import List

import numpy as np
from langchain_core.documents.base import Document

from src.logging.logging import get_logger
from src.rag.rank_bm25 import BM25Okapi, BM25Okapi_without_corpus
from src.rag.vector_store import query_pinecone


logger = get_logger("fusion_retrieval")



def new_create_BM25Okapi_index(documents: List[Document], bm25_index: BM25Okapi) -> BM25Okapi:
    tokenized_docs = [doc.split() for doc in documents]
    bm25_index.add_documents(tokenized_docs)
    return bm25_index

def new_create_BM25Okapi_without_corpus_index(documents: List[Document], bm25_index: BM25Okapi) -> BM25Okapi:
    tokenized_docs = [doc.split() for doc in documents]
    bm25_index.add_documents(tokenized_docs)
    return bm25_index


def create_bm25_index_v2(variable_list):
    """
    'corpus_size': self.corpus_size,
    'avgdl': self.avgdl,
    'doc_freqs': self.doc_freqs,
    'idf': self.idf,
    'doc_len': self.doc_len,
    'average_idf': self.average_idf,
    'k1': self.k1,
    'b': self.b,
    'epsilon': self.epsilon
    """
    corpus_size = variable_list['corpus_size']
    avgdl = variable_list['avgdl']
    doc_freqs = variable_list['doc_freqs']
    idf = variable_list['idf']
    doc_len = variable_list['doc_len']
    average_idf = variable_list['average_idf']
    k1 = variable_list['k1']
    b = variable_list['b']
    epsilon = variable_list['epsilon']


    #    def __init__(self, corpus_size, avgdl, doc_freqs, idf, doc_len, average_idf,tokenizer=None, k1=1.5, b=0.75, epsilon=0.25):

    bm25=BM25Okapi_without_corpus(corpus_size=corpus_size, avgdl=avgdl, doc_freqs=doc_freqs, idf=idf, doc_len=doc_len, average_idf=average_idf, k1=k1, b=b, epsilon=epsilon)
    return bm25



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
    # print(f"Creating BM25 index for {len(documents)} documents...")
    tokenized_docs = [doc.split() for doc in documents]
    # print(f"Tokenized {len(tokenized_docs)} documents for BM25 indexing.")
    return BM25Okapi(tokenized_docs)


async def fusion_retrieval(stats, Pinecone_index, length_of_total_chunks, embedding_model, bm25, query: str,namespace, k: int = 5, alpha: float = 0.5) -> List[int]:
    """
    What's the issue in here? 
    The current code requires to retrieves all the chunks to compute BM25 scores. So if the knowledge base is updated frequently with new documents/chunks, 
    the BM25 index needs to be rebuilt each time to include the new data.
    The current implementation assumes that the documents used to create the BM25 index are the same as those in the vector store.
    This implementation is ineffiecient for large datasets as it requires loading all documents into memory to compute BM25 scores.
    So we need to change the implementation to compute bm25 scores.
    In summary, the goal: precompute the bm25 scores in server startup. 
    Then, As soon as a new document's chunks are created the bm25 index should be updated with the new chunks. For that we need to store the internal state of bm25 model.
    We then need to update the variables of rank_bm25.BM25Okapi class with the new chunks. 
    """
    
    
    
    
    
    
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
    # all_docs = documents

    # Step 2: Perform BM25 search
    # print(f"Performing BM25 search for query: {query}...")
    bm25_scores = bm25.get_scores(query.split())

    logger.info("BM25 scores computed", extra={"document_count": len(bm25_scores), "namespace": namespace})

    # Step 3: Perform vector search
    #query_pinecone(query,namespace,embedding_model, top_k=3)
    vector_results= await query_pinecone(stats, index=Pinecone_index, query=query, namespace=namespace, embedding_model=embedding_model, top_k=length_of_total_chunks)
    logger.info(
        "Vector search completed",
        extra={
            "query": query,
            "namespace": namespace,
            "result_count": len(vector_results),
        },
    )
    # print(f"Vector search returned {len(vector_results['matches'])} matches.")
    
    # Step 4: Normalize scores
    vector_scores = np.array([doc[1] for doc in vector_results])
    # print(f"Shapes of vector score {vector_scores.shape} and bm25 scores {bm25_scores.shape}")
    vector_scores = 1 - (vector_scores - np.min(vector_scores)) / (np.max(vector_scores) - np.min(vector_scores) + epsilon)

    # print(f"Vector scores normalized for {len(vector_scores)} documents.")

    bm25_scores = (bm25_scores - np.min(bm25_scores)) / (np.max(bm25_scores) -  np.min(bm25_scores) + epsilon)
    # print(f"BM25 scores normalized for {len(bm25_scores)} documents.")

    # Step 5: Combine scores
    combined_scores = alpha * vector_scores + (1 - alpha) * bm25_scores  

    # Step 6: Rank documents
    sorted_indices = np.argsort(combined_scores)[::-1]
    
    # Step 7: Return top k documents 
    # sorted_indices    
    # The sorted indices starts from 0 to len(all_docs)-1   
    return [int(i) for i in sorted_indices[:k]]
    # return [all_docs[i] for i in sorted_indices[:k]]
