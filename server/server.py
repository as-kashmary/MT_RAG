import time
import json
import uvicorn
import sys
import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse



PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.document_loader import read_pdf_to_string
from src.response_generation import ResponseGenerator
from src.embeder import HFInferenceEmbeddings
from src.vector_store import sending_to_pinecone, retrieve_namespace, query_pinecone
from src.fusion_retrieval import fusion_retrieval, create_bm25_index, fusion
from src.query_classifier import QueryClassifier
from src.semantic_chunker import SemanticChunking


from contextlib import asynccontextmanager





HF_TOKEN="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"

namespace="default"





#on startup code here
@asynccontextmanager
async def lifespan(app: FastAPI):
    global embeddings
    start_time = time.time()

    print("Starting up the RAG server...")
    embeddings= HFInferenceEmbeddings(
        model="intfloat/multilingual-e5-large-instruct",
        api_key=HF_TOKEN
    )
    print(f"Embeddings model loaded. Total elapsed time: {time.time() - start_time:.2f} seconds")
    yield
    print("Shutting down the RAG server...")



app = FastAPI(lifespan=lifespan)

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

@app.post("/chunk")
async def chunk(path: str="documents/texts.txt"):
    start_time=time.time()
    global document_list
    content= read_pdf_to_string(path)
    document_reading_time = time.time() - start_time
    print(f"Document Reading Time: {document_reading_time:.2f} seconds. ")

    chunks=SemanticChunking(content, embeddings)
    print(f"Number of chunks: {len(chunks.get_chunks())}")
    document_list=chunks.get_chunks()
    semnantic_chunking_time = time.time() - start_time
    print(f"Semantic Chunking Time: {semnantic_chunking_time:.2f} seconds. ")

@app.get("/vectorizing")
async def vectorizing():
    start_time=time.time()
    global vectors
    vectors = embeddings.embed_documents(document_list)
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
    query_classifier=QueryClassifier(query)
    query_class=query_classifier.classification()
    print(f"Query Classification Time: {time.time() - start_time:.2f} seconds")
    return query_class




@app.post("/generate-response")
async def generate_response(query: str="How can I evaluate global climate?"):
    start_time=time.time()
    """
    Retrieves relevant document chunks for a given query using fusion retrieval.
    """
    results = fusion(document_list, query, namespace)
    context=results[0]
    # data = await request.json()
    # query = data.get("query")
    # context = data.get("context")

    generator = ResponseGenerator(query, context)
    response = generator.generation()
    response_generation_time = time.time() - start_time
    print(f"Response Generation Time: {response_generation_time:.2f} seconds")

    return JSONResponse(content={"response": response})


#hosting on localhost
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)