from pinecone import Pinecone


async def retrieve_namespace(stats, namespace)-> bool:
    try:
        if stats["namespaces"].get(namespace) is None:
            return False
        else:
            return True
    except Exception as e:
        raise Exception(f"Pinecone connection failed:{str(e)}")
    

async def retrieve_length_of_namespace(stats, namespace)-> int:
    try:
        if stats["namespaces"].get(namespace) is None:
            return 0
        else:
            return stats["namespaces"][namespace]["vector_count"]
    except Exception as e:
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
        return None

    except Exception as e:
        raise Exception(f"Pinecone connection failed:{str(e)}")
    


async def query_pinecone(stats, index, query: str,namespace:str ,embedding_model: object, top_k)-> list:
    try:

        query_vector = embedding_model.embed_query(query)
        # print(f"Query vector : {query_vector}")
        results=index.query(
            namespace=namespace,
            vector=query_vector, 
            top_k=top_k,
            include_metadata=True,
            include_values=False
        )
        # print(f"Query results: {results}")
        retrieved_chunks=[]
        # Sort the results[matches] according to i['id']
        results['matches'].sort(key=lambda x: x['id'])
        
        for i in results['matches']:
            # print(f"ID: {i['id']}, Score: {i['score']}, Metadata: {i['metadata']['text']}")
            print(f"ID: {i['id']}")
            retrieved_chunks.append((i['metadata']['text'], i['score']))
        return retrieved_chunks
    except Exception as e:
        raise Exception(f"Pinecone connection failed:{str(e)}")
        

