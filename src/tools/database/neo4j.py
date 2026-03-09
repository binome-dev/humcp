"""Neo4j graph database tools for Cypher queries and schema inspection."""

from __future__ import annotations

import logging
import os
from typing import Any

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.humcp.permissions import require_auth
from src.tools.database.schemas import (
    Neo4jQueryData,
    Neo4jQueryResponse,
    Neo4jSchemaData,
    Neo4jSchemaResponse,
)

try:
    from neo4j import GraphDatabase
except ImportError as err:
    raise ImportError(
        "neo4j is required for Neo4j tools. Install with: pip install neo4j"
    ) from err

logger = logging.getLogger("humcp.tools.database.neo4j")


def _get_driver(username: str, password: str):
    """Create a Neo4j driver with the provided credentials.

    Args:
        username: Neo4j username.
        password: Neo4j password.

    Returns:
        A Neo4j driver instance.
    """
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    return GraphDatabase.driver(uri, auth=(username, password))


@tool()
async def neo4j_query(
    cypher_query: str,
    parameters: dict[str, Any] | None = None,
) -> Neo4jQueryResponse:
    """Execute a Cypher query against the Neo4j database.

    Runs any Cypher query and returns the results as a list of records.

    Args:
        cypher_query: The Cypher query string to execute.
        parameters: Optional dictionary of query parameters.

    Returns:
        Query results as a list of record dictionaries.
    """
    try:
        await require_auth()

        username = await resolve_credential("NEO4J_USERNAME")
        password = await resolve_credential("NEO4J_PASSWORD")
        if not username or not password:
            return Neo4jQueryResponse(
                success=False,
                error="NEO4J_USERNAME and NEO4J_PASSWORD are required.",
            )

        logger.info("Executing Cypher query: %s", cypher_query)

        driver = _get_driver(username, password)
        try:
            with driver.session() as session:
                result = session.run(
                    cypher_query,
                    parameters=parameters or {},
                )
                records = result.data()

            return Neo4jQueryResponse(
                success=True,
                data=Neo4jQueryData(
                    records=records,
                    record_count=len(records),
                ),
            )
        finally:
            driver.close()

    except ValueError as e:
        return Neo4jQueryResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception("Neo4j query failed")
        return Neo4jQueryResponse(success=False, error=f"Neo4j error: {e}")


@tool()
async def neo4j_get_schema() -> Neo4jSchemaResponse:
    """Retrieve the schema of the Neo4j database.

    Returns node labels, relationship types, and a schema visualization
    of the connected Neo4j database.

    Returns:
        Database schema including labels, relationship types, and visualization data.
    """
    try:
        await require_auth()

        username = await resolve_credential("NEO4J_USERNAME")
        password = await resolve_credential("NEO4J_PASSWORD")
        if not username or not password:
            return Neo4jSchemaResponse(
                success=False,
                error="NEO4J_USERNAME and NEO4J_PASSWORD are required.",
            )

        logger.info("Retrieving Neo4j schema")

        driver = _get_driver(username, password)
        try:
            with driver.session() as session:
                # Get node labels
                labels_result = session.run("CALL db.labels()")
                labels = [record["label"] for record in labels_result]

                # Get relationship types
                rel_result = session.run("CALL db.relationshipTypes()")
                relationship_types = [
                    record["relationshipType"] for record in rel_result
                ]

                # Get schema visualization
                try:
                    viz_result = session.run("CALL db.schema.visualization()")
                    schema_visualization = viz_result.data()
                except Exception:
                    logger.warning("db.schema.visualization() not available, skipping")
                    schema_visualization = []

            return Neo4jSchemaResponse(
                success=True,
                data=Neo4jSchemaData(
                    labels=labels,
                    relationship_types=relationship_types,
                    schema_visualization=schema_visualization,
                ),
            )
        finally:
            driver.close()

    except ValueError as e:
        return Neo4jSchemaResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception("Neo4j get schema failed")
        return Neo4jSchemaResponse(success=False, error=f"Neo4j error: {e}")
