#!/usr/bin/env python3
"""
Agent Tool Definitions for Claude API

This module defines ONLY the agent-specific tools (fetch_skill, complete_task).
MCP tools are now discovered dynamically from the MCP server at runtime.

NO HARDCODED TOOLS! The agent discovers available tools from the MCP server.
"""


def get_agent_tools():
    """
    Get tools that the agent handles locally (not sent to MCP server).

    These are agent-specific tools for managing the conversation and skill loading.

    Returns:
        list: Agent-specific tool definitions
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
                        "description": "Name of the skill to fetch (e.g., 'operations-and-lifecycle/reviewing-cluster-health', 'onboarding-and-migrations/molt-replicator'). Available skill categories: operations-and-lifecycle, query-and-schema-design, observability-and-diagnostics, security-and-governance, onboarding-and-migrations."
                    }
                },
                "required": ["skill_name"]
            }
        },
        {
            "name": "complete_task",
            "description": "Call this when you have completed the user's task and are ready to provide the final answer. Include which skills (if any) helped you answer the question.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "skills_that_helped": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of skill names that you actually referenced and used to complete this task. ONLY include skills you truly used. If you didn't need any skills, pass an empty array []."
                    },
                    "answer": {
                        "type": "string",
                        "description": "Your complete answer to the user's question. This should be the full response, not a summary."
                    }
                },
                "required": ["skills_that_helped", "answer"]
            }
        }
    ]


if __name__ == "__main__":
    """Test agent tools"""
    import json

    print("=" * 80)
    print("Agent-Specific Tools")
    print("=" * 80)
    print()

    tools = get_agent_tools()

    print(f"Number of agent tools: {len(tools)}")
    print()

    for i, tool in enumerate(tools, 1):
        print(f"{i}. {tool['name']}")
        print(f"   Description: {tool['description'][:80]}...")
        print()

    print("MCP tools are discovered dynamically from the server at runtime!")
    print("No hardcoded tool definitions = no brittleness!")
