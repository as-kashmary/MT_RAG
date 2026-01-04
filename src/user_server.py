# from fastapi import FastAPI, Request, status, HTTPException, Depends
# from pathlib import Path
# from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
# from fastapi.middleware.cors import CORSMiddleware
# import uvicorn
# import time
# import os
# from contextlib import asynccontextmanager

# from src.rag.fusion_retrieval import fusion_retrieval, create_bm25_index_v2
# from src.rag.response_generation import ResponseGenerator
# from src.rag.local_embeder import LocalEmbeddings

# from src.DB_Routes.mongodb_implementation import retrieve_bm25_index_and_chunks_using_company
# from src.DB_Routes.User_routes import router as user_router
# from pinecone import Pinecone

# from src.logging.logging import configure_logging, get_logger
# from src.logging.request_id import RequestIDMiddleware

# configure_logging(level="INFO", service_name="user-server")

# # Set default company ID (from environment variable or hardcoded for single-company setup)
# DEFAULT_COMPANY_ID = os.getenv("DEFAULT_COMPANY_ID", "1893ab51e6284c1b8ed64c88238b116b")




# class UserSession:
#     def __init__(self):
#         self.namespace = None
#         self.length_of_total_chunks = None
#         self.context = None
#         self.product_based_bm25_dict = {}
#         self.company_id = None
#         self.query = None
        

# sessions = {}


# def get_user_session(user_id: str):
#     if user_id not in sessions:
#         sessions[user_id] = UserSession()
#     return sessions[user_id]




# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     global embedding_model, Pinecone_index, stats
#     start_time = time.time()
#     logger.info("Starting up the server...")
    
#     embedding_model= LocalEmbeddings("./models/multilingual-e5-large-instruct")
#     embedding_model._load_model()
#     logger.info(f"Embeddings model loaded, bm25 objects loaded. Total elapsed time: {time.time() - start_time:.2f} seconds")
#     try:
#         pc = Pinecone(api_key="pcsk_2ht9Mg_9VwrnZM7wQrAiCkEfUTQFLDsPui6p9VxkcKbCPvKsVSUaR9jZwmeQwwuUpbpGJv")

#         Pinecone_index = pc.Index(host="https://test-11ejuti.svc.aped-4627-b74a.pinecone.io")
#         stats=Pinecone_index.describe_index_stats()
#         logger.info(f"Pinecone connected. Stats: {stats}")
#     except Exception as e:
#         logger.error(f"Pinecone connection failed: {str(e)}")
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Pinecone connection failed:{str(e)}")

    
#     yield
#     logger.info("Shutting down the server...")


# app = FastAPI(lifespan=lifespan)

# # Configure CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "http://localhost:5173",  # Vite dev server default port
#         "http://localhost:3000",  # Common dev port
#         "http://localhost:8080",  # Another common port
#         "http://127.0.0.1:5173",
#         "http://127.0.0.1:3000",
#         "http://127.0.0.1:8080",
#     ],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# """
# Added RequestIDMiddleware to log request ids in logs for tracing.

# """

# app.add_middleware(RequestIDMiddleware)

# # Include User routes
# app.include_router(user_router)

# logger = get_logger("user_server")



# @app.get("/retrieve_bm25_index_and_chunks")
# async def retrieve_bm25_index_and_chunks(user_id: str,
#                                         user_session: UserSession = Depends(get_user_session)):
#     try:
#         company_id = DEFAULT_COMPANY_ID  # Use default company_id
#         user_session.company_id = company_id
#         retrieved_data= retrieve_bm25_index_and_chunks_using_company(company_id)
#         # logger.info(f"Retrieved data: {retrieved_data}")
#         if retrieved_data is None:
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No BM25 index and chunks found for the given company_id. The mongodb collection might be empty.")
#         else:
#             logger.info(f"BM25 index and chunks retrieved successfully for company_id: {company_id}")
#             for data in retrieved_data:
#                 product_id=data['product_id']
#                 bm25=create_bm25_index_v2(data['bm25_index_variables'])
#                 chunk_tuples=[]
#                 for item in data['chunks']:
#                     for item2 in item['chunks']:
#                         chunk_tuples.append(item2)
                        
#                 user_session.product_based_bm25_dict[product_id]={
#                     "bm25_object": bm25,
#                     "chunk_length": data["chunk_length"],
#                     "chunks": chunk_tuples}
#         logger.info(f"BM25 indexes and chunks stored in user session for user_id: {user_id}")
#         # return  user_session.product_based_bm25_dict
#         return chunk_tuples

