import time
from langchain_community.document_loaders import TextLoader,PyPDFLoader, Docx2txtLoader
import chardet
import json


def determine_encoding(path):
    with open(path, "rb") as f:
        raw = f.read()
    enc = chardet.detect(raw)['encoding']
    return enc


def read_txt_to_string(path):
    """
    Reads a PDF file and returns its content as a string.

    Args:
        path (str): Path to the PDF file.

    Returns:
        str: The content of the PDF file as a string.
    """
    encoding_type = determine_encoding(path)
    print(f"Determined encoding: {encoding_type}")

    loader = TextLoader(path, encoding=encoding_type)
    documents = loader.load()
    return documents[0].page_content

def read_pdf_to_string(path):
    """
    Reads a PDF file and returns its content as a string.

    Args:
        path (str): Path to the PDF file.

    Returns:
        str: The content of the PDF file as a string.
    """

    loader = PyPDFLoader(path)
    documents = loader.load()
    print(documents)
    page_contents=[doc.page_content for doc in documents]

    with open("text.txt", 'w', encoding="utf-8") as f:
        for i in page_contents:
            f.write(i)


    print(f"Loaded {len(page_contents)} documents from {path}.")
    page_content=""
    for i in page_contents:
        page_content+=i+'\n'

    return page_content

def read_docx_to_string(path):
    """
    Reads a DOCX file and returns its content as a string.

    Args:
        path (str): Path to the DOCX file.

    Returns:
        str: The content of the DOCX file as a string.
    """

    loader = Docx2txtLoader(path)

    data = loader.load()

    return data[0].page_content


"""
We will integrate more document loaders using API from unstructured.io in the future.
Future goals: ppt, html, csv, images, videos, audio etc.
"""