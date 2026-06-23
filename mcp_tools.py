#!/usr/bin/env python3
"""
MCP Tool Definitions for Claude API

This module defines all available CockroachDB MCP tools in the format
that Claude API expects for tool use. When Claude wants to interact with
CockroachDB, it will call these tools, and we'll execute them via the MCP server.
"""


# Tool definitions for Claude API
# These match the MCP server tools available at https://cockroachlabs.cloud/mcp
MCP_TOOLS = [
    {
        "name": "list_clusters",
        "description": "List all CockroachDB clusters accessible to the authenticated user. Returns cluster IDs, names, plans, regions, and status.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_cluster",
        "description": "Get detailed information about the current CockroachDB cluster, including version, cloud provider, state, plan, regions, and configuration.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "list_databases",
        "description": "List all databases in the CockroachDB cluster. Equivalent to SQL: SHOW DATABASES. Returns database names and owners.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "list_tables",
        "description": "List all tables in a specific database. Equivalent to SQL: SHOW TABLES FROM <database>. Returns table names, schema, and types.",
        "input_schema": {
            "type": "object",
            "properties": {
                "database": {
                    "type": "string",
                    "description": "Name of the database to list tables from"
                }
            },
            "required": ["database"]
        }
    },
    {
        "name": "get_table_schema",
        "description": "Get the schema (CREATE TABLE statement) for a specific table. Shows columns, data types, constraints, indexes, and foreign keys.",
        "input_schema": {
            "type": "object",
            "properties": {
                "database": {
                    "type": "string",
                    "description": "Name of the database containing the table"
                },
                "table": {
                    "type": "string",
                    "description": "Name of the table (optionally schema-qualified like 'public.users')"
                }
            },
            "required": ["database", "table"]
        }
    },
    {
        "name": "select_query",
        "description": "Execute a SELECT query against the database. Returns query results as rows. Use this for reading data, checking database state, or running diagnostics. Only SELECT statements are allowed - no INSERT, UPDATE, DELETE, or DDL.",
        "input_schema": {
            "type": "object",
            "properties": {
                "database": {
                    "type": "string",
                    "description": "Name of the database to query"
                },
                "query": {
                    "type": "string",
                    "description": "The SELECT SQL query to execute (must start with SELECT)"
                }
            },
            "required": ["database", "query"]
        }
    },
    {
        "name": "explain_query",
        "description": "Execute an EXPLAIN statement to show the query execution plan. Useful for understanding query performance, identifying full table scans, and optimizing queries. Can use EXPLAIN, EXPLAIN ANALYZE, or EXPLAIN (DISTSQL).",
        "input_schema": {
            "type": "object",
            "properties": {
                "database": {
                    "type": "string",
                    "description": "Name of the database to query"
                },
                "query": {
                    "type": "string",
                    "description": "The EXPLAIN statement to execute (e.g., 'EXPLAIN SELECT * FROM users')"
                }
            },
            "required": ["database", "query"]
        }
    },
    {
        "name": "show_running_queries",
        "description": "Show all currently running SQL queries on the cluster. Equivalent to querying crdb_internal.cluster_queries. Returns query text, user, start time, and execution status. Useful for identifying long-running queries or troubleshooting performance.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "create_database",
        "description": "Create a new database in the cluster. Equivalent to SQL: CREATE DATABASE <name>. This is a write operation that requires explicit user consent.",
        "input_schema": {
            "type": "object",
            "properties": {
                "database": {
                    "type": "string",
                    "description": "Name of the database to create"
                }
            },
            "required": ["database"]
        }
    },
    {
        "name": "create_table",
        "description": "Create a new table in a database. Requires a CREATE TABLE SQL statement. This is a write operation that requires explicit user consent.",
        "input_schema": {
            "type": "object",
            "properties": {
                "database": {
                    "type": "string",
                    "description": "Name of the database where the table will be created"
                },
                "create_statement": {
                    "type": "string",
                    "description": "The CREATE TABLE SQL statement"
                }
            },
            "required": ["database", "create_statement"]
        }
    },
    {
        "name": "insert_rows",
        "description": "Insert rows into a table. Equivalent to SQL: INSERT INTO <table> VALUES (...). This is a write operation that requires explicit user consent.",
        "input_schema": {
            "type": "object",
            "properties": {
                "database": {
                    "type": "string",
                    "description": "Name of the database containing the table"
                },
                "table": {
                    "type": "string",
                    "description": "Name of the table to insert into"
                },
                "rows": {
                    "type": "array",
                    "description": "Array of row objects to insert, where each object has column names as keys",
                    "items": {
                        "type": "object"
                    }
                }
            },
            "required": ["database", "table", "rows"]
        }
    }
]


