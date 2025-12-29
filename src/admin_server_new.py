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


@app.post("/parser",response_class=JSONResponse)
async def parser(admin_id: str,
                 product_id: str,
                 company_id: str,
                 document_path: str,
                 admin_session: AdminSession = Depends(get_admin_session))-> JSONResponse:
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
        
        return {"message": "Document parsed successfully",
                "product_id":product_id,
                "company_id":company_id,
                "file_name":filename,
                "content": content}

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
        for content in admin_session.parsed_contents_list:
            semantic_chunk_object= SemanticChunking(content["content"], embedding_model)
            logger.info(f"Number of chunks created from a document: {len(semantic_chunk_object.get_chunks())} for {content['file_name']}")
            # Just saving the chunks in memory for now using chunks_list attribute of admin_session.

            admin_session.chunks_list.append({
                "file_name": content["file_name"],
                "product_id": content["product_id"],
                "company_id": content["company_id"],
                "chunks": [{'file_name': content["file_name"], 'chunks': semantic_chunk_object.get_chunks()}]
            })
            """
            We are checking if the product_id already exists in product_based_chunks list. If not, we create a new entry.
            If it exists, we append the new chunks to the existing entry.
            """
            if content["product_id"] not in [item['product_id'] for item in product_based_chunks]:
                product_based_chunks.append({
                    "file_name": content["file_name"],
                    "product_id": content["product_id"],
                    "company_id": content["company_id"],
                    "chunks_with_file_name": [{'file_name': content["file_name"], 'chunks': semantic_chunk_object.get_chunks()}]
                })
            else:
                """
                Append the new chunks to the existing entry.
                """
                for item in product_based_chunks:
                    if item['product_id'] == content["product_id"] and item["company_id"]==content["company_id"]:
                        new_chunk_with_file_name = {'file_name': content["file_name"], 'chunks': semantic_chunk_object.get_chunks()}
                        item['chunks_with_file_name'].append(new_chunk_with_file_name)
                        break 

            """
            This is for creating company wide "X" bm25 index. Product id is "X" is the common namespace for all products of a company.
            """
            all_chunks.append({'file_name': content["file_name"], 'chunks': semantic_chunk_object.get_chunks()})
        

        data = retrieve_bm25_index_and_chunks_using_company(admin_session.company_id)
        admin_session.created_or_not= False
        """
        If data is None, then we have to create a new bm25 index and store it in mongodb.
        Otherwise, we have to retrieve the bm25 index from mongodb and update it with the new chunks.
        Now for every product in the chunks_list, we will create or update the bm25 index accordingly.
        """
        logger.info(f"Retrieved BM25 index data from MongoDB for company {admin_session.company_id}: {data}")
        retrieved_product_ids=[]
        if data is not None:
            for item in data:
                retrieved_product_ids.append(item["product_id"])

        admin_session.retrieved_product_ids= retrieved_product_ids
            
        # logger.info(f"Here's the product_based_chunks for company {admin_session.company_id}: {product_based_chunks}")
        logger.info(f"Retrieved product ids from MongoDB for company {admin_session.company_id}: {retrieved_product_ids}")
        for product_id in unique_product_ids:
            if product_id not in retrieved_product_ids:
                logger.info(f"Not found in retrieved data. Creating new BM25 index for product {product_id}.")
                chunks=[]
                for item in product_based_chunks:
                    if item["product_id"]==product_id and item["company_id"]==admin_session.company_id:
                        chunks= item["chunks_with_file_name"]
                        break
                # logger.info(f"Chunks found for product {product_id}: {chunks}")

                # Validate chunks not empty before creating BM25 index
                if not chunks:
                    logger.warning(f"No chunks found for product {product_id}. Skipping BM25 index creation.")
                    continue
                # Flatten chunk text list for BM25
                chunk_texts = []
                for entry in chunks:
                    chunk_texts.extend(entry['chunks'])

                logger.info(f"Creating new BM25 index for product {product_id} with {len(chunk_texts)} chunks.")
                
                bm25_index=create_bm25_index(chunk_texts)
                variable_list= bm25_index.return_variables()
                admin_session.product_variable_list.append({
                    "product_id": product_id,
                    "variables": variable_list,
                    "chunk_length": len(chunk_texts),
                    "old_chunk_length":0,
                    "chunks": chunks,
                    "old_chunks": []
                })
                admin_session.created_or_not= True

                bm25_index=None
                variable_list=None
            
            elif product_id in retrieved_product_ids:
                logger.info(f"Found in retrieved data. Updating existing BM25 index for product {product_id}.")
                """
                Retrieve the existing bm25 index variables from mongodb and create the bm25 index.
                """
                old_chunk_length=0
                old_chunks=[]
                found_product_data=None
                
                # Find product data from retrieved data
                if data is not None:
                    logger.info(f"Searching for product {product_id} in retrieved data for company {admin_session.company_id}.")
                    logger.info(f"Retrieved data: {data}")
                    for item in data:
                        logger.info(f"Product id retrieved from MongoDB: {item['product_id']} and chunk length: {item['chunk_length']}")

                        if item["product_id"]==product_id:
                            old_chunk_length= item['chunk_length']
                            old_chunks= item['chunks']
                            found_product_data=item
                            break
                
                # Validate found_product_data exists before proceeding
                if found_product_data is None:
                    logger.warning(f"Product {product_id} listed in retrieved_product_ids but data not found in MongoDB. Skipping update.")
                    continue
                
                bm25_index= create_bm25_index_v2(found_product_data['bm25_index_variables'])
                chunks=[]
                for item in product_based_chunks:
                    if item["product_id"]==product_id and item["company_id"]==admin_session.company_id:
                        chunks= item["chunks_with_file_name"]
                        break
                admin_session.retrieved_chunk_length= found_product_data['chunk_length']

                chunk_texts = []
                for entry in chunks:
                    chunk_texts.extend(entry['chunks'])

                bm25_index= new_create_BM25Okapi_without_corpus_index(chunk_texts, bm25_index)
                variable_list= bm25_index.return_variables()
                chunks= old_chunks + chunks
                admin_session.product_variable_list.append({
                    "product_id": product_id,
                    "variables": variable_list,
                    "chunk_length": len(chunk_texts),
                    "old_chunk_length": old_chunk_length,
                    "chunks": chunks,
                    "old_chunks": old_chunks
                })
                bm25_index=None
                variable_list=None
                

        # Handle company-wide "X" index - check data is not None before accessing

        logger.info(f"Handling company-wide 'X' BM25 index for company {admin_session.company_id}.")
        if data is not None and any(item["product_id"]=="X" for item in data):
            logger.info(f"Found existing company-wide 'X' BM25 index for company {admin_session.company_id}. Updating it.")
            found_product_data = None
            old_chunk_length=0
            old_chunks=[]
            for item in data:
                if item["product_id"] == "X":
                    found_product_data = item
                    old_chunk_length= item['chunk_length']
                    old_chunks= item['chunks']
                    break
            
            chunks=[]
            for val in all_chunks:
                chunks.extend(val['chunks'])
            bm25_index= create_bm25_index_v2(found_product_data['bm25_index_variables'])
            admin_session.retrieved_chunk_length= found_product_data['chunk_length']
            bm25_index= new_create_BM25Okapi_without_corpus_index(chunks, bm25_index)
            variable_list= bm25_index.return_variables()
            admin_session.product_variable_list.append({
                "product_id": "X",
                "variables": variable_list,
                "chunk_length": len(chunks),
                "old_chunk_length": old_chunk_length,
                "chunks": all_chunks,
                "old_chunks": old_chunks  
            })
            bm25_index=None
            variable_list=None
        elif data is None or not any(item["product_id"]=="X" for item in data):
            logger.info(f"No existing company-wide 'X' BM25 index for company {admin_session.company_id}. Creating new one.")
            if all_chunks:  # Only create if we have chunks
                chunks=[]
                for val in all_chunks:
                    chunks.extend(val['chunks'])

                bm25_index=create_bm25_index(chunks)
                variable_list= bm25_index.return_variables()
                admin_session.product_variable_list.append({
                    "product_id": "X",
                    "variables": variable_list,
                    "chunk_length": len(chunks),
                    "old_chunk_length":0,
                    "chunks": all_chunks,
                    "old_chunks": []
                })
                bm25_index=None
                variable_list=None

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

        return {"message": "Chunking completed successfully",
                "company_id":admin_session.company_id,
                "variable_list": admin_session.product_variable_list,
                "total_chunks": len(all_chunks)}

    

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
        for product_data in admin_session.product_variable_list:
            product_id= product_data["product_id"]
            chunks_texts=[]
            for item in product_data["chunks"]:
                chunks_texts= item['chunks']
                logger.info(f"Vectorizing {len(chunks_texts)} chunks for product {product_id} and filename {item['file_name']}.")
                generated_vectors=embedding_model.embed_documents(item['chunks'] )
                logger.info(f"Number of vectors generated for product {product_id} and filename {item['file_name']}: {len(generated_vectors)}")
                admin_session.vectors.append({
                    "product_id": product_id,
                    "file_name": item['file_name'],
                    "vectors": generated_vectors
                })

        embedding_time = time.time() - start_time
        logger.info(f"Embedding Time: {embedding_time:.2f} seconds")
        # return admin_session.vectors
    except Exception as e:
        logger.error(f"Embedding failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Embedding failed:{str(e)}")

    vectorizing_time = time.time() - start_time
    logger.info(f"Vectorizing completed in {vectorizing_time:.2f} seconds.")


