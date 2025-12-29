import time
import json
import uvicorn
import sys
import os
from fastapi import FastAPI, Request, status, Depends, HTTPException
from pathlib import Path
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
import argparse

from pinecone import Pinecone

# PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# sys.path.insert(0, PROJECT_ROOT)

from src.rag.document_loader import read_txt_to_string, read_pdf_to_string, read_docx_to_string
from src.rag.vector_store import sending_to_pinecone, retrieve_namespace, query_pinecone, retrieve_length_of_namespace
from src.rag.fusion_retrieval import fusion_retrieval, create_bm25_index, new_create_BM25Okapi_index, new_create_BM25Okapi_without_corpus_index, create_bm25_index_v2
from src.rag.semantic_chunker import SemanticChunking
from contextlib import asynccontextmanager

from src.rag.local_embeder import LocalEmbeddings
from src.DB_Routes.mongodb_implementation import (
    store_bm25_index_and_chunks_in_mongodb, 
    retrieve_bm25_index_and_chunks_using_namespace, 
    update_bm25_index_and_chunks_in_mongodb, 
    retrieve_chunks_from_mongodb)

from src.logging.logging import configure_logging, get_logger
from src.logging.request_id import RequestIDMiddleware

configure_logging(level="INFO", service_name="admin-server")

class AdminSession:
    def __init__(self):
        self.document_list = []
        self.namespace = None
        self.bm25 = None
        self.length_of_total_chunks = None
        self.vectors = None
        self.contents_list = []       
        self.variable_list = None
        self.created_or_not = False
        self.namespace = None
        self.retrieved_chunk_length = 0
        


sessions = {}

def get_admin_session(admin_id: str):
    if admin_id not in sessions:
        sessions[admin_id] = AdminSession()
    return sessions[admin_id]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Currrent idea is to load the embedding model and bm25 index here on startup and keep them in global variables for use in the routes.
    This way we don't have to load them every time a request comes in, which would be very inefficient.

    """

    global embedding_model, Pinecone_index, stats
    start_time = time.time()

    logger.info("Starting up the RAG server...")

    embedding_model= LocalEmbeddings("./models/multilingual-e5-large-instruct")
    embedding_model._load_model()
    logger.info(f"Embeddings model loaded. Total elapsed time: {time.time() - start_time:.2f} seconds")
    try:
        pc = Pinecone(api_key="pcsk_2ht9Mg_9VwrnZM7wQrAiCkEfUTQFLDsPui6p9VxkcKbCPvKsVSUaR9jZwmeQwwuUpbpGJv")

        Pinecone_index = pc.Index(host="https://test-11ejuti.svc.aped-4627-b74a.pinecone.io")
        stats=Pinecone_index.describe_index_stats()
        logger.info(f"Pinecone connected. Stats: {stats}")
    except Exception as e:
        logger.error(f"Pinecone connection failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Pinecone connection failed:{str(e)}")

    yield
    logger.info("Shutting down the RAG server...")

app = FastAPI(lifespan=lifespan)


"""
Added RequestIDMiddleware to log request ids in logs for tracing.