def get_tool_definitions():
    """
    Get all MCP tool definitions formatted for Claude API.

    Returns:
        list: List of tool definition dictionaries
    """
    return MCP_TOOLS


def get_tool_by_name(tool_name):
    """
    Get a specific tool definition by name.

    Args:
        tool_name: Name of the tool (e.g., "list_databases")

    Returns:
        dict: Tool definition, or None if not found
    """
    for tool in MCP_TOOLS:
        if tool["name"] == tool_name:
            return tool
    return None


def get_read_only_tools():
    """
    Get only read-only tools (safe operations that don't modify data).

    Returns:
        list: List of read-only tool definitions
    """
    write_tools = {"create_database", "create_table", "insert_rows"}
    return [tool for tool in MCP_TOOLS if tool["name"] not in write_tools]


def get_write_tools():
    """
    Get only write tools (operations that modify data/schema).

    Returns:
        list: List of write tool definitions
    """
    write_tools = {"create_database", "create_table", "insert_rows"}
    return [tool for tool in MCP_TOOLS if tool["name"] in write_tools]


def get_agent_tools():
    """
    Get tools that the agent handles locally (not sent to MCP server).

    Returns:
        list: Agent-specific tools
    """
    return [
        {
            "name": "fetch_skill",
            "description": "Load a specific CockroachDB skill guide when you need additional information not in your current context. Use this when the user's request requires knowledge from a specific skill area that you don't currently have.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "skill_name": {
                        "type": "string",
                        "description": "Name of the skill to fetch (e.g., 'data-security-and-compliance/replication-configuration'). Available skills: operations-and-lifecycle/reviewing-cluster-health, query-and-schema-design/cockroachdb-sql, observability-and-diagnostics/triaging-live-sql-activity, data-security-and-compliance/replication-configuration, deployment-and-infrastructure/cluster-topology, and others."
                    }
                },
                "required": ["skill_name"]
            }
        },
        {
            "name": "complete_task",
            "description": "Mark the user's task as complete and report which skills were actually helpful in answering their question. Call this when you have successfully completed the task and are ready to return your final answer.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "skills_that_helped": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of skill names that were actually useful in completing this task. Only include skills whose content you referenced in your answer. Exclude skills that were loaded but not used."
                    },
                    "answer": {
                        "type": "string",
                        "description": "Your final answer to the user's question"
                    }
                },
                "required": ["skills_that_helped", "answer"]
            }
        }
    ]


def get_all_tools():
    """
    Get all available tools (MCP + agent tools).

    Returns:
        list: All tools
    """
    return get_read_only_tools() + get_agent_tools()


def main():
    """
    Test: Display all available MCP tools.
    """
    print("=" * 80)
    print("CockroachDB MCP Tools for Claude API")
    print("=" * 80)
    print()

    print("READ-ONLY TOOLS:")
    print("-" * 80)
    for tool in get_read_only_tools():
        print(f"\n{tool['name']}")
        print(f"  {tool['description']}")
        if tool['input_schema']['required']:
            print(f"  Required: {', '.join(tool['input_schema']['required'])}")

    print("\n\nWRITE TOOLS (require user consent):")
    print("-" * 80)
    for tool in get_write_tools():
        print(f"\n{tool['name']}")
        print(f"  {tool['description']}")
        if tool['input_schema']['required']:
            print(f"  Required: {', '.join(tool['input_schema']['required'])}")

    print(f"\n\nTotal: {len(MCP_TOOLS)} tools")


if __name__ == "__main__":
    main()
