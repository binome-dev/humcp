import os
from unittest.mock import MagicMock, patch

import pytest

from src.tools.search.tavily_tool import TavilySearchTool, tavily_web_search


@pytest.fixture
def mock_tavily_client():
    with patch("src.tools.search.tavily_tool.TavilyClient") as mock:
        yield mock


@pytest.fixture
def mock_env_api_key():
    with patch.dict(os.environ, {"TAVILY_API_KEY": "test-api-key"}):
        yield


class TestTavilySearchTool:
    def test_init(self, mock_tavily_client):
        tool = TavilySearchTool(api_key="test-key", search_depth="advanced", max_tokens=5000)
        mock_tavily_client.assert_called_once_with(api_key="test-key")
        assert tool.search_depth == "advanced"
        assert tool.max_tokens == 5000

    def test_web_search_success(self, mock_tavily_client):
        mock_client = MagicMock()
        mock_client.search.return_value = {
            "answer": "Test answer",
            "results": [
                {
                    "title": "Result 1",
                    "url": "https://example.com/1",
                    "content": "Content 1",
                    "score": 0.95,
                },
                {
                    "title": "Result 2",
                    "url": "https://example.com/2",
                    "content": "Content 2",
                    "score": 0.85,
                },
            ],
        }
        mock_tavily_client.return_value = mock_client

        tool = TavilySearchTool(api_key="test-key")
        result = tool.web_search_using_tavily("test query")

        assert result["query"] == "test query"
        assert result["answer"] == "Test answer"
        assert len(result["results"]) == 2
        assert result["results"][0]["title"] == "Result 1"

    def test_web_search_no_answer(self, mock_tavily_client):
        mock_client = MagicMock()
        mock_client.search.return_value = {
            "results": [
                {
                    "title": "Result 1",
                    "url": "https://example.com/1",
                    "content": "Content 1",
                    "score": 0.95,
                }
            ]
        }
        mock_tavily_client.return_value = mock_client

        tool = TavilySearchTool(api_key="test-key")
        result = tool.web_search_using_tavily("test query")

        assert "answer" not in result
        assert len(result["results"]) == 1

    def test_web_search_token_limit(self, mock_tavily_client):
        mock_client = MagicMock()
        # Create results with large content that will exceed token limit
        mock_client.search.return_value = {
            "results": [
                {
                    "title": f"Result {i}",
                    "url": f"https://example.com/{i}",
                    "content": "A" * 1000,  # Large content
                    "score": 0.9 - i * 0.1,
                }
                for i in range(10)
            ]
        }
        mock_tavily_client.return_value = mock_client

        # Use a small max_tokens to trigger trimming
        tool = TavilySearchTool(api_key="test-key", max_tokens=2000)
        result = tool.web_search_using_tavily("test query", max_results=10)

        # Should have fewer results due to token limit
        assert len(result["results"]) < 10

    def test_web_search_empty_results(self, mock_tavily_client):
        mock_client = MagicMock()
        mock_client.search.return_value = {"results": []}
        mock_tavily_client.return_value = mock_client

        tool = TavilySearchTool(api_key="test-key")
        result = tool.web_search_using_tavily("obscure query")

        assert result["query"] == "obscure query"
        assert result["results"] == []


