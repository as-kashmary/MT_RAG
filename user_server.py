from fastapi import FastAPI, Request, status, HTTPException, Depends
from pathlib import Path
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
import uvicorn
import time
from contextlib import asynccontextmanager

from src.fusion_retrieval import fusion_retrieval, create_bm25_index_v2
from src.response_generation import ResponseGenerator
from src.local_embeder import LocalEmbeddings

from DB_Routes.monogodb_implementation import retrieve_all
from pinecone import Pinecone


class UserSession:
    def __init__(self):
        self.namespace = None
        self.bm25_dict = {}
        self.length_of_total_chunks = None
        self.context = None
        

sessions = {}

def get_user_session(user_id: str):
    if user_id not in sessions:
        sessions[user_id] = UserSession()
    return sessions[user_id]




@asynccontextmanager
async def lifespan(app: FastAPI):
    global embedding_model, Pinecone_index, stats
    start_time = time.time()
    print("Starting up the server...")
    
    embedding_model= LocalEmbeddings("./models/multilingual-e5-large-instruct")
    embedding_model._load_model()
    print(f"Embeddings model loaded, bm25 objects loaded. Total elapsed time: {time.time() - start_time:.2f} seconds")
    try:
        pc = Pinecone(api_key="pcsk_2ht9Mg_9VwrnZM7wQrAiCkEfUTQFLDsPui6p9VxkcKbCPvKsVSUaR9jZwmeQwwuUpbpGJv")

        Pinecone_index = pc.Index(host="https://test-11ejuti.svc.aped-4627-b74a.pinecone.io")
        stats=Pinecone_index.describe_index_stats()
        print(stats)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Pinecone connection failed:{str(e)}")

    
    yield
    print("Shutting down the server...")


app = FastAPI(lifespan=lifespan)
@app.get("/retrieve_bm25_index_and_chunks")
async def retrieve_bm25_index_and_chunks(namespace:str ="dotlines",
                                         user_session: UserSession = Depends(get_user_session)):
    try:
        retrieved_data= retrieve_all()
        print(retrieved_data)
        for data in retrieved_data:
            bm25=create_bm25_index_v2(data['bm25_index_variables'])
            user_session.bm25_dict[data['namespace']]={
                "bm25_object": bm25,
                "chunk_length": data["chunk_length"],
                "chunks": data["chunks"]}

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"retrieve_bm25_index_and_chunks endpoint failed:{str(e)}")



@app.get("/context_generation")
async def context_generation(query:str ="How can I solve my echo's noise problem?",
                             namespace:str ="dotlines",
                             user_session: UserSession = Depends(get_user_session)):

    try:
        user_session.length_of_total_chunks=user_session.bm25_dict[namespace]["chunk_length"]
        result_indexes=await fusion_retrieval(
            stats=stats, 
            Pinecone_index=Pinecone_index, 
            length_of_total_chunks=user_session.length_of_total_chunks, 
            embedding_model=embedding_model, 
            bm25=user_session.bm25_dict[namespace]["bm25_object"], 
            query=query, 
            namespace=namespace)
        results= [user_session.bm25_dict[namespace]["chunks"][i][1] for i in result_indexes]
        user_session.context=results[0]+results[1]+results[2]
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Context generation failed:{str(e)}")


@app.get("/response_generation")
async def response_generation(query:str ="How can I solve my echo's noise problem?",
                              namespace:str ="dotlines",
                              user_session: UserSession = Depends(get_user_session)):
    try:
        context= user_session.context
        generator = ResponseGenerator(query, context)
        response = generator.generation()
        return response
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Response generation failed:{str(e)}")
    



#hosting on localhost
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)