"""

app.add_middleware(RequestIDMiddleware)
logger = get_logger("admin_server")


@app.post("/parser")
async def parser(path: str="documents",
                 admin_session: AdminSession = Depends(get_admin_session)):
    """
    Here, we parse different document types and return their contents as strings.
    This will be called before chunking.
    """
    """
    We have to implement multiprocessing here to speed up the parsing of multiple documents.
    """
    try:

        start_time=time.time()
        admin_session.contents_list = []

        def file_type_checker(file_name):
            if file_name.endswith(".pdf"):
                return "pdf"
            elif file_name.endswith(".txt"):
                return "txt"
            elif file_name.endswith(".docx"):
                return "docx"
            else:
                return "unknown"

        #iterate through all pdf files in the given path
        for file_name in os.listdir(path):
            file_path = os.path.join(path, file_name)
            if file_type_checker(file_name) == "txt":
                content= read_txt_to_string(file_path)
            elif file_type_checker(file_name) == "docx":
                content= read_docx_to_string(file_path)
            elif file_type_checker(file_name) == "pdf":
                content= read_pdf_to_string(file_path)
            admin_session.contents_list.append(content)


        parsing_time = time.time() - start_time
        logger.info(f"Parsed {len(admin_session.contents_list)} documents from {path} in {parsing_time:.2f} seconds.")

    except Exception as e:
        logger.error(f"Parsing failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Parsing failed:{str(e)}")


@app.post("/chunk")
async def chunk(namespace: str="dotlines",
                 admin_session: AdminSession = Depends(get_admin_session)):
    start_time=time.time()
    # global document_list, bm25, length_of_total_chunks, created_or_not, variable_list, namespace1
    admin_session.namespace= namespace
    """
    28/11/2025
    Here, we chunk the parsed document contents into smaller semantic chunks.
    This will be called after parsing.
    We will also index the chunks using BM25 for fusion retrieval. We are doing this so that we don't have to store all the chunks in local storage or cloud storage.
    So we are deleteting "{namespace}_document_list.json" from current code.
    For calling main fusion_retrieval function we are storing the length of total chunks in a global variable. So we also no need to pass the document list around.
    But the idea of only passing length_of_total_chunks is failed because the current implementation of bm25 forbides it.
    We have to implement multiprocessing here to speed up the chunking of multiple documents.
    """
    """
    30/11/2025
    Modified the rank_bm25 by creating a new class BM25Okapi_without_corpus which can update the internal state of bm25 index with new documents without requiring the original corpus.
    Also created a method in the parent class BM25: add_documents to update the internal state with new documents 
    And created another method return_variables to return the internal state variables as a dictionary for storing in mongodb.
    So here, if the bm25 index for the given namespace exists in mongodb, we retrieve it and update it with the new chunks.
    Otherwise, we create a new bm25 index and store it in mongodb.

    """
    try:
        for content in admin_session.contents_list:
            chunks= SemanticChunking(content, embedding_model)
            logger.info(f"Number of chunks created from a document: {len(chunks.get_chunks())}")
            admin_session.document_list+=chunks.get_chunks()

        admin_session.length_of_total_chunks=len(admin_session.document_list)
        data = retrieve_bm25_index_and_chunks_using_namespace(admin_session.namespace)
        admin_session.created_or_not= False
        if data is None:
            admin_session.bm25=create_bm25_index(admin_session.document_list)
            admin_session.variable_list= admin_session.bm25.return_variables()
            admin_session.created_or_not= True
            logger.info(f"BM25 index created with {len(admin_session.document_list)} documents inside chunking route.")
        else:
            logger.info(f"BM25 index retrieved from MongoDB with {len(admin_session.document_list)} documents inside chunking route.")
            admin_session.bm25= create_bm25_index_v2(data['bm25_index_variables'])
            admin_session.retrieved_chunk_length= data['chunk_length']
            admin_session.bm25= new_create_BM25Okapi_without_corpus_index(admin_session.document_list, admin_session.bm25)
            admin_session.variable_list= admin_session.bm25.return_variables()
    except Exception as e:
        logger.error(f"Chunking failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Chunking failed:{str(e)}")

    """
    28/11/2025

    We will not save the chunks in a json file anymore. It's inefficient and unnecessary.
    We found out that after sending to pinecone, only place where chunks are required as texts is fusion retrieval.
    So we are stil figuring out ways to avoid storing and passsing them in memory.
    If it required mongodb implementation then it can be done later.
    """
    chunking_time = time.time() - start_time
    logger.info(f"Chunking completed in {chunking_time:.2f} seconds. Total chunks: {len(admin_session.document_list)}")

@app.get("/vectorizing")
async def vectorizing(namespace: str="dotlines",
                    admin_session: AdminSession = Depends(get_admin_session)):
    """
    28/11/2025
    Chunks are stored in document_list global variable after chunking.
    Here, we vectorize the chunks and store them in Pinecone vectorstore.
    This will be called after chunking.
    """ 

    start_time=time.time()
    # global vectors

    try:
        admin_session.vectors =  embedding_model.embed_documents(admin_session.document_list)
        logger.info(f"Number of vectors: {len(admin_session.vectors)}")
        embedding_time = time.time() - start_time
        logger.info(f"Embedding Time: {embedding_time:.2f} seconds")
    except Exception as e:
        logger.error(f"Embedding failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Embedding failed:{str(e)}")

    vectorizing_time = time.time() - start_time
    logger.info(f"Vectorizing completed in {vectorizing_time:.2f} seconds.")


@app.post("/store")
async def store(admin_session: AdminSession = Depends(get_admin_session)):
    start_time=time.time()
    try:
        if admin_session.created_or_not: 
            store_bm25_index_and_chunks_in_mongodb(admin_session.variable_list, admin_session.document_list, admin_session.namespace)
            logger.info(f"BM25 index and chunks stored in MongoDB inside chunking route.")
        else:
            update_bm25_index_and_chunks_in_mongodb(admin_session.variable_list, admin_session.document_list, admin_session.namespace)
            logger.info(f"BM25 index updated with {len(admin_session.document_list)} new documents inside chunking route.")
        start_time=time.time()
        ids = [str(i+admin_session.retrieved_chunk_length) for i in range(len(admin_session.vectors))]
        metadata_list = [{"text": chunk} for chunk in admin_session.document_list]
        await sending_to_pinecone(stats=stats, index=Pinecone_index, vectors=admin_session.vectors, ids=ids, metadata_list=metadata_list, namespace=admin_session.namespace)
    except Exception as e:
        logger.error(f"Storing failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Storing failed:{str(e)}")
        
    
    vector_storing_time = time.time() - start_time
    logger.info(f"Vector Storing Time: {vector_storing_time:.2f} seconds")

    


#hosting on localhost
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)