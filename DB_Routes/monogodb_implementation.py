from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import datetime
import ssl
import certifi


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
database= client['Dotlines']
collection= database['BM25_index']
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")

    collection.find_one()
except Exception as e:
    print(e)


def store_bm25_index_and_chunks_in_mongodb(bm25_index_variables, chunks, namespace):
    bm25_data = {
        'timestamp':  datetime.datetime.now(),
        "namespace": namespace,
        "bm25_index_variables": bm25_index_variables,
        "chunk_length": len(chunks),
        "chunks": [(i, chunks[i]) for i in range(len(chunks))]
    }
    collection.insert_one(bm25_data)
    print("BM25 index and chunks stored in MongoDB.")

def retrieve_bm25_index_and_chunks_using_namespace(namespace):
    data = collection.find_one({'namespace': namespace})
    return data


def retrieve_all():
    return collection.find()


def update_bm25_index_and_chunks_in_mongodb(bm25_index_variables, new_chunks, namespace):
    update_data = {
        'timestamp':  datetime.datetime.now(),
        "bm25_index_variables": bm25_index_variables,
        'chunk_length': len(new_chunks),
        "chunks": [(i, new_chunks[i]) for i in range(len(new_chunks))]
    }
    collection.update_one({'namespace': namespace}, {'$set': update_data})
    print("BM25 index and chunks updated in MongoDB.")

def retrieve_chunks_from_mongodb(namespace, index_list):
    data = collection.find_one({'namespace': namespace})
    all_chunks = data['chunks']
    selected_chunks = [all_chunks[i][1] for i in index_list]
    return selected_chunks