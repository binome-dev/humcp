import asyncio
import logging

from fastmcp import FastMCP

from src.tools.google.auth import SCOPES, get_google_service

logger = logging.getLogger("humcp.tools.google.chat")

CHAT_READONLY_SCOPES = [SCOPES["chat_spaces"], SCOPES["chat_messages_readonly"]]
CHAT_FULL_SCOPES = [SCOPES["chat_spaces"], SCOPES["chat_messages"]]


async def list_spaces(space_type: str = "all", max_results: int = 100) -> dict:
    """List Google Chat spaces (rooms and direct messages)."""
    try:

        def _list():
            service = get_google_service("chat", "v1", CHAT_READONLY_SCOPES)
            results = service.spaces().list(pageSize=max_results).execute()
            spaces = results.get("spaces", [])

            # Filter by type if requested
            if space_type != "all":
                type_filter = "ROOM" if space_type == "room" else "DIRECT_MESSAGE"
                spaces = [s for s in spaces if s.get("type") == type_filter]

            return {
                "spaces": [
                    {
                        "name": s["name"],
                        "display_name": s.get("displayName", ""),
                        "type": s.get("type", ""),
                        "single_user_bot_dm": s.get("singleUserBotDm", False),
                        "threaded": s.get("threaded", False),
                    }
                    for s in spaces
                ],
                "total": len(spaces),
            }

        logger.info("chat_list_spaces type=%s", space_type)
        result = await asyncio.to_thread(_list)
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception("chat_list_spaces failed")
        return {"success": False, "error": str(e)}


async def get_messages(
    space_name: str,
    max_results: int = 25,
    order_by: str = "createTime desc",
) -> dict:
    """Get messages from a Google Chat space."""
    try:

        def _get():
            service = get_google_service("chat", "v1", CHAT_READONLY_SCOPES)
            results = (
                service.spaces()
                .messages()
                .list(parent=space_name, pageSize=max_results, orderBy=order_by)
                .execute()
            )
            messages = results.get("messages", [])

            return {
                "messages": [
                    {
                        "name": m["name"],
                        "text": m.get("text", ""),
                        "sender": m.get("sender", {}).get("displayName", ""),
                        "sender_type": m.get("sender", {}).get("type", ""),
                        "created": m.get("createTime", ""),
                        "thread_name": m.get("thread", {}).get("name", ""),
                    }
                    for m in messages
                ],
                "total": len(messages),
            }

        logger.info("chat_get_messages space=%s", space_name)
        result = await asyncio.to_thread(_get)
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception("chat_get_messages failed")
        return {"success": False, "error": str(e)}


async def send_message(
    space_name: str,
    text: str,
    thread_key: str = "",
) -> dict:
    """Send a message to a Google Chat space."""
    try:

        def _send():
            service = get_google_service("chat", "v1", CHAT_FULL_SCOPES)

            body = {"text": text}
            kwargs = {"parent": space_name, "body": body}

            if thread_key:
                body["thread"] = {"threadKey": thread_key}
                kwargs["messageReplyOption"] = "REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD"

            message = service.spaces().messages().create(**kwargs).execute()

            return {
                "name": message["name"],
                "text": message.get("text", ""),
                "created": message.get("createTime", ""),
                "thread_name": message.get("thread", {}).get("name", ""),
            }

        logger.info("chat_send_message space=%s", space_name)
        result = await asyncio.to_thread(_send)
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception("chat_send_message failed")
        return {"success": False, "error": str(e)}


async def get_space(space_name: str) -> dict:
    """Get details about a specific space."""
    try:

        def _get():
            service = get_google_service("chat", "v1", CHAT_READONLY_SCOPES)
            space = service.spaces().get(name=space_name).execute()

            return {
                "name": space["name"],
                "display_name": space.get("displayName", ""),
                "type": space.get("type", ""),
                "single_user_bot_dm": space.get("singleUserBotDm", False),
                "threaded": space.get("threaded", False),
                "external_user_allowed": space.get("externalUserAllowed", False),
            }

        logger.info("chat_get_space space=%s", space_name)
        result = await asyncio.to_thread(_get)
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception("chat_get_space failed")
        return {"success": False, "error": str(e)}


async def get_message(message_name: str) -> dict:
    """Get a specific message by name."""
    try:

        def _get():
            service = get_google_service("chat", "v1", CHAT_READONLY_SCOPES)
            message = service.spaces().messages().get(name=message_name).execute()

            return {
                "name": message["name"],
                "text": message.get("text", ""),
                "sender": message.get("sender", {}).get("displayName", ""),
                "sender_type": message.get("sender", {}).get("type", ""),
                "created": message.get("createTime", ""),
                "thread_name": message.get("thread", {}).get("name", ""),
                "space_name": message.get("space", {}).get("name", ""),
            }

        logger.info("chat_get_message message=%s", message_name)
        result = await asyncio.to_thread(_get)
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception("chat_get_message failed")
        return {"success": False, "error": str(e)}


def register_tools(mcp: FastMCP) -> None:
    """Register all Google Chat tools with the MCP server."""
    mcp.tool(name="chat_list_spaces")(list_spaces)
    mcp.tool(name="chat_get_space")(get_space)
    mcp.tool(name="chat_get_messages")(get_messages)
    mcp.tool(name="chat_get_message")(get_message)
    mcp.tool(name="chat_send_message")(send_message)
