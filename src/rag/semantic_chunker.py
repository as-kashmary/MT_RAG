from langchain_experimental.text_splitter import SemanticChunker
# from langchain_experimental.text_splitter.SemanticChunker import *
import time
import os
from typing import Literal

from src.logging.logging import get_logger

logger= get_logger("semantic_chunker")

class SemanticChunking:
    """
    A class to handle the Semantic Chunking process for document chunking.
    """
    def __init__(self, content, embedding_model, breakpoint_type: Literal['percentile', 'standard_deviation', 'interquartile', 'gradient'] = 'percentile',
                 breakpoint_amount=90):
        """
        Initializes the SemanticChunking by encoding the content using a semantic chunker.

        Args:
            content (str): Content of the document to encode.
            embedding_model: embedding_model model to use for vectorization.
            breakpoint_type (BreakpointThresholdType): Type of breakpoint threshold.
            breakpoint_amount (int): Amount for the breakpoint threshold.
        """
        # self.path = path
        self.embedding_model = embedding_model

        # Read the PDF content
        
        self.pdf_content = content
        # self.breakpoint_type = breakpoint_type
        self.breakpoint_amount = breakpoint_amount

        # Initialize the semantic chunker

        semantic_chunker=SemanticChunker(
            embeddings=self.embedding_model,
            buffer_size = 1, 
            add_start_index= False, 
            breakpoint_threshold_type=breakpoint_type, 
            breakpoint_threshold_amount= breakpoint_amount, 
        )

        # Perform semantic chunking
        # start_time = time.time()
        self.semantic_docs = semantic_chunker.split_text(self.pdf_content)
        logger.info(f"Semantic chunking completed. Total chunks created: {len(self.semantic_docs)} . With breakpoint type: {breakpoint_type} and breakpoint amount: {breakpoint_amount}.")
        # self.time_records = {'Chunking': time.time() - start_time}
        # print(f"Semantic Chunking Time: {self.time_records['Chunking']:.2f} seconds")
        
    def get_chunks(self):
        """
        Returns the semantic chunks.

        Returns:
            list: A list of semantic chunks (strings).
        """
        return self.semantic_docs
        