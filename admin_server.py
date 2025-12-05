import time
import json
import uvicorn
import sys
import os
from fastapi import FastAPI, Request, status
from pathlib import Path
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
import argparse

# PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# sys.path.insert(0, PROJECT_ROOT)

from src.document_loader import read_txt_to_string, read_pdf_to_string, read_docx_to_string
from src.vector_store import sending_to_pinecone, retrieve_namespace, query_pinecone, retrieve_length_of_namespace
from src.fusion_retrieval import fusion_retrieval, create_bm25_index, new_create_BM25Okapi_index, new_create_BM25Okapi_without_corpus_index, create_bm25_index_v2
from src.semantic_chunker import SemanticChunking
from contextlib import asynccontextmanager

from src.local_embeder import LocalEmbeddings
from DB_Routes.monogodb_implementation import store_bm25_index_and_chunks_in_mongodb, retrieve_bm25_index_and_chunks_using_namespace, update_bm25_index_and_chunks_in_mongodb, retrieve_chunks_from_mongodb

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Currrent idea is to load the embedding model and bm25 index here on startup and keep them in global variables for use in the routes.
    This way we don't have to load them every time a request comes in, which would be very inefficient.

    """

    global embeddings, embedding_model
    start_time = time.time()

    print("Starting up the RAG server...")

    embedding_model= LocalEmbeddings("./models/multilingual-e5-large-instruct")
    embedding_model._load_model()
    print(f"Embeddings model loaded. Total elapsed time: {time.time() - start_time:.2f} seconds")

    yield
    print("Shutting down the RAG server...")

app = FastAPI(lifespan=lifespan)


@app.post("/parser")
async def parser(path: str="documents"):
    """
    Here, we parse different document types and return their contents as strings.
    This will be called before chunking.
    """
    """
    We have to implement multiprocessing here to speed up the parsing of multiple documents.
    """


    start_time=time.time()
    global contents_list
    contents_list = []

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
        print(f"Processing file: {file_path}")
        if file_type_checker(file_name) == "txt":
            content= read_txt_to_string(file_path)
        elif file_type_checker(file_name) == "docx":
            content= read_docx_to_string(file_path)
        elif file_type_checker(file_name) == "pdf":
            content= read_pdf_to_string(file_path)
        contents_list.append(content)

    print(contents_list)

    parsing_time = time.time() - start_time
    print(f"Parsing Time: {parsing_time:.2f} seconds. ")

@app.post("/chunk")
async def chunk(namespace: str="dotlines"):
    start_time=time.time()
    global document_list, bm25, length_of_total_chunks, created_or_not, variable_list, namespace1
    namespace1= namespace
    document_list = []
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

    for content in contents_list:
        chunks= SemanticChunking(content, embedding_model)
        print(f"Number of chunks: {len(chunks.get_chunks())}")
        document_list+=chunks.get_chunks()

    length_of_total_chunks=len(document_list)
    data = retrieve_bm25_index_and_chunks_using_namespace(namespace)
    created_or_not= False
    if data is None:
        bm25=create_bm25_index(document_list)
        variable_list= bm25.return_variables()
        created_or_not= True
        print(f"BM25 index created with {len(document_list)} documents inside chunking route.")
    else:
        print(f"BM25 index retrieved from MongoDB with {len(document_list)} documents inside chunking route.")
        bm25= create_bm25_index_v2(data['bm25_index_variables'])
        bm25= new_create_BM25Okapi_without_corpus_index(document_list, bm25)
        variable_list= bm25.return_variables()
        

    """
    28/11/2025

    We will not save the chunks in a json file anymore. It's inefficient and unnecessary.
    We found out that after sending to pinecone, only place where chunks are required as texts is fusion retrieval.
    So we are stil figuring out ways to avoid storing and passsing them in memory.
    If it required mongodb implementation then it can be done later.
    """

    semnantic_chunking_time = time.time() - start_time
    print(f"Parsing and Chunking Time: {semnantic_chunking_time:.2f} seconds. ")

@app.get("/vectorizing")
async def vectorizing(namespace: str="dotlines"):
    """
    28/11/2025
    Chunks are stored in document_list global variable after chunking.
    Here, we vectorize the chunks and store them in Pinecone vectorstore.
    This will be called after chunking.
    """ 

    start_time=time.time()
    global vectors


    vectors =  embedding_model.embed_documents(document_list)
    print(f"Number of vectors: {len(vectors)}")
    embedding_time = time.time() - start_time
    print(f"Embedding Time: {embedding_time:.2f} seconds")



# @app.get("/retrieve")
# async def retrieve(query: str):

#     return results


@app.post("/store")
async def store():
    start_time=time.time()
    if created_or_not: 
        store_bm25_index_and_chunks_in_mongodb(variable_list, document_list, namespace1)
        print(f"BM25 index and chunks stored in MongoDB inside chunking route.")
    else:
        update_bm25_index_and_chunks_in_mongodb(variable_list, document_list, namespace1)
        print(f"BM25 index updated with {len(document_list)} new documents inside chunking route.")
    start_time=time.time()
    ids = [str(i) for i in range(len(vectors))]
    metadata_list = [{"text": chunk} for chunk in document_list]
    sending_to_pinecone(vectors=vectors, ids=ids, metadata_list=metadata_list, namespace=namespace1)
    vector_storing_time = time.time() - start_time
    print(f"Vector Storing Time: {vector_storing_time:.2f} seconds")

    


#hosting on localhost
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)