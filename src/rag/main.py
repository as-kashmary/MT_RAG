import argparse
import time
import json
import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from document_loader import read_txt_to_string
from semantic_chunker import SemanticChunking
# from embeder import HFInferenceEmbeddings
from vector_store import sending_to_pinecone, retrieve_namespace, query_pinecone
from query_classifier import QueryClassifier
from fusion_retrieval import fusion
import numpy as np
from response_generation import ResponseGenerator

from local_embeder import LocalEmbeddings


HF_TOKEN="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"

def parse_args():
    parser = argparse.ArgumentParser(
        description="This is a whole RAG pipleine")
    parser.add_argument("--path", type=str, default="documents/texts.txt",
                        help="Path to the PDF file to encode.")
    parser.add_argument("--namespace", type=str, default="default",
                        help="Namespace in Pinecone to store/already stored the vectors.")
    return parser.parse_args()
    


def query_classifier_main(query, elapsed_time):
    query_classifier=QueryClassifier(query)
    query_class=query_classifier.classification()
    # print(f"Query Classification from function: {query_class}")
    query_classification_time = time.time() - elapsed_time
    # print(f"Query Classification Time: {query_classification_time:.2f} seconds. Total elapsed time: {elapsed_time + query_classification_time:.2f} seconds")
    return query_class, query_classification_time




def chunking_and_embedding(content, embedding_model, namespace, start_time, path):
    content = read_txt_to_string(path)
    document_reading_time = time.time() - start_time
    print(f"Document Reading Time: {document_reading_time:.2f} seconds. Total elapsed time: {time.time() - start_time:.2f} seconds")

    chunks=SemanticChunking(content, embedding_model)
    print(f"Number of chunks: {len(chunks.get_chunks())}")
    document_list=chunks.get_chunks()
    semnantic_chunking_time = time.time() - start_time - document_reading_time
    print(f"Semantic Chunking Time: {semnantic_chunking_time:.2f} seconds. Total elapsed time: {time.time() - start_time:.2f} seconds")

    vectors = embedding_model.embed_documents(chunks.get_chunks())
    print(f"Number of vectors: {len(vectors)}")
    embedding_time = time.time() - start_time - document_reading_time - semnantic_chunking_time
    print(f"Embedding Time: {embedding_time:.2f} seconds. Total elapsed time: {time.time() - start_time:.2f} seconds")

    ids = [str(i) for i in range(len(vectors))]
    metadata_list = [{"text": chunk} for chunk in chunks.get_chunks()]
    sending_to_pinecone(vectors=vectors, ids=ids, metadata_list=metadata_list, namespace=namespace)
    vector_storing_time = time.time() - start_time - document_reading_time - semnantic_chunking_time - embedding_time
    print(f"Vector Storing Time: {vector_storing_time:.2f} seconds. Total elapsed time: {time.time() - start_time:.2f} seconds")

    elapsed_time = time.time() - start_time
    return elapsed_time, document_list



def retrieval_and_fusion(document_list,embedding_model, query, namespace):
    # results= query_pinecone(query, namespace=namespace, top_k=5)
    # print(f"Vector search returned {len(results['matches'])} matches.")
    # print("Top 5 Fusion Retrieval Results:")
    # for i, doc in enumerate(results):
    #     print(f"Result {i+1}, Score: {doc[1]}: {doc[0]}")

    results = fusion(document_list=document_list,embedding_model=embedding_model, query=query, namespace=namespace)
    return results


def main(args):
    start_time = time.time()
    # embeddings = HFInferenceEmbeddings(
    #     model="intfloat/multilingual-e5-large-instruct",
    #     api_key=HF_TOKEN
    # )
    embedding_model= LocalEmbeddings("./models/multilingual-e5-large-instruct")
    embedding_model._load_model()
    print(f"Using embedding model from local path: ./models/multilingual-e5-large-instruct")

    path = args.path
    namespace= args.namespace
    # namespace= "default-namespace"
    doc_list_path = f"{namespace}_document_list.json"
    if retrieve_namespace(namespace):
        print(f"Namespace '{namespace}' already exists in Pinecone.")
        document_list = []
        try:
            with open(doc_list_path, 'r') as f:
                document_list = json.load(f)
            print(f"Loaded document list from {doc_list_path}")
        except FileNotFoundError:
            print(f"Warning: Document list file '{doc_list_path}' not found. Retrieval might fail.")
        query=input("Enter your query for classification: ")
        elapsed_time=time.time() - start_time
        query_class, query_classification_time= query_classifier_main(query, elapsed_time)
        print(f"Query Classification: {query_class}")
        print(f"Query classification Time: {query_classification_time:.2f} seconds. Total elapsed time: {time.time() - start_time:.2f} seconds")


        
    else:
        print(f"Namespace '{namespace}' does not exist. It will be created when storing vectors.")
        namespace= args.namespace
        elapsed_time,document_list=chunking_and_embedding(path, embedding_model, namespace, start_time, path)

        with open(doc_list_path, 'w') as f:
            json.dump(document_list, f)
        query=input("Enter your query for classification: ")
        query_class, query_classification_time= query_classifier_main(query, elapsed_time)
        print(f"Saved document list to {doc_list_path}")
        print(f"Query Classification: {query_class}")


    results= retrieval_and_fusion(document_list,embedding_model, query, namespace)
    # print("Top 5 Fusion Retrieval Results:")
    # for i, doc in enumerate(results):
    #     print(f"Result {i+1}: {doc}")
    context=results[0]
    print(f"Context: {context}")
    generator= ResponseGenerator(query, context)
    response= generator.generation()
    print("--------------------------------------------------")
    print(f"Generated Response: {response}")





if __name__ == "__main__":
    args=parse_args()
    main(args)
    
