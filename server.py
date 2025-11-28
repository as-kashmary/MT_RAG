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
from src.response_generation import ResponseGenerator
from src.embeder import HFInferenceEmbeddings
from src.vector_store import sending_to_pinecone, retrieve_namespace, query_pinecone, retrieve_length_of_namespace
from src.fusion_retrieval import fusion_retrieval, create_bm25_index
from src.query_classifier import QueryClassifier
from src.semantic_chunker import SemanticChunking
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from src.local_embeder import LocalEmbeddings





#on startup code here
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Currrent idea is to load the embedding model and bm25 index here on startup and keep them in global variables for use in the routes.
    This way we don't have to load them every time a request comes in, which would be very inefficient.

    """

    global embeddings, embedding_model
    start_time = time.time()

    print("Starting up the RAG server...")
    # embeddings= HFInferenceEmbeddings(
    #     model="intfloat/multilingual-e5-large-instruct",
    #     api_key=HF_TOKEN
    # )

    embedding_model= LocalEmbeddings("./models/multilingual-e5-large-instruct")
    # embedding_model = LocalEmbeddings(
    #     os.path.join(PROJECT_ROOT, "models", "multilingual-e5-large-instruct")
    # )
    embedding_model._load_model()
    print(f"Embeddings model loaded. Total elapsed tim¬e: {time.time() - start_time:.2f} seconds")

    yield
    print("Shutting down the RAG server...")

app = FastAPI(lifespan=lifespan)

class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-store"
        return response
app.mount("/static", NoCacheStaticFiles(directory="static"), name="static")

# @app.get("/loader")
# async def loader():
#     doc_list_path = f"{namespace}_document_list.json"
#     global document_list
#     document_list = []
#     try:
#         with open(doc_list_path, 'r') as f:
#             document_list = json.load(f)
#         print(f"Loaded document list from {doc_list_path}")
#     except FileNotFoundError:
#         print(f"Warning: Document list file '{doc_list_path}' not found. Retrieval might fail.")


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

    parsing_time = time.time() - start_time
    print(f"Parsing Time: {parsing_time:.2f} seconds. ")


@app.post("/chunk")
async def chunk():
    start_time=time.time()
    global document_list, bm25, length_of_total_chunks
    document_list = []
    """
    Here, we chunk the parsed document contents into smaller semantic chunks.
    This will be called after parsing.
    We will also index the chunks using BM25 for fusion retrieval. We are doing this so that we don't have to store all the chunks in local storage or cloud storage.
    So we are deleteting "{namespace}_document_list.json" from current code.
    For calling main fusion_retrieval function we are storing the length of total chunks in a global variable. So we also no need to pass the document list around.
    But the idea of only passing length_of_total_chunks is failed because the current implementation of bm25 forbides it.
    """

    """
    We have to implement multiprocessing here to speed up the chunking of multiple documents.
    """

    for content in contents_list:
        chunks= SemanticChunking(content, embedding_model)
        print(f"Number of chunks: {len(chunks.get_chunks())}")
        document_list+=chunks.get_chunks()
    
    bm25=create_bm25_index(document_list)
    print(f"BM25 index created with {len(document_list)} documents inside chunking route.")
    length_of_total_chunks=len(document_list)

    """
    We will not save the chunks in a json file anymore. It's inefficient and unnecessary.
    We found out that after sending to pinecone, only place where chunks are required as texts is fusion retrieval.
    So we are stil figuring out ways to avoid storing and passsing them in memory.
    If it required mongodb implementation then it can be done later.
    """

    semnantic_chunking_time = time.time() - start_time
    print(f"Parsing and Chunking Time: {semnantic_chunking_time:.2f} seconds. ")

@app.get("/vectorizing")
async def vectorizing(namespace: str="x200_namespace"):
    """
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

    start_time=time.time()
    ids = [str(i) for i in range(len(vectors))]
    metadata_list = [{"text": chunk} for chunk in document_list]
    sending_to_pinecone(vectors=vectors, ids=ids, metadata_list=metadata_list, namespace=namespace)
    vector_storing_time = time.time() - start_time
    print(f"Vector Storing Time: {vector_storing_time:.2f} seconds")

# @app.get("/retrieve")
# async def retrieve(query: str):

#     return results

@app.get("/classify")
async def query_classifier(query: str="How can I evaluate global climate?"):
    start_time=time.time()

    query_classifier= QueryClassifier(query)
    query_class=query_classifier.classification()
    print(f"Query Classification Time: {time.time() - start_time:.2f} seconds")
    return query_class


@app.post("/generate-response")
async def generate_response(query: str="How can I evaluate global climate?", namespace: str ="x200_namespace"):
    # print( f"Received query: {query} for namespace: {namespace}")
    start_time=time.time()
    """
    Retrieves relevant document chunks for a given query using fusion retrieval.
    """

    vector_count=retrieve_length_of_namespace(namespace)
    print(f"Length of total chunks in namespace '{namespace}': {vector_count}")


    """
    The current implementation do not use the locally stored json file of chunks. 
    Because, we are figuring out how can we skip the part of storing and using of chunks as texts
    """


    """
    From here on, the code is broke because we aren't passing the chunks in fusion_retrieval as texts
    """

    result_index=fusion_retrieval(length_of_total_chunks,embedding_model, bm25, query, namespace, k=5, alpha=0.5)
    print(result_index)
    print("------------------------------------------------------------------------------")
    # results =  fusion(document_list=document_list,embedding_model=embedding_model, query=query, namespace=namespace)
    context=results[0]
    print(f"Retrieved context for response generation: {context}")

    generator = ResponseGenerator(query, context)
    response = generator.generation()
    response_generation_time = time.time() - start_time
    print(f"Response Generation Time: {response_generation_time:.2f} seconds")

    return {"response": response}


@app.get("/admin", status_code=status.HTTP_200_OK)
async def get_admin_page():
    admin_path = Path("static/admin.html")
    return HTMLResponse(content=admin_path.read_text(), status_code=200) 


@app.get("/user", status_code=status.HTTP_200_OK)
async def get_admin_page():
    user_path = Path("static/user.html")
    return HTMLResponse(content=user_path.read_text(), status_code=200)



def parse_args():
    parser = argparse.ArgumentParser(
        description="This is a whole RAG pipleine")
    parser.add_argument("--path", type=str, default="documents/texts.txt",
                        help="Path to the PDF file to encode.")
    parser.add_argument("--namespace", type=str, default="default",
                        help="Namespace in Pinecone to store/already stored the vectors.")
    return parser.parse_args()


#hosting on localhost
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)