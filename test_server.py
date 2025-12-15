from fastapi import FastAPI, status, HTTPException
import uvicorn
from contextlib import asynccontextmanager
import os

from DB_Routes.Company_routes import router as company_router
from DB_Routes.User_routes import router as user_router
from DB_Routes.File_routes import router as file_router
from DB_Routes.query_routes import router as query_router
from DB_Routes.Admin_routes import router as admin_router
from DB_Routes.db_connection_new import DBSession, Base

from src.document_loader import read_txt_to_string
from src.semantic_chunker import SemanticChunking
from src.local_embeder import LocalEmbeddings
from src.vector_store import sending_to_pinecone



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