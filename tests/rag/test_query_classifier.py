"""
Tests for query_classifier.py - Query Classification with LLM.

This module tests:
- QueryClassifier class initialization
- classification: Classify query into categories
"""
import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, PROJECT_ROOT)


class TestQueryClassifier:
    """Tests for the QueryClassifier class."""
    
    @patch('src.rag.query_classifier.Client')
    def test_initialization_factual(self, mock_client):
        """Test QueryClassifier initialization with factual query."""
        # Setup mock streaming response
        mock_client_instance = MagicMock()
        
        def mock_chat(*args, **kwargs):
            yield {'message': {'content': 'Factual'}}
        
        mock_client_instance.chat = mock_chat
        mock_client.return_value = mock_client_instance
        
        from src.rag.query_classifier import QueryClassifier
        
        classifier = QueryClassifier("What is the capital of France?")
        
        assert classifier.query == "What is the capital of France?"
        assert classifier.response == "Factual"
    
    @patch('src.rag.query_classifier.Client')
    def test_initialization_analytical(self, mock_client):
        """Test QueryClassifier with analytical query."""
        mock_client_instance = MagicMock()
        
        def mock_chat(*args, **kwargs):
            yield {'message': {'content': 'Analytical'}}
        
        mock_client_instance.chat = mock_chat
        mock_client.return_value = mock_client_instance
        
        from src.rag.query_classifier import QueryClassifier
        
        classifier = QueryClassifier("Why do prices increase during inflation?")
        
        assert classifier.response == "Analytical"
    
    @patch('src.rag.query_classifier.Client')
    def test_initialization_opinion(self, mock_client):
        """Test QueryClassifier with opinion query."""
        mock_client_instance = MagicMock()
        
        def mock_chat(*args, **kwargs):
            yield {'message': {'content': 'Opinion'}}
        
        mock_client_instance.chat = mock_chat
        mock_client.return_value = mock_client_instance
        
        from src.rag.query_classifier import QueryClassifier
        
        classifier = QueryClassifier("What is the best programming language?")
        
        assert classifier.response == "Opinion"
    
    @patch('src.rag.query_classifier.Client')
    def test_initialization_contextual(self, mock_client):
        """Test QueryClassifier with contextual query."""
        mock_client_instance = MagicMock()
        
        def mock_chat(*args, **kwargs):
            yield {'message': {'content': 'Contextual'}}
        
        mock_client_instance.chat = mock_chat
        mock_client.return_value = mock_client_instance
        
        from src.rag.query_classifier import QueryClassifier
        
        classifier = QueryClassifier("Based on the document, what are the main points?")
        
        assert classifier.response == "Contextual"
    
    @patch('src.rag.query_classifier.Client')
    def test_classification_method(self, mock_client):
        """Test the classification method returns classified type."""
        mock_client_instance = MagicMock()
        
        def mock_chat(*args, **kwargs):
            yield {'message': {'content': 'Factual'}}
        
        mock_client_instance.chat = mock_chat
        mock_client.return_value = mock_client_instance
        
        from src.rag.query_classifier import QueryClassifier
        
        classifier = QueryClassifier("What is 2+2?")
        result = classifier.classification()
        
        assert result == "Factual"
        assert isinstance(result, str)
    
    @patch('src.rag.query_classifier.Client')
    def test_streaming_response_accumulation(self, mock_client):
        """Test that streaming response is accumulated correctly."""
        mock_client_instance = MagicMock()
        
        # Simulate chunked streaming response
        def mock_chat(*args, **kwargs):
            yield {'message': {'content': 'Fact'}}
            yield {'message': {'content': 'ual'}}
        
        mock_client_instance.chat = mock_chat
        mock_client.return_value = mock_client_instance
        
        from src.rag.query_classifier import QueryClassifier
        
        classifier = QueryClassifier("Test query")
        
        assert classifier.response == "Factual"
    
    @patch('src.rag.query_classifier.Client')
    def test_response_stripped(self, mock_client):
        """Test that response whitespace is stripped."""
        mock_client_instance = MagicMock()
        
        def mock_chat(*args, **kwargs):
            yield {'message': {'content': '  Factual  \n'}}
        
        mock_client_instance.chat = mock_chat
        mock_client.return_value = mock_client_instance
        
        from src.rag.query_classifier import QueryClassifier
        
        classifier = QueryClassifier("Test query")
        
        assert classifier.response == "Factual"
    
    @patch('src.rag.query_classifier.Client')
    def test_client_initialization(self, mock_client):
        """Test that Ollama client is initialized with correct parameters."""
        mock_client_instance = MagicMock()
        
        def mock_chat(*args, **kwargs):
            yield {'message': {'content': 'Factual'}}
        
        mock_client_instance.chat = mock_chat
        mock_client.return_value = mock_client_instance
        
        from src.rag.query_classifier import QueryClassifier
        
        classifier = QueryClassifier("Test")
        
        # Verify client was created with host parameter
        mock_client.assert_called_once()
        call_kwargs = mock_client.call_args[1]
        assert 'host' in call_kwargs
        assert 'headers' in call_kwargs


