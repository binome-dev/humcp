import os
import uuid

import pytest
from dotenv import load_dotenv
from grafi.common.containers.container import container
from grafi.common.events.topic_events.publish_to_topic_event import PublishToTopicEvent
from grafi.common.models.invoke_context import InvokeContext
from grafi.common.models.mcp_connections import StreamableHttpConnection
from grafi.common.models.message import Message
from grafi.tools.function_calls.impl.mcp_tool import MCPTool
from simple_function_call_assistant import SimpleFunctionCallAssistant

load_dotenv()

event_store = container.event_store
api_key = os.getenv("OPENAI_API_KEY", "")


def get_invoke_context() -> InvokeContext:
    return InvokeContext(
        conversation_id="conversation_id",
        invoke_id=uuid.uuid4().hex,
        assistant_request_id=uuid.uuid4().hex,
    )


# For integration tests.
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
@pytest.mark.asyncio
async def test_simple_function_call_assistant_with_mcp(mcp_server):
    """Test that the assistant can call MCP tools and return results."""
    invoke_context = get_invoke_context()

    server_params = {
        "mcp": StreamableHttpConnection(
            {
                "url": mcp_server["mcp_url"],
                "transport": "http",
            }
        )
    }

    mcp_tool = await MCPTool.builder().connections(server_params).build()

    assistant = (
        SimpleFunctionCallAssistant.builder()
        .name("MCPAssistant")
        .api_key(api_key)
        .function_tool(mcp_tool)
        .function_call_llm_system_message(
            "You are a helpful assistant that calls functions, you have a bunch of tools that you can call"
        )
        .build()
    )

    input_data = [
        Message(
            role="user",
            content="call the calculator tool and return the results of 1 + 1",
        )
    ]

    outputs = []
    async for output in assistant.invoke(
        PublishToTopicEvent(
            invoke_context=invoke_context,
            data=input_data,
        )
    ):
        print(f"Output: {output}")
        outputs.append(output)
        assert output is not None

    print(f"Total outputs: {len(outputs)}")
    for i, out in enumerate(outputs):
        print(f"Output {i}: {out}")

    events = await event_store.get_events()
    print(f"Total events: {len(events)}")
    assert len(events) == 24
