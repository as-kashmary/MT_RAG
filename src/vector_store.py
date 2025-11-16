from pinecone import Pinecone
from src.embeder import HFInferenceEmbeddings

HF_TOKEN="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"

pc = Pinecone(api_key="pcsk_2ht9Mg_9VwrnZM7wQrAiCkEfUTQFLDsPui6p9VxkcKbCPvKsVSUaR9jZwmeQwwuUpbpGJv")

index = pc.Index(host="https://test-11ejuti.svc.aped-4627-b74a.pinecone.io")

embeddings = HFInferenceEmbeddings(
    model="intfloat/multilingual-e5-large-instruct",
    api_key=HF_TOKEN
)


# print(index.describe_index_stats())
stats=index.describe_index_stats()


def retrieve_namespace(namespace):
    if stats["namespaces"].get(namespace) is None:
        return False
    else:
        return True


def sending_to_pinecone(vectors, ids, metadata_list, namespace):
    if stats["namespaces"].get(namespace) is None:
        # index.create_namespace(namespace)

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



def query_pinecone(query,namespace, top_k=3):
    query_vector = embeddings.embed_query(query)
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
    for i in results['matches']:
        # print(f"ID: {i['id']}, Score: {i['score']}, Metadata: {i['metadata']['text']}")
        retrieved_chunks.append((i['metadata']['text'], i['score']))
    return retrieved_chunks