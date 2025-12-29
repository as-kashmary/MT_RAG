from pinecone import Pinecone
from src.logging.logging import get_logger

logger= get_logger("vector_store")


async def retrieve_namespace(stats, namespace)-> bool:
    try:
        if stats["namespaces"].get(namespace) is None:
            return False
        else:
            return True
    except Exception as e:
        logger.error(f"Pinecone connection failed:{str(e)}")
        raise Exception(f"Pinecone connection failed:{str(e)}")
    

async def retrieve_length_of_namespace(stats, namespace)-> int:
    try:
        if stats["namespaces"].get(namespace) is None:
            return 0
        else:
            return stats["namespaces"][namespace]["vector_count"]
    except Exception as e:
        logger.error(f"Pinecone connection failed:{str(e)}")
        raise Exception(f"Pinecone connection failed:{str(e)}")
    


async def sending_to_pinecone(stats, index, vectors, ids, metadata_list, namespace)-> None:
    try:
        """
        Have to resolve the id collision issue in the future.
        """


        to_upsert = []
        for i in range(len(vectors)):
            to_upsert.append({
                "id": ids[i],
                "values": vectors[i],
                "metadata": metadata_list[i]
            })
        index.upsert(
            vectors=to_upsert,
            namespace=namespace
        )
        logger.info(f"Upserted {len(vectors)} vectors to Pinecone in namespace '{namespace}'.")
        return None

    except Exception as e:
        logger.error(f"Pinecone connection failed:{str(e)}")
        raise Exception(f"Pinecone connection failed:{str(e)}")
    


async def query_pinecone(stats, index, query: str,namespace:str ,embedding_model: object, top_k)-> list:
    try:

        query_vector = embedding_model.embed_query(query)
        results=index.query(
            namespace=namespace,
            vector=query_vector, 
            top_k=top_k,
            include_metadata=True,
            include_values=False
        )
        retrieved_chunks=[]
        logger.info(f"Pinecone query results: {results}")
        # Sort the results[matches] according to i['id']. Sort will be done considering the 'id' as integer
        results['matches'].sort(key=lambda x: int(x['id']))
        

        for i in results['matches']:
            retrieved_chunks.append((i['metadata']['text'], i['score']))
        logger.info(f"Queried Pinecone in namespace '{namespace}' with query '{query}'. Retrieved {len(retrieved_chunks)} chunks.")
        return retrieved_chunks
    except Exception as e:
        logger.error(f"Pinecone connection failed:{str(e)}")
        raise Exception(f"Pinecone connection failed:{str(e)}")
        

