from fastapi import FastAPI, status, HTTPException
import uvicorn
from contextlib import asynccontextmanager
import os

from src.DB_Routes.Company_routes import router as company_router
from src.DB_Routes.User_routes import router as user_router
from src.DB_Routes.File_routes import router as file_router
from src.DB_Routes.query_routes import router as query_router
from src.DB_Routes.Admin_routes import router as admin_router
from src.DB_Routes.db_connection_new import DBSession, Base

from src.rag.document_loader import read_txt_to_string
from src.rag.semantic_chunker import SemanticChunking
from src.rag.local_embeder import LocalEmbeddings
from src.rag.vector_store import sending_to_pinecone

from src.logging.logging import configure_logging, get_logger
configure_logging(level="INFO", service_name="test-server")
logger= get_logger("test_server")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # global embeddings
    # embeddings= LocalEmbeddings("./models/multilingual-e5-large-instruct")
    # embeddings._load_model()
    yield




app= FastAPI(lifespan=lifespan)



app.include_router(company_router)
app.include_router(user_router)
app.include_router(file_router)
app.include_router(query_router)
app.include_router(admin_router)

if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000)