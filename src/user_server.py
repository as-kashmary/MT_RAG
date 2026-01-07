from fastapi import FastAPI, Request, status, HTTPException, Depends
from pathlib import Path
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
import uvicorn
import time
from contextlib import asynccontextmanager

from src.rag.fusion_retrieval import fusion_retrieval, create_bm25_index_v2
from src.rag.response_generation import ResponseGenerator
from src.rag.local_embeder import LocalEmbeddings

from src.DB_Routes.mongodb_implementation import retrieve_bm25_index_and_chunks_using_company
from pinecone import Pinecone

from src.logging.logging import configure_logging, get_logger
from src.logging.request_id import RequestIDMiddleware

configure_logging(level="INFO", service_name="user-server")




class UserSession:
    def __init__(self):
        self.namespace = None
        self.length_of_total_chunks = None
        self.context = None
        self.product_based_bm25_dict = {}
        self.company_id = None
        self.query = None
        

sessions = {}


def get_user_session(user_id: str):
    if user_id not in sessions:
        sessions[user_id] = UserSession()
    return sessions[user_id]




@asynccontextmanager
async def lifespan(app: FastAPI):
    global embedding_model, Pinecone_index, stats
    start_time = time.time()
    logger.info("Starting up the server...")
    
    embedding_model= LocalEmbeddings("./models/multilingual-e5-large-instruct")
    embedding_model._load_model()
    logger.info(f"Embeddings model loaded, bm25 objects loaded. Total elapsed time: {time.time() - start_time:.2f} seconds")
    try:
        pc = Pinecone(api_key="pcsk_2ht9Mg_9VwrnZM7wQrAiCkEfUTQFLDsPui6p9VxkcKbCPvKsVSUaR9jZwmeQwwuUpbpGJv")

        Pinecone_index = pc.Index(host="https://test-11ejuti.svc.aped-4627-b74a.pinecone.io")
        stats=Pinecone_index.describe_index_stats()
        logger.info(f"Pinecone connected. Stats: {stats}")
    except Exception as e:
        logger.error(f"Pinecone connection failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Pinecone connection failed:{str(e)}")

    
    yield
    logger.info("Shutting down the server...")


app = FastAPI(lifespan=lifespan)


"""
Added RequestIDMiddleware to log request ids in logs for tracing.

"""

app.add_middleware(RequestIDMiddleware)
logger = get_logger("user_server")



@app.get("/retrieve_bm25_index_and_chunks")
async def retrieve_bm25_index_and_chunks(user_id: str,
                                        company_id: str,
                                        user_session: UserSession = Depends(get_user_session)):
    try:
        user_session.company_id= company_id
        retrieved_data= retrieve_bm25_index_and_chunks_using_company(company_id)
        # logger.info(f"Retrieved data: {retrieved_data}")
        if retrieved_data is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No BM25 index and chunks found for the given company_id. The mongodb collection might be empty.")
        else:
            logger.info(f"BM25 index and chunks retrieved successfully for company_id: {company_id}")
            for data in retrieved_data:
                product_id=data['product_id']
                bm25=create_bm25_index_v2(data['bm25_index_variables'])
                chunk_tuples=[]
                for item in data['chunks']:
                    for item2 in item['chunks']:
                        chunk_tuples.append(item2)
                        
                user_session.product_based_bm25_dict[product_id]={
                    "bm25_object": bm25,
                    "chunk_length": data["chunk_length"],
                    "chunks": chunk_tuples}
        logger.info(f"BM25 indexes and chunks stored in user session for user_id: {user_id}")
        # return  user_session.product_based_bm25_dict
        return chunk_tuples

    except Exception as e:
        logger.error(f"retrieve_bm25_index_and_chunks endpoint failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"retrieve_bm25_index_and_chunks endpoint failed:{str(e)}")



@app.get("/context_generation", response_class=JSONResponse)
async def context_generation(product_id:str,
                            query:str ="How can I solve my echo's noise problem?",
                            user_session: UserSession = Depends(get_user_session)):

    try:
        user_session.query=query
        namespace= f"{user_session.company_id}_{product_id}"
        if product_id not in user_session.product_based_bm25_dict:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"BM25 index and chunks for product_id: {product_id} not found in user session. Please retrieve it first using /retrieve_bm25_index_and_chunks endpoint.")
        
        bm25=user_session.product_based_bm25_dict[product_id]["bm25_object"]
        chunk_length=user_session.product_based_bm25_dict[product_id]["chunk_length"]
        chunks=user_session.product_based_bm25_dict[product_id]["chunks"]
        result_indexes=await fusion_retrieval(
            stats=stats, 
            Pinecone_index=Pinecone_index, 
            length_of_total_chunks=chunk_length, 
            embedding_model=embedding_model, 
            bm25=bm25, 
            query=query, 
            namespace=namespace)
        
        """
        fusion retrieval returns the indexes starting from 0 to len(chunks)-1
        but our chunks are stored in mongodb with index starting from 1 to len(chunks)
        So we need to add 1 to each index before retrieving the chunks.
        """
    
        result_indexes=[int(i)+1 for i in result_indexes]
        logger.info(f"Result indexes from fusion retrieval: {result_indexes}")
        logger.info(f"Chunks structure (first item): {chunks[0] if chunks else 'Empty chunks'}")
        logger.info(f"Total chunks available: {len(chunks)}")
        logger.info(f"{chunks}")
        
        """
        Now let's sort the chunks according to the result_indexes order.
        As throughout the retrieval the order may be changed.
        """
        sorted_chunks=[]
        for idx in result_indexes:
            for chunk_tuple in chunks:
                if chunk_tuple[0]==idx:
                    sorted_chunks.append(chunk_tuple[1])
                    break
        user_session.context=sorted_chunks[0]+sorted_chunks[1]+sorted_chunks[2]

        logger.info(f"Context generated successfully for query: {query}")
        return {"context": user_session.context}
    except Exception as e:
        logger.error(f"Context generation failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Context generation failed:{str(e)}")


@app.get("/response_generation", response_class=JSONResponse)
async def response_generation(user_id: str,
                              user_session: UserSession = Depends(get_user_session)):
    try:
        context= user_session.context
        generator = ResponseGenerator(user_session.query, context)
        response = generator.generation()
        logger.info(f"Response generated successfully for query: {user_session.query}")
        user_session.context= None  # Freeing up memory
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"Response generation failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Response generation failed:{str(e)}")
    



#hosting on localhost
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)

