from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import datetime
import ssl
import certifi

from src.logging.logging import get_logger
logger= get_logger("mongodb_implementation")


user="ahhask4127_db_user"
password="56lqIaZoyLWvE3l8"
cluster="cluster.n9fywsv.mongodb.net"
appname="Cluster"


uri = f"mongodb+srv://{user}:{password}@{cluster}/?appName={appname}"

# Create a new client and connect to the server
client = MongoClient(
    uri,
    server_api=ServerApi('1'),
    # tls=True,
    # tlsAllowInvalidCertificates=False,
    # tlsCAFile=certifi.where()
)
database= client['retrieval_DB']
collection= database['Chunks']
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    logger.info("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    logger.error(f"Error connecting to MongoDB: {str(e)}")


def store_bm25_index_and_chunks_in_mongodb_for_specific_product(bm25_index_variables, chunks, company_id, product_id, chunk_length):
    try:
        """
        if the chunks and bm25_index_variables is for the whole company then product_id is "X"
        else it is for a specific product
        """
        """
        here chunks will be:
        {
            "file_name": item['file_name'],
            "chunks": [
                [
                    "index": i,
                    "chunk": chunk_text
                ],
                ...
            ]
        }
        """

        bm25_data = {
            'timestamp':  datetime.datetime.now(),
            "company_id": company_id,
            "product_id": product_id,
            "bm25_index_variables": bm25_index_variables,
            "chunk_length": chunk_length,
            "chunks": chunks
        }
        collection.insert_one(bm25_data)
        logger.info("BM25 index and chunks stored in MongoDB.")
    except Exception as e:
        logger.error(f"Error storing BM25 index and chunks in MongoDB: {str(e)}")



def retrieve_bm25_index_and_chunks_using_company(company_id):
    try:
        """
        collection.find returns a MongoDB Cursor, not a list. 
        A cursor is lazy and iterable, but when you iterate over it multiple times, 
        the cursor gets exhausted after the first iteration.
        That's why in the calling function we have to convert it to a list.
        """
        data = list(collection.find({'company_id': company_id}))
        logger.info(f"Retrieved BM25 index and chunks for company {company_id}")
        return data if data else None
    except Exception as e:
        logger.error(f"Error retrieving BM25 index and chunks from MongoDB: {str(e)}")
        return None
        



def retrieve_bm25_index_and_chunks_using_company_and_product(company_id, product_id):
    try:
        """
        collection.find returns a MongoDB Cursor, not a list. 
        A cursor is lazy and iterable, but when you iterate over it multiple times, 
        the cursor gets exhausted after the first iteration.
        That's why in the calling function we have to convert it to a list.
        """
        data = list(collection.find({'company_id': company_id, 'product_id': product_id}))
        logger.info(f"Retrieved BM25 index and chunks for company {company_id} and product {product_id}")
        return data if data else None
    except Exception as e:
        logger.error(f"Error retrieving BM25 index and chunks from MongoDB: {str(e)}")
        return None


def update_bm25_index_and_chunks_in_mongodb(bm25_index_variables, new_chunks, company_id, product_id, chunk_length):
    try:
        # data =retrieve_bm25_index_and_chunks_using_company_and_product(company_id, product_id)
        """
        here chunks will be:
        {
            
            "file_name": item['file_name'],
            "chunks": item['chunks']
        }
        """

        update_data = {
            'timestamp':  datetime.datetime.now(),
            "company_id": company_id,
            "product_id": product_id,
            "bm25_index_variables": bm25_index_variables,
            "chunk_length": chunk_length,
            "chunks": new_chunks
        }
        collection.update_one({'company_id': company_id, 'product_id': product_id}, {'$set': update_data})
        logger.info("BM25 index and chunks updated in MongoDB.")
    except Exception as e:
        logger.error(f"Error updating BM25 index and chunks in MongoDB: {str(e)}")


def retrieve_chunks_from_mongodb(namespace, index_list):
    try:
        data = collection.find_one({'namespace': namespace})
        all_chunks = data['chunks']
        selected_chunks = [all_chunks[i][1] for i in index_list]
        logger.info(f"Retrieved selected chunks for namespace {namespace}")
        return selected_chunks
    except Exception as e:
        logger.error(f"Error retrieving chunks from MongoDB: {str(e)}")
        return None