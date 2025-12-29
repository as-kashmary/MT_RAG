import time
import json
import uvicorn
import sys
import os
from fastapi import FastAPI, Request, status, Depends, HTTPException
from pathlib import Path
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
import argparse

from pinecone import Pinecone

# PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# sys.path.insert(0, PROJECT_ROOT)

from src.rag.document_loader import read_txt_to_string, read_pdf_to_string, read_docx_to_string
from src.rag.vector_store import sending_to_pinecone, retrieve_namespace, query_pinecone, retrieve_length_of_namespace
from src.rag.fusion_retrieval import fusion_retrieval, create_bm25_index, new_create_BM25Okapi_index, new_create_BM25Okapi_without_corpus_index, create_bm25_index_v2
from src.rag.semantic_chunker import SemanticChunking
from contextlib import asynccontextmanager

from src.rag.local_embeder import LocalEmbeddings
from src.DB_Routes.mongodb_implementation_copy import (
    store_bm25_index_and_chunks_in_mongodb_for_specific_product, 
    retrieve_bm25_index_and_chunks_using_company, 
    update_bm25_index_and_chunks_in_mongodb, 
    retrieve_chunks_from_mongodb)

from src.logging.logging import configure_logging, get_logger
from src.logging.request_id import RequestIDMiddleware

configure_logging(level="INFO", service_name="admin-server")

class AdminSession:
    def __init__(self):
        self.chunks_list = []
        self.company_id = None
        self.bm25 = None
        # self.length_of_total_chunks = None
        # Initialized to list so downstream code can append
        self.vectors = []
        self.parsed_contents_list = []       
        self.product_variable_list = []
        self.all_variable_list = []
        self.created_or_not = False
        # self.namespace = None
        self.retrieved_chunk_length = 0
        self.retrieved_product_ids=[]
        self.chunk_length={}
        self.product_based_chunk_info={}
        self.product_based_vector_info={}
        self.retrieved_product_data={}
        


sessions = {}

def get_admin_session(admin_id: str = None):
    """
    Get or create an AdminSession for a given admin_id.
    If admin_id is not provided, a ValueError is raised to prevent session confusion.
    """
    if admin_id is None:
        raise ValueError("admin_id is required as a query parameter")
    
    if admin_id not in sessions:
        sessions[admin_id] = AdminSession()
    return sessions[admin_id]



@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Currrent idea is to load the embedding model and bm25 index here on startup and keep them in global variables for use in the routes.
    This way we don't have to load them every time a request comes in, which would be very inefficient.

    """

    global embedding_model, Pinecone_index, stats
    start_time = time.time()

    logger.info("Starting up the RAG server...")

    embedding_model= LocalEmbeddings("./models/multilingual-e5-large-instruct")
    embedding_model._load_model()
    logger.info(f"Embeddings model loaded. Total elapsed time: {time.time() - start_time:.2f} seconds")
    try:
        pc = Pinecone(api_key="pcsk_2ht9Mg_9VwrnZM7wQrAiCkEfUTQFLDsPui6p9VxkcKbCPvKsVSUaR9jZwmeQwwuUpbpGJv")

        Pinecone_index = pc.Index(host="https://test-11ejuti.svc.aped-4627-b74a.pinecone.io")
        stats=Pinecone_index.describe_index_stats()
        logger.info(f"Pinecone connected. Stats: {stats}")
    except Exception as e:
        logger.error(f"Pinecone connection failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Pinecone connection failed:{str(e)}")

    yield
    logger.info("Shutting down the RAG server...")

app = FastAPI(lifespan=lifespan)


"""
Added RequestIDMiddleware to log request ids in logs for tracing.