#     except Exception as e:
#         logger.error(f"retrieve_bm25_index_and_chunks endpoint failed: {str(e)}")
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"retrieve_bm25_index_and_chunks endpoint failed:{str(e)}")



# @app.get("/context_generation", response_class=JSONResponse)
# async def context_generation(product_id:str,
#                             query:str ="How can I solve my echo's noise problem?",
#                             user_session: UserSession = Depends(get_user_session)):

#     try:
#         user_session.query=query
#         namespace= f"{user_session.company_id}_{product_id}"
#         if product_id not in user_session.product_based_bm25_dict:
#             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"BM25 index and chunks for product_id: {product_id} not found in user session. Please retrieve it first using /retrieve_bm25_index_and_chunks endpoint.")
        
#         bm25=user_session.product_based_bm25_dict[product_id]["bm25_object"]
#         chunk_length=user_session.product_based_bm25_dict[product_id]["chunk_length"]
#         chunks=user_session.product_based_bm25_dict[product_id]["chunks"]
#         result_indexes=await fusion_retrieval(
#             stats=stats, 
#             Pinecone_index=Pinecone_index, 
#             length_of_total_chunks=chunk_length, 
#             embedding_model=embedding_model, 
#             bm25=bm25, 
#             query=query, 
#             namespace=namespace)
        
#         """
#         fusion retrieval returns the indexes starting from 0 to len(chunks)-1
#         but our chunks are stored in mongodb with index starting from 1 to len(chunks)
#         So we need to add 1 to each index before retrieving the chunks.
#         """
    
#         result_indexes=[int(i)+1 for i in result_indexes]
#         logger.info(f"Result indexes from fusion retrieval: {result_indexes}")
#         logger.info(f"Chunks structure (first item): {chunks[0] if chunks else 'Empty chunks'}")
#         logger.info(f"Total chunks available: {len(chunks)}")
#         logger.info(f"{chunks}")
        
#         """
#         Now let's sort the chunks according to the result_indexes order.
#         As throughout the retrieval the order may be changed.
#         """
#         sorted_chunks=[]
#         for idx in result_indexes:
#             for chunk_tuple in chunks:
#                 if chunk_tuple[0]==idx:
#                     sorted_chunks.append(chunk_tuple[1])
#                     break
#         user_session.context=sorted_chunks[0]+sorted_chunks[1]+sorted_chunks[2]

#         logger.info(f"Context generated successfully for query: {query}")
#         return {"context": user_session.context}
#     except Exception as e:
#         logger.error(f"Context generation failed: {str(e)}")
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Context generation failed:{str(e)}")


# @app.get("/response_generation", response_class=JSONResponse)
# async def response_generation(user_id: str,
#                               user_session: UserSession = Depends(get_user_session)):
#     try:
#         context= user_session.context
#         generator = ResponseGenerator(user_session.query, context)
#         response = generator.generation()
#         logger.info(f"Response generated successfully for query: {user_session.query}")
#         return JSONResponse(content=response)
#     except Exception as e:
#         logger.error(f"Response generation failed: {str(e)}")
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Response generation failed:{str(e)}")
    



# #hosting on localhost
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8001)




from fastapi import FastAPI, Request, status, HTTPException, Depends
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import time
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

# --- IMPORTS ---
from src.rag.fusion_retrieval import fusion_retrieval, create_bm25_index_v2
from src.rag.response_generation import ResponseGenerator
from src.rag.local_embeder import LocalEmbeddings
from src.DB_Routes.mongodb_implementation import retrieve_bm25_index_and_chunks_using_company
from src.DB_Routes.db_connection_new import DBSession
from src.DB_Routes.entities import ChatMessage, ChatSession, encode_uuid, decode_uuid

# IMPORT ROUTES
from src.DB_Routes.User_routes import router as user_router
from src.DB_Routes.product_routes import router as product_router 
from src.DB_Routes.chat_routes import router as history_router # NEW

from pinecone import Pinecone
from src.logging.logging import configure_logging, get_logger
from src.logging.request_id import RequestIDMiddleware

configure_logging(level="INFO", service_name="user-server")
logger = get_logger("user_server")

DEFAULT_COMPANY_ID = os.getenv("DEFAULT_COMPANY_ID", "1893ab51e6284c1b8ed64c88238b116b")

class ChatRequest(BaseModel):
    userId: str
    productId: str 
    sessionId: str | None = None # NEW
    message: str

class ChatResponse(BaseModel):
    role: str
    content: str
    sessionId: str # NEW