@app.post("/store")
async def store(admin_id: str,
                admin_session: AdminSession = Depends(get_admin_session)):
    start_time=time.time()
    try:
        """
        Here first we have to check whether the bm25_index for the given product_id is already present in mongodb or not.
        then accordingly we have to either create a new entry or update the existing entry.
        After that we have to store the vectors in pinecone with proper metadata.


        store_bm25_index_and_chunks_in_mongodb_for_specific_product will accept bm25_index_variables and chunks for every product separately.
        chunks will be passed like this: {index: int ,file_name: str, chunks: List[str] }
        """

        """
        At first store the vectors for every products in this format: {"filename":filename, "vectors":vectors}
        """
        vector_formatted=[]
        for item in admin_session.vectors:
            product_id= item["product_id"]
            if product_id not in [entry['product_id'] for entry in vector_formatted]:
                vector_formatted.append({
                    "product_id": product_id,
                    "vectors_with_filename": [{
                        "file_name": item["file_name"],
                        "vectors": item["vectors"]
                    }]
                })
            else:
                for entry in vector_formatted:
                    if entry['product_id'] == product_id:
                        entry['vectors_with_filename'].append({
                            "file_name": item["file_name"],
                            "vectors": item["vectors"]
                        })
                        break




        for product_data in admin_session.product_variable_list:
            product_id= product_data["product_id"]
            vectors=[]
            ids=[]
            metadata_list=[]
            product_namespace= f"{admin_session.company_id}_{product_id}"
            k=1
            for entry in vector_formatted:
                if entry["product_id"]==product_id:
                    for vector_data in entry["vectors_with_filename"]:
                        if product_id=="X":
                            logger.info(f"Storing vectors for company-wide 'X' namespace for company {admin_session.company_id} using filename {vector_data['file_name']}.")
                        vectors.extend( vector_data["vectors"])
                        ids.extend( [str(i+product_data["old_chunk_length"]+k) for i in range(len(vector_data["vectors"]))])
                        k+= len(vector_data["vectors"])
                        metadata_list.extend( [{
                            "file_name": vector_data["file_name"], 
                            "product_id": product_id, 
                            "company_id": admin_session.company_id
                            } for _ in range(len(vector_data["vectors"]))])
                    break
            logger.info(f"here's the ids for product{product_id}:{ids}")


            # for vector_data in admin_session.vectors:
            #     if vector_data["product_id"]==product_id:
            #         if product_id=="X":
            #             logger.info(f"Storing vectors for company-wide 'X' namespace for company {admin_session.company_id} using filename {vector_data['file_name']}.")
            #         vectors= vector_data["vectors"]
            #         ids= [str(i+product_data["old_chunk_length"]) for i in range(len(vectors))]
            #         metadata_list= [{
            #             "file_name": vector_data["file_name"], 
            #             "product_id": product_id, 
            #             "company_id": admin_session.company_id
            #             } for _ in range(len(vectors))]
            #         break
            
            """
            In retrieved_product_ids we have the list of product ids for which bm25 index already exists in mongodb.
            So here we are checking whether the current product_id exists in that list or not.
            """
            product_exists= False
            if product_data["old_chunk_length"]>0:
                product_exists= True
                sent_chunks=[]
                i=product_data["old_chunk_length"]
                chunk_length=product_data["chunk_length"]
                chunk_with_index= []
                for chunk in product_data["chunks"]:
                    for text in chunk['chunks']:
                        i+=1
                        chunk_with_index.append((i, text))

                for item in product_data["chunks"]:
                    i+=1
                    sent_chunks.append({
                        "file_name": item['file_name'],
                        "chunks": chunk_with_index
                    })
                final_chunks= sent_chunks
                final_chunk_length= product_data["old_chunk_length"] + chunk_length
                update_bm25_index_and_chunks_in_mongodb(
                    bm25_index_variables=product_data["variables"],
                    new_chunks=final_chunks,
                    company_id=admin_session.company_id,
                    product_id=product_id,
                    chunk_length=final_chunk_length
                )
                logger.info(f"BM25 index and chunks updated in MongoDB for company {admin_session.company_id} for product {product_id}.")

            else:
                product_exists= False
                sent_chunks=[]
                i=0
                chunk_length=product_data["chunk_length"]
                chunk_with_index= []
                for chunk in product_data["chunks"]:
                    for text in chunk['chunks']:
                        i+=1
                        chunk_with_index.append((i, text))


                for item in product_data["chunks"]:
                    i+=1
                    sent_chunks.append({
                        "file_name": item['file_name'],
                        "chunks": chunk_with_index
                    })
                store_bm25_index_and_chunks_in_mongodb_for_specific_product(
                    bm25_index_variables=product_data["variables"],
                    chunks=sent_chunks,
                    company_id=admin_session.company_id,
                    product_id=product_id,
                    chunk_length= chunk_length
                )
                logger.info(f"BM25 index and chunks stored in MongoDB for company {admin_session.company_id} for product {product_id}.")
            
            # Now sending vectors to pinecone
            
            await sending_to_pinecone(stats=stats, index=Pinecone_index, vectors=vectors, ids=ids, metadata_list=metadata_list, namespace=product_namespace)
            logger.info(f"Vectors stored in Pinecone for company {admin_session.company_id} and product {product_id}.")


            # flush all admin_session data after storing
        admin_session.chunks_list = []
        admin_session.vectors = []
        admin_session.parsed_contents_list = []
        admin_session.product_variable_list = []
        admin_session.all_variable_list = []
        admin_session.created_or_not = False
        admin_session.retrieved_chunk_length = 0

    except Exception as e:
        logger.error(f"Storing failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Storing failed:{str(e)}")
        
    
    vector_storing_time = time.time() - start_time
    logger.info(f"Vector Storing Time: {vector_storing_time:.2f} seconds")

    


#hosting on localhost
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)