class TestTavilyWebSearch:
    @pytest.mark.asyncio
    async def test_search_success(self, mock_tavily_client, mock_env_api_key):
        mock_client = MagicMock()
        mock_client.search.return_value = {
            "answer": "Python is a programming language",
            "results": [
                {
                    "title": "Python Official Site",
                    "url": "https://python.org",
                    "content": "Python is a powerful language",
                    "score": 0.98,
                }
            ],
        }
        mock_tavily_client.return_value = mock_client

        result = await tavily_web_search("What is Python?")
        assert result["success"] is True
        assert result["data"]["query"] == "What is Python?"
        assert len(result["data"]["results"]) == 1

    @pytest.mark.asyncio
    async def test_search_no_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            # Ensure TAVILY_API_KEY is not set
            if "TAVILY_API_KEY" in os.environ:
                del os.environ["TAVILY_API_KEY"]

            result = await tavily_web_search("test query")
            assert result["success"] is False
            assert "TAVILY_API_KEY" in result["error"]

    @pytest.mark.asyncio
    async def test_search_invalid_max_results(self, mock_env_api_key):
        result = await tavily_web_search("test query", max_results=0)
        assert result["success"] is False
        assert "max_results must be at least 1" in result["error"]

    @pytest.mark.asyncio
    async def test_search_negative_max_results(self, mock_env_api_key):
        result = await tavily_web_search("test query", max_results=-5)
        assert result["success"] is False
        assert "max_results must be at least 1" in result["error"]

    @pytest.mark.asyncio
    async def test_search_empty_results(self, mock_tavily_client, mock_env_api_key):
        # When search returns results but the results list is empty
        mock_client = MagicMock()
        mock_client.search.return_value = {"results": []}
        mock_tavily_client.return_value = mock_client

        result = await tavily_web_search("extremely obscure query xyz123")
        # Still succeeds, just with empty results list
        assert result["success"] is True
        assert result["data"]["results"] == []

    @pytest.mark.asyncio
    async def test_search_returns_none(self, mock_tavily_client, mock_env_api_key):
        # Test edge case where web_search_using_tavily returns empty dict
        with patch(
            "src.tools.search.tavily_tool.TavilySearchTool.web_search_using_tavily"
        ) as mock_search:
            mock_search.return_value = {}

            result = await tavily_web_search("test query")
            assert result["success"] is False
            assert "No results found" in result["error"]

    @pytest.mark.asyncio
    async def test_search_exception(self, mock_tavily_client, mock_env_api_key):
        mock_client = MagicMock()
        mock_client.search.side_effect = Exception("API rate limit exceeded")
        mock_tavily_client.return_value = mock_client

        result = await tavily_web_search("test query")
        assert result["success"] is False
        assert "rate limit" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_search_with_custom_params(self, mock_tavily_client, mock_env_api_key):
        mock_client = MagicMock()
        mock_client.search.return_value = {
            "results": [
                {
                    "title": "Deep Result",
                    "url": "https://example.com",
                    "content": "Detailed content",
                    "score": 0.99,
                }
            ]
        }
        mock_tavily_client.return_value = mock_client

        result = await tavily_web_search(
            "advanced query",
            max_results=10,
            search_depth="advanced",
            max_tokens=5000,
        )
        assert result["success"] is True
        mock_client.search.assert_called_once_with(
            query="advanced query", search_depth="advanced", max_results=10
        )

    @pytest.mark.asyncio
    async def test_search_multiple_results(self, mock_tavily_client, mock_env_api_key):
        mock_client = MagicMock()
        mock_client.search.return_value = {
            "results": [
                {
                    "title": f"Result {i}",
                    "url": f"https://example.com/{i}",
                    "content": f"Content for result {i}",
                    "score": 0.9 - i * 0.1,
                }
                for i in range(5)
            ]
        }
        mock_tavily_client.return_value = mock_client

        result = await tavily_web_search("multi result query", max_results=5)
        assert result["success"] is True
        assert len(result["data"]["results"]) == 5

    @pytest.mark.asyncio
    async def test_search_preserves_result_fields(
        self, mock_tavily_client, mock_env_api_key
    ):
        mock_client = MagicMock()
        mock_client.search.return_value = {
            "results": [
                {
                    "title": "Test Title",
                    "url": "https://test.com",
                    "content": "Test content here",
                    "score": 0.87,
                    "extra_field": "should be ignored",
                }
            ]
        }
        mock_tavily_client.return_value = mock_client

        result = await tavily_web_search("test")
        assert result["success"] is True
        res = result["data"]["results"][0]
        assert res["title"] == "Test Title"
        assert res["url"] == "https://test.com"
        assert res["content"] == "Test content here"
        assert res["score"] == 0.87
        # Extra fields should not be included in cleaned response
        assert "extra_field" not in res