"""

app.add_middleware(RequestIDMiddleware)
logger = get_logger("admin_server")


@app.post("/parser")
async def parser(admin_id: str,
                 product_id: str,
                 company_id: str,
                 document_path: str,
                 admin_session: AdminSession = Depends(get_admin_session)):
    """
    Here, we parse different document types and return their contents as strings.
    This will be called before chunking.
    """
    """
    We have to implement multiprocessing here to speed up the parsing of multiple documents.
    """
    try:
        start_time=time.time()
        admin_session.company_id= company_id

        def file_type_checker(file_name):
            if file_name.endswith(".pdf"):
                return "pdf"
            elif file_name.endswith(".txt"):
                return "txt"
            elif file_name.endswith(".docx"):
                return "docx"
            else:
                return "unknown"
            
        # Handle both file path and directory path
        if os.path.isfile(document_path):
            # document_path is a file
            file_path = document_path
            filename = os.path.basename(document_path)
        elif os.path.isdir(document_path):
            # document_path is a directory - get the first file
            filenames = os.listdir(document_path)
            
            if not filenames:
                raise ValueError(f"No files found in {document_path}")
            
            filename = filenames[0]
            file_path = os.path.join(document_path, filename)
        else:
            raise ValueError(f"Invalid path: {document_path} (not a file or directory)")
        
        file_type = file_type_checker(filename)
        if file_type == "txt":
            content = read_txt_to_string(file_path)
        elif file_type == "docx":
            content = read_docx_to_string(file_path)
        elif file_type == "pdf":
            content = read_pdf_to_string(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        admin_session.parsed_contents_list.append({
            "file_name": filename,
            "product_id": product_id,
            "company_id": company_id,
            "content": content
        })
    
        parsing_time = time.time() - start_time
        logger.info(f"Parsed {filename} document from {document_path} in {parsing_time:.2f} seconds for product {product_id} and company {company_id}.")
        
        return admin_session.parsed_contents_list

    except Exception as e:
        logger.error(f"Parsing failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Parsing failed:{str(e)}")


@app.post("/chunk")
async def chunk(admin_id: str,
                company_id: str="abcd",
                admin_session: AdminSession = Depends(get_admin_session)):
    start_time=time.time()
    admin_session.chunks_list = []
    admin_session.company_id= company_id
    # global document_list, bm25, length_of_total_chunks, created_or_not, variable_list, namespace1
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
    """
    26/12/2025
    Creating chunks for every product's documents. Saving them on the basis of file_name, product_id, company_id. 
    Because whenever the documents of namespace of a particular company or product will be updated, we have to update the chunks accordingly.
    We also have to calculate bm25 index for every product's documents separately. and a bm25 index for every company separately.
    So if a company has 3 products, then there will be 3 bm25 indexes for products and 1 bm25 index for company.
    
    """

    try:
        """
        Now chunking the contents present in admin_session.chunks_list
        The chunks are presented in admin_session.chunks_list in this format:
        [
            {
                "file_name": "file1.pdf",
                "product_id": "product1",
                "company_id": "company",
                "chunks": chunks_list_for_file1
            },
        ]
        """
        # Validate that we have parsed content
        if not admin_session.parsed_contents_list:
            raise ValueError("No parsed content available. Call /parser endpoint first.")
        
        unique_product_ids = set([item['product_id'] for item in admin_session.parsed_contents_list])
        logger.info(f"Unique product ids found for company {admin_session.company_id}: {unique_product_ids}")
        product_based_chunks = []
        all_chunks = []
        for id in unique_product_ids:
            admin_session.chunk_length[id]=0
        admin_session.chunk_length["X"]=0  # For company-wide chunks
        

        
        for content in admin_session.parsed_contents_list:
            product_id= content["product_id"]
            file_name= content["file_name"]
            semantic_chunk_object= SemanticChunking(content["content"], embedding_model)
            logger.info(f"Number of chunks created from a document: {len(semantic_chunk_object.get_chunks())} for {content['file_name']}")
            # Just saving the chunks in memory for now using chunks_list attribute of admin_session.
            chunk_texts= semantic_chunk_object.get_chunks()
            chunk_tuples= []
            chunk_tuples_company_wide= []
            for i in range(len(chunk_texts)):
                admin_session.chunk_length[product_id]+=1
                admin_session.chunk_length["X"]+=1
                chunk_tuples.append( (admin_session.chunk_length[product_id], chunk_texts[i]) )
                chunk_tuples_company_wide.append( (admin_session.chunk_length["X"], chunk_texts[i]) )
            chunk_length=len(chunk_texts)

            admin_session.chunks_list.append({
                "file_name": file_name,
                "product_id": product_id,
                "company_id": content["company_id"],
                "chunks": [{'file_name': content["file_name"], 'chunks': chunk_tuples}],
                "chunk_length": chunk_length
            })
            admin_session.chunks_list.append({
                "file_name": file_name,
                "product_id": "X",
                "company_id": content["company_id"],
                "chunks": [{'file_name': content["file_name"], 'chunks': chunk_tuples_company_wide }],
                "chunk_length": chunk_length
            })
        
        """
        admin_session.chunks_list is now populated with chunks for every document. 
        Now we will sort the chunks based on product_id and company_id for further processing in product_based_chunks.
        """
        unique_product_ids.add("X")  # Adding company-wide product_id
        for product_id in unique_product_ids:
            chunks_for_product = []
            chunk_length_for_product = 0
            for item in admin_session.chunks_list:
                if item["product_id"] == product_id and item["company_id"]==admin_session.company_id:
                    chunks_for_product.extend(item["chunks"])

            chunk_length_for_product = admin_session.chunk_length[product_id]
            
            admin_session.product_based_chunk_info[product_id]= {
                "product_id": product_id,
                "company_id": admin_session.company_id,
                "chunks_with_file_name": chunks_for_product,
                "bm_25_index_variables": None,
                "chunk_length": chunk_length_for_product,
                "old_chunk":[],
                "old_chunk_length":0
            }
        
        

        data = retrieve_bm25_index_and_chunks_using_company(admin_session.company_id)
        admin_session.created_or_not= False
        if data is not None:
            for entry in data:
                if entry['product_id'] not in admin_session.retrieved_product_data:
                    admin_session.retrieved_product_data[entry['product_id']] = entry
        """
        If data is None, then we have to create a new bm25 index and store it in mongodb.
        Otherwise, we have to retrieve the bm25 index from mongodb and update it with the new chunks.
        Now for every product in the chunks_list, we will create or update the bm25 index accordingly.
        """
        for item in admin_session.product_based_chunk_info:
            product_id= item
            
            if product_id not in admin_session.retrieved_product_data:
                """
                Logic for creating the info of product for the first time
                """
                chunk_texts=[]
                for chunk_item in admin_session.product_based_chunk_info[item]["chunks_with_file_name"]:
                    for text in chunk_item['chunks']:
                        chunk_texts.append(text[1])

                bm25_index=create_bm25_index(chunk_texts)
                bm25_variables= bm25_index.return_variables()
                admin_session.product_based_chunk_info[item]["bm_25_index_variables"]= bm25_variables
            if product_id in admin_session.retrieved_product_data:
                """
                logic for updating the info of product
                """
                old_data=admin_session.retrieved_product_data[product_id]
                admin_session.product_based_chunk_info[item]["old_chunk"]= old_data["chunks"]
                admin_session.product_based_chunk_info[item]["old_chunk_length"]= old_data["chunk_length"]
                old_chunk_length= old_data["chunk_length"]
                chunk_texts=[]
                chunks_with_file_name=[]
                for chunk_item in admin_session.product_based_chunk_info[item]["chunks_with_file_name"]:
                    chunk_tuples=[]
                    file_name= chunk_item['file_name']
                    for text in chunk_item['chunks']:
                        chunk_texts.append(text[1])
                        chunk_tuples.append( (text[0]+ old_chunk_length, text[1]) )
                    chunks_with_file_name.append({
                        "file_name": file_name,
                        "chunks": chunk_tuples
                    })
                admin_session.product_based_chunk_info[item]["chunks_with_file_name"]= chunks_with_file_name
                old_variables= old_data["bm25_index_variables"]
                old_bm25_index= create_bm25_index_v2(old_variables)
                updated_bm25_index= new_create_BM25Okapi_without_corpus_index(chunk_texts, old_bm25_index)
                bm25_variables= updated_bm25_index.return_variables()
                admin_session.product_based_chunk_info[item]["bm_25_index_variables"]= bm25_variables


        logger.info(f"Chunking completed for company {admin_session.company_id} in {time.time() - start_time:.2f} seconds.")

        chunking_time = time.time() - start_time
        logger.info(f"Chunking Time: {chunking_time:.2f} seconds")
        """
        28/11/2025

        We will not save the chunks in a json file anymore. It's inefficient and unnecessary.
        We found out that after sending to pinecone, only place where chunks are required as texts is fusion retrieval.
        So we are stil figuring out ways to avoid storing and passsing them in memory.
        If it required mongodb implementation then it can be done later.
        """

        return admin_session.product_based_chunk_info

    

    except Exception as e:
        logger.error(f"Chunking failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Chunking failed:{str(e)}")

    

@app.get("/vectorizing")
async def vectorizing(admin_id: str,
                    admin_session: AdminSession = Depends(get_admin_session)):
    """
    28/11/2025
    Chunks are stored in document_list global variable after chunking.
    Here, we vectorize the chunks and store them in Pinecone vectorstore.
    This will be called after chunking.
    """ 

    start_time=time.time()
    # global vectors

    try:
        """
        For every product's file_name's chunks in product_variable_list, we will vectorize them and store them with proper filename metadata.
        """
        for item in admin_session.product_based_chunk_info:
            """
            Here's the format of admin.session.product_based_vector_info{
                product_id: {
                    "company_id": company_id,
                    "namespace": f"{company_id}_{product_id}",
                    "total_chunks": total_chunks,
                    "ids": [list of ids],
                    "vectors": [list of vectors],
                    "metadata": [
                       { "filename": filename,
                        "product_id": product_id,
                        "chunk": chunk_text},
                        ...
                    ]


                }
            }

            """
            product_id= item
            chunk_texts=[]
            ids=[]
            metadata_list=[]
            chunk_length= admin_session.product_based_chunk_info[item]["chunk_length"]
            

            
            for chunk_item in admin_session.product_based_chunk_info[item]["chunks_with_file_name"]:
                file_name= chunk_item['file_name']
                for text in chunk_item['chunks']:
                    chunk_texts.append(text[1])
                    ids.append( str(text[0]) )
                    metadata_list.append({
                        "file_name": file_name,
                        "product_id": product_id,
                        "company_id": admin_session.company_id,
                        "chunk": text[1]
                    })
            chunk_vectors= embedding_model.embed_documents(chunk_texts)
            admin_session.product_based_vector_info[product_id]= {
                "company_id": admin_session.company_id,
                "namespace": f"{admin_session.company_id}_{product_id}",
                "total_chunks": chunk_length,
                "ids": ids,
                "vectors": chunk_vectors,
                "metadata": metadata_list
            }

            
        
        embedding_time = time.time() - start_time
        logger.info(f"Embedding Time: {embedding_time:.2f} seconds")
        # return admin_session.product_based_vector_info
    except Exception as e:
        logger.error(f"Embedding failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Embedding failed:{str(e)}")


@app.post("/store")
async def store(admin_id: str,
                admin_session: AdminSession = Depends(get_admin_session)):
    start_time=time.time()
    try:
        """
        mainly the data of mongodb will be collected from admin_session.product_based_chunk_info
        And for the data of pinecone, it will be collected from admin_session.product_based_vector_info
        """
        for product_id in  admin_session.product_based_chunk_info:
            if product_id not in admin_session.retrieved_product_data:
                """
                Logic for storing the info of product for the first time
                """
                bm25_variables= admin_session.product_based_chunk_info[product_id]["bm_25_index_variables"]
                chunks= list(admin_session.product_based_chunk_info[product_id]["old_chunk"])+admin_session.product_based_chunk_info[product_id]["chunks_with_file_name"]
                chunk_length= admin_session.product_based_chunk_info[product_id]["chunk_length"]
                store_bm25_index_and_chunks_in_mongodb_for_specific_product(bm25_variables, chunks, admin_session.company_id, product_id, chunk_length)
            if product_id in admin_session.retrieved_product_data:
                """
                logic for updating the info of product
                """
                bm25_variables= admin_session.product_based_chunk_info[product_id]["bm_25_index_variables"]
                chunks= list(admin_session.product_based_chunk_info[product_id]["old_chunk"])+admin_session.product_based_chunk_info[product_id]["chunks_with_file_name"]
                chunk_length= admin_session.product_based_chunk_info[product_id]["chunk_length"]+ admin_session.product_based_chunk_info[product_id]["old_chunk_length"]
                update_bm25_index_and_chunks_in_mongodb(bm25_variables, chunks, admin_session.company_id, product_id, chunk_length)

            await sending_to_pinecone(
                stats,
                Pinecone_index,
                admin_session.product_based_vector_info[product_id]["vectors"],
                admin_session.product_based_vector_info[product_id]["ids"],
                admin_session.product_based_vector_info[product_id]["metadata"],
                admin_session.product_based_vector_info[product_id]["namespace"]
            )
        logger.info(f"Storing completed for company {admin_session.company_id} in {time.time() - start_time:.2f} seconds.")


    except Exception as e:
        logger.error(f"Storing failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Storing failed:{str(e)}")
        
    
    vector_storing_time = time.time() - start_time
    logger.info(f"Vector Storing Time: {vector_storing_time:.2f} seconds")

    


#hosting on localhost
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)