class TestQueryClassifierPrompt:
    """Tests for query classifier prompt construction."""
    
    @patch('src.rag.query_classifier.Client')
    def test_prompt_contains_query(self, mock_client):
        """Test that the prompt includes the user query."""
        mock_client_instance = MagicMock()
        captured_messages = []
        
        def mock_chat(model, messages, **kwargs):
            captured_messages.append(messages)
            yield {'message': {'content': 'Factual'}}
        
        mock_client_instance.chat = mock_chat
        mock_client.return_value = mock_client_instance
        
        from src.rag.query_classifier import QueryClassifier
        
        test_query = "What is machine learning?"
        classifier = QueryClassifier(test_query)
        
        # Check that the query is in the prompt
        assert len(captured_messages) == 1
        prompt_content = captured_messages[0][0]['content']
        assert test_query in prompt_content
    
    @patch('src.rag.query_classifier.Client')
    def test_prompt_contains_categories(self, mock_client):
        """Test that prompt mentions all classification categories."""
        mock_client_instance = MagicMock()
        captured_messages = []
        
        def mock_chat(model, messages, **kwargs):
            captured_messages.append(messages)
            yield {'message': {'content': 'Factual'}}
        
        mock_client_instance.chat = mock_chat
        mock_client.return_value = mock_client_instance
        
        from src.rag.query_classifier import QueryClassifier
        
        classifier = QueryClassifier("Test query")
        
        prompt_content = captured_messages[0][0]['content']
        
        # All categories should be mentioned in the prompt
        assert 'Factual' in prompt_content
        assert 'Analytical' in prompt_content
        assert 'Opinion' in prompt_content
        assert 'Contextual' in prompt_content


class TestQueryClassifierEdgeCases:
    """Edge case tests for QueryClassifier."""
    
    @patch('src.rag.query_classifier.Client')
    def test_empty_query(self, mock_client):
        """Test handling of empty query."""
        mock_client_instance = MagicMock()
        
        def mock_chat(*args, **kwargs):
            yield {'message': {'content': 'Contextual'}}
        
        mock_client_instance.chat = mock_chat
        mock_client.return_value = mock_client_instance
        
        from src.rag.query_classifier import QueryClassifier
        
        classifier = QueryClassifier("")
        
        assert classifier.query == ""
        assert classifier.response is not None
    
    @patch('src.rag.query_classifier.Client')
    def test_unicode_query(self, mock_client):
        """Test handling of unicode characters in query."""
        mock_client_instance = MagicMock()
        
        def mock_chat(*args, **kwargs):
            yield {'message': {'content': 'Factual'}}
        
        mock_client_instance.chat = mock_chat
        mock_client.return_value = mock_client_instance
        
        from src.rag.query_classifier import QueryClassifier
        
        unicode_query = "日本の首都は何ですか？"  # "What is the capital of Japan?" in Japanese
        classifier = QueryClassifier(unicode_query)
        
        assert classifier.query == unicode_query
        assert classifier.response == "Factual"
    
    @patch('src.rag.query_classifier.Client')
    def test_long_query(self, mock_client):
        """Test handling of very long query."""
        mock_client_instance = MagicMock()
        
        def mock_chat(*args, **kwargs):
            yield {'message': {'content': 'Analytical'}}
        
        mock_client_instance.chat = mock_chat
        mock_client.return_value = mock_client_instance
        
        from src.rag.query_classifier import QueryClassifier
        
        long_query = "This is a very long query. " * 100
        classifier = QueryClassifier(long_query)
        
        assert len(classifier.query) > 1000
        assert classifier.response == "Analytical"
