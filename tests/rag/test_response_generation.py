"""
Tests for response_generation.py - LLM Response Generation.
"""
import pytest
from unittest.mock import MagicMock, patch
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, PROJECT_ROOT)


class TestResponseGenerator:
    """Tests for the ResponseGenerator class."""
    
    @patch('src.rag.response_generation.Client')
    def test_initialization(self, mock_client):
        """Test ResponseGenerator initialization."""
        mock_client_instance = MagicMock()
        def mock_chat(*args, **kwargs):
            yield {'message': {'content': 'Generated response.'}}
        mock_client_instance.chat = mock_chat
        mock_client.return_value = mock_client_instance
        
        from src.rag.response_generation import ResponseGenerator
        
        generator = ResponseGenerator(query="What is AI?", context="AI is artificial intelligence.")
        
        assert generator.query == "What is AI?"
        assert generator.context == "AI is artificial intelligence."
        assert generator.response == "Generated response."
    
    @patch('src.rag.response_generation.Client')
    def test_generation_method(self, mock_client):
        """Test the generation method returns response."""
        mock_client_instance = MagicMock()
        def mock_chat(*args, **kwargs):
            yield {'message': {'content': 'Detailed answer.'}}
        mock_client_instance.chat = mock_chat
        mock_client.return_value = mock_client_instance
        
        from src.rag.response_generation import ResponseGenerator
        
        generator = ResponseGenerator(query="What is AI?", context="AI context.")
        result = generator.generation()
        
        assert result == "Detailed answer."
        assert isinstance(result, str)
    
    @patch('src.rag.response_generation.Client')
    def test_streaming_accumulation(self, mock_client):
        """Test streaming response accumulation."""
        mock_client_instance = MagicMock()
        def mock_chat(*args, **kwargs):
            yield {'message': {'content': 'First '}}
            yield {'message': {'content': 'Second.'}}
        mock_client_instance.chat = mock_chat
        mock_client.return_value = mock_client_instance
        
        from src.rag.response_generation import ResponseGenerator
        
        generator = ResponseGenerator(query="Test", context="Context")
        assert generator.response == "First Second."
    
    @patch('src.rag.response_generation.Client')
    def test_response_stripped(self, mock_client):
        """Test response whitespace is stripped."""
        mock_client_instance = MagicMock()
        def mock_chat(*args, **kwargs):
            yield {'message': {'content': '  Response  \n  '}}
        mock_client_instance.chat = mock_chat
        mock_client.return_value = mock_client_instance
        
        from src.rag.response_generation import ResponseGenerator
        
        generator = ResponseGenerator(query="Test", context="Context")
        assert generator.response == "Response"
    
    @patch('src.rag.response_generation.Client')
    def test_prompt_contains_query_and_context(self, mock_client):
        """Test prompt includes query and context."""
        mock_client_instance = MagicMock()
        captured_messages = []
        def mock_chat(model, messages, **kwargs):
            captured_messages.append(messages)
            yield {'message': {'content': 'Response'}}
        mock_client_instance.chat = mock_chat
        mock_client.return_value = mock_client_instance
        
        from src.rag.response_generation import ResponseGenerator
        
        generator = ResponseGenerator(query="What is ML?", context="ML is machine learning.")
        
        prompt_content = captured_messages[0][0]['content']
        assert "What is ML?" in prompt_content
        assert "ML is machine learning." in prompt_content
    
    @patch('src.rag.response_generation.Client')
    def test_long_context(self, mock_client):
        """Test handling of long context."""
        mock_client_instance = MagicMock()
        def mock_chat(*args, **kwargs):
            yield {'message': {'content': 'Summary.'}}
        mock_client_instance.chat = mock_chat
        mock_client.return_value = mock_client_instance
        
        from src.rag.response_generation import ResponseGenerator
        
        long_context = "Paragraph. " * 500
        generator = ResponseGenerator(query="Summarize.", context=long_context)
        
        assert len(generator.context) > 5000
        assert generator.response == "Summary."
    
    @patch('src.rag.response_generation.Client')
    def test_unicode_content(self, mock_client):
        """Test handling of unicode content."""
        mock_client_instance = MagicMock()
        def mock_chat(*args, **kwargs):
            yield {'message': {'content': '日本は島国です。'}}
        mock_client_instance.chat = mock_chat
        mock_client.return_value = mock_client_instance
        
        from src.rag.response_generation import ResponseGenerator
        
        generator = ResponseGenerator(query="日本について", context="日本は東アジアの国")
        assert generator.response == "日本は島国です。"
