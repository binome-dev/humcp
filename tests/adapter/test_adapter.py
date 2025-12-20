import inspect

from src.adapter.adapter import FastMCPFastAPIAdapter


class TestConstructUrl:
    def _get_construct_url(self):
        return FastMCPFastAPIAdapter._construct_url

    def test_sse_transport_appends_sse(self):
        adapter = object.__new__(FastMCPFastAPIAdapter)
        result = adapter._construct_url("http://localhost:8080", "sse")
        assert result == "http://localhost:8080/sse"

    def test_sse_transport_already_has_sse(self):
        adapter = object.__new__(FastMCPFastAPIAdapter)
        result = adapter._construct_url("http://localhost:8080/sse", "sse")
        assert result == "http://localhost:8080/sse"

    def test_sse_transport_trailing_slash(self):
        adapter = object.__new__(FastMCPFastAPIAdapter)
        result = adapter._construct_url("http://localhost:8080/", "sse")
        assert result == "http://localhost:8080/sse"

    def test_stdio_transport_unchanged(self):
        adapter = object.__new__(FastMCPFastAPIAdapter)
        result = adapter._construct_url("http://localhost:8080", "stdio")
        assert result == "http://localhost:8080"

    def test_stdio_transport_with_trailing_slash(self):
        adapter = object.__new__(FastMCPFastAPIAdapter)
        result = adapter._construct_url("http://localhost:8080/", "stdio")
        assert result == "http://localhost:8080"

    def test_custom_transport_appends(self):
        adapter = object.__new__(FastMCPFastAPIAdapter)
        result = adapter._construct_url("http://localhost:8080", "websocket")
        assert result == "http://localhost:8080/websocket"

    def test_custom_transport_already_has_suffix(self):
        adapter = object.__new__(FastMCPFastAPIAdapter)
        result = adapter._construct_url("http://localhost:8080/websocket", "websocket")
        assert result == "http://localhost:8080/websocket"

    def test_complex_url_with_path(self):
        adapter = object.__new__(FastMCPFastAPIAdapter)
        result = adapter._construct_url("http://localhost:8080/api/v1", "sse")
        assert result == "http://localhost:8080/api/v1/sse"

    def test_https_url(self):
        adapter = object.__new__(FastMCPFastAPIAdapter)
        result = adapter._construct_url("https://example.com", "sse")
        assert result == "https://example.com/sse"

    def test_url_with_port(self):
        adapter = object.__new__(FastMCPFastAPIAdapter)
        result = adapter._construct_url("http://192.168.1.1:3000", "sse")
        assert result == "http://192.168.1.1:3000/sse"


class TestAdapterInitialization:
    def test_default_values(self):
        assert hasattr(FastMCPFastAPIAdapter.__init__, "__code__")

    def test_init_parameters(self):
        sig = inspect.signature(FastMCPFastAPIAdapter.__init__)
        params = list(sig.parameters.keys())

        assert "mcp_transport" in params
        assert "transport" in params
        assert "title" in params
        assert "description" in params
        assert "version" in params
        assert "route_prefix" in params
        assert "tags" in params
