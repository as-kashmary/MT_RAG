from db_connection import session, File, Company, User
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.rag.document_loader import read_txt_to_string
from src.rag.semantic_chunker import SemanticChunking
from src.rag.local_embeder import LocalEmbeddings
from src.rag.vector_store import sending_to_pinecone


from .Company_routes import router as company_router
from .User_routes import router as user_router
from .File_routes import router as file_router
from .query_routes import router as query_router

from db_update import update_file_status_successful, update_file_status_failed, update_file_status_running
from db_fetch import fetch_company_by_name, fetch_file_by_company_pending


embeddings= LocalEmbeddings("./models/multilingual-e5-large-instruct")
embeddings._load_model()

file_dir="download_dir"

company_name="Dotlines"

company= fetch_company_by_name(company_name=company_name, session=session)
if company:
    company_id= company.id
    files= fetch_file_by_company_pending(company_id=company_id, session=session)
    for file in files:
        file_path= os.path.join(file_dir, file.file_name)
        with open(file_path, "wb") as f:
            f.write(file.file_data)
        print(f"File {file.file_name} saved to {file_path}")
        content= read_txt_to_string(file_path)
        update_file_status_running(file_id=file.id, session=session)

        chunks=SemanticChunking(content, embeddings)
        vectors = embeddings.embed_documents(chunks.get_chunks())
        ids = [str(i) for i in range(len(vectors))]
        metadata_list = [{"text": chunk} for chunk in chunks.get_chunks()]
        try:
            await sending_to_pinecone(vectors=vectors, ids=ids, metadata_list=metadata_list, namespace=company_name)
            print(f"File {file.file_name} processed and uploaded to vector DB.")
            update_file_status_successful(file_id=file.id, session=session)
            # delete the file after processing  
            os.remove(file_path)
            print(f"File {file.file_name} removed from local storage.")
        except Exception as e:
            print(f"Error processing file {file.file_name}: {e}")
            update_file_status_failed(file_id=file.id, session=session)
            continue

else:
    print(f"Company {company_name} not found in the database.")


# for file_name, file_object in zip(os.listdir(file_dir),files):
#     file_path= os.path.join(file_dir, file_name)
#     content= read_txt_to_string(file_path)
#     update_file_status_running(file_object.id, True, session)
#     embeddings= HFInferenceEmbeddings(
#         model="intfloat/multilingual-e5-large-instruct",
#         api_key="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"
#     )
#     chunks=SemanticChunking(content, embeddings)
#     vectors = embeddings.embed_documents(chunks.get_chunks())
#     ids = [str(i) for i in range(len(vectors))]
#     metadata_list = [{"text": chunk} for chunk in chunks.get_chunks()]
#     sending_to_pinecone(vectors=vectors, ids=ids, metadata_list=metadata_list, namespace=company_name)
#     print(f"File {file_name} processed and uploaded to vector DB.")
#     update_file_status_successful(file_object.id, True, session)
#     # delete the file after processing  
#     os.remove(file_path)
#     print(f"File {file_name} removed from local storage.")

    