class UserSession:
    def __init__(self):
        self.product_based_bm25_dict = {}
        self.company_id = DEFAULT_COMPANY_ID
        self.context = "" 

sessions = {}

def get_user_session(user_id: str) -> UserSession:
    if user_id not in sessions:
        sessions[user_id] = UserSession()
    return sessions[user_id]

@asynccontextmanager
async def lifespan(app: FastAPI):
    global embedding_model, Pinecone_index, stats
    logger.info("Starting up server...")
    embedding_model = LocalEmbeddings("./models/multilingual-e5-large-instruct")
    embedding_model._load_model()
    
    try:
        pc = Pinecone(api_key="pcsk_2ht9Mg_9VwrnZM7wQrAiCkEfUTQFLDsPui6p9VxkcKbCPvKsVSUaR9jZwmeQwwuUpbpGJv")
        Pinecone_index = pc.Index(host="https://test-11ejuti.svc.aped-4627-b74a.pinecone.io")
        stats = Pinecone_index.describe_index_stats()
    except Exception as e:
        logger.error(f"Pinecone connection failed: {str(e)}")
        
    yield
    logger.info("Shutting down...")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)

# REGISTER ROUTES
app.include_router(user_router)
app.include_router(product_router)
app.include_router(history_router) # NEW

async def load_company_data_into_session(session: UserSession):
    if session.product_based_bm25_dict: return 
    retrieved_data = retrieve_bm25_index_and_chunks_using_company(session.company_id)
    if not retrieved_data: return

    for data in retrieved_data:
        p_id = data.get('product_id', 'default')
        bm25 = create_bm25_index_v2(data['bm25_index_variables'])
        chunk_tuples = []
        for item in data['chunks']:
            sub_chunks = item.get('chunks', [])
            chunk_tuples.extend(sub_chunks)

        session.product_based_bm25_dict[p_id] = {
            "bm25_object": bm25,
            "chunk_length": data["chunk_length"],
            "chunks": chunk_tuples
        }

@app.post("/warmup")
async def warmup_endpoint(request: ChatRequest):
    try:
        session = get_user_session(request.userId)
        await load_company_data_into_session(session)
        return {"status": "ready"}
    except Exception as e:
        return {"status": "partial", "message": str(e)}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: DBSession):
    try:
        session = get_user_session(request.userId)
        await load_company_data_into_session(session)

        # 1. Handle Session Creation
        session_uuid = None
        if request.sessionId:
            session_uuid = encode_uuid(request.sessionId)
        else:
            new_session = ChatSession(
                user_id=encode_uuid(request.userId),
                product_id=encode_uuid(request.productId),
                title=request.message[:50]
            )
            db.add(new_session)
            await db.commit()
            session_uuid = new_session.id

        # 2. RAG Logic
        target_product_id = request.productId
        if target_product_id not in session.product_based_bm25_dict:
             if session.product_based_bm25_dict:
                 target_product_id = next(iter(session.product_based_bm25_dict))
             else:
                 return {"role": "assistant", "content": "No documents loaded.", "sessionId": str(decode_uuid(session_uuid))}

        product_data = session.product_based_bm25_dict[target_product_id]
        namespace = f"{session.company_id}_{target_product_id}"
        
        result_indexes = await fusion_retrieval(
            stats=stats,
            Pinecone_index=Pinecone_index,
            length_of_total_chunks=product_data["chunk_length"],
            embedding_model=embedding_model,
            bm25=product_data["bm25_object"],
            query=request.message,
            namespace=namespace
        )

        result_indexes = [int(i) + 1 for i in result_indexes]
        chunk_map = {c[0]: c[1] for c in product_data["chunks"]}
        sorted_chunks = [chunk_map[idx] for idx in result_indexes if idx in chunk_map]
        context_text = " ".join(sorted_chunks[:3])
        
        generator = ResponseGenerator(request.message, context_text)
        final_answer = generator.generation()

        # 3. Save to DB
        user_msg = ChatMessage(session_id=session_uuid, role="user", content=request.message)
        ai_msg = ChatMessage(session_id=session_uuid, role="assistant", content=final_answer)
        db.add_all([user_msg, ai_msg])
        
        session_obj = await db.get(ChatSession, session_uuid)
        if session_obj: session_obj.updated_at = datetime.now(timezone.utc)
        
        await db.commit()

        return {
            "role": "assistant",
            "content": final_answer,
            "sessionId": str(decode_uuid(session_uuid))
        }

    except Exception as e:
        logger.error(f"Chat failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
