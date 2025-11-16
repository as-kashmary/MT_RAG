import time
from langchain_community.document_loaders import TextLoader



def read_pdf_to_string(path):
    """
    Reads a PDF file and returns its content as a string.

    Args:
        path (str): Path to the PDF file.

    Returns:
        str: The content of the PDF file as a string.
    """
    loader = TextLoader(path)
    documents = loader.load()

    docs= []
    # for doc in documents:
    #     doc.page_content = doc.page_content.replace('\t', ' ') 
    #     docs.append(doc)

    # print(f"Loaded {len(documents)} documents from {path}.")

    return documents[0].page_content