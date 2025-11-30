from fastapi import FastAPI, Request, status
from pathlib import Path
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
import uvicorn
import time
from contextlib import asynccontextmanager

from src.fusion_retrieval import fusion_retrieval, create_bm25_index_v2
from src.response_generation import ResponseGenerator
from src.local_embeder import LocalEmbeddings

from DB_Routes.monogodb_implementation import retrieve_all




@asynccontextmanager
async def lifespan(app: FastAPI):
    global bm25_dict, embedding_model
    start_time = time.time()
    print("Starting up the server...")
    retrieved_data= retrieve_all()
    bm25_dict={}
    for data in retrieved_data:
        bm25=create_bm25_index_v2(data['bm25_index_variables'])
        bm25_dict[data['namespace']]={
            "bm25_object": bm25,
            "chunk_length": data["chunk_length"],
            "chunks": data["chunks"]}

    # print(bm25_dict)
    embedding_model= LocalEmbeddings("./models/multilingual-e5-large-instruct")
    embedding_model._load_model()
    print(f"Embeddings model loaded, bm25 objects loaded. Total elapsed time: {time.time() - start_time:.2f} seconds")
    yield
    print("Shutting down the server...")


app = FastAPI(lifespan=lifespan)

@app.get("/context_generation")
async def context_generation(query:str ="Why my echo making noise?",namespace:str ="dotlines"):
    global context
    length_of_total_chunks=bm25_dict[namespace]["chunk_length"]

    result_indexes= fusion_retrieval(
        length_of_total_chunks=length_of_total_chunks, 
        embedding_model=embedding_model, 
        bm25=bm25_dict[namespace]["bm25_object"], 
        query=query, 
        namespace=namespace)
    results= [bm25_dict[namespace]["chunks"][i][1] for i in result_indexes]
    context=" ".join(results)
    return context

@app.get("/response_generation")
async def response_generation(query:str ="Why my echo making noise?",namespace:str ="dotlines"):
    context= await context_generation(query,namespace)
    generator = ResponseGenerator(query, context)
    response = generator.generation()
    return response
    



#hosting on localhost
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)

