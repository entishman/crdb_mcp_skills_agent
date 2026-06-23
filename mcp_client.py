#!/usr/bin/env python3
"""
MCP Client for CockroachDB

This module handles communication with the CockroachDB Cloud MCP server.
It executes tool calls from Claude API and returns the results.

Based on the MCP client from aidemo1, but refactored for use in an
agent loop where Claude directly calls MCP tools.
"""

import json
import httpx


class MCPClient:
    """
    Client for executing MCP tool calls against CockroachDB Cloud.
    """

    def __init__(self, mcp_server_url, cluster_id, api_key):
        """
        Initialize the MCP client.

        Args:
            mcp_server_url: URL of the MCP server (https://cockroachlabs.cloud/mcp)
            cluster_id: UUID of the CockroachDB cluster
            api_key: API key for authentication
        """
        self.mcp_server_url = mcp_server_url
        self.cluster_id = cluster_id
        self.api_key = api_key
        self.client = httpx.Client(timeout=30.0)
        self.request_id = 0

    def _parse_sse_response(self, text):
        """
        Parse Server-Sent Events (SSE) response to extract JSON data.

        The CockroachDB Cloud MCP server uses SSE format for responses.

        Args:
            text: Raw HTTP response body (SSE formatted text)

        Returns:
            dict: Parsed JSON-RPC response, or None if no data found
        """
        lines = text.strip().split('\n')
        for line in lines:
            if line.startswith('data: '):
                json_str = line[6:]  # Remove 'data: ' prefix
                return json.loads(json_str)
        return None

    def _convert_mcp_to_claude_format(self, mcp_tools):
        """
        Convert MCP tool format to Claude API format.

        MCP uses 'inputSchema' (camelCase)
        Claude API uses 'input_schema' (snake_case)

        Args:
            mcp_tools: List of tools in MCP format

        Returns:
            list: Tools in Claude API format
        """
        claude_tools = []

        for tool in mcp_tools:
            claude_tool = {
                "name": tool.get("name"),
                "description": tool.get("description", "")
            }

            # Convert inputSchema to input_schema
            if "inputSchema" in tool:
                claude_tool["input_schema"] = tool["inputSchema"]
            elif "input_schema" in tool:
                # Already in correct format
                claude_tool["input_schema"] = tool["input_schema"]
            else:
                # No schema provided, add empty one
                claude_tool["input_schema"] = {
                    "type": "object",
                    "properties": {},
                    "required": []
                }

            claude_tools.append(claude_tool)

        return claude_tools

    def list_tools(self):
        """
        Discover available tools from the MCP server using tools/list method.

        Returns tools in Claude API format (with input_schema, not inputSchema).

        Returns:
            list: List of tool definitions in Claude API format, or empty list on error
        """
        self.request_id += 1

        # Build HTTP headers
        headers = {
            "Content-Type": "application/json",
            "mcp-cluster-id": self.cluster_id,
            "Authorization": f"Bearer {self.api_key}"
        }

        # Build JSON-RPC 2.0 request for tools/list
        payload = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "tools/list",
            "params": {}
        }

        try:
            # Send POST request to MCP server
            response = self.client.post(
                self.mcp_server_url,
                headers=headers,
                json=payload
            )

            response.raise_for_status()

            # Parse response
            if 'text/event-stream' in response.headers.get('content-type', ''):
                result = self._parse_sse_response(response.text)
            else:
                result = response.json()

            # Check for errors
            if result and "error" in result:
                print(f"Error discovering tools: {result['error'].get('message', 'Unknown error')}")
                return []

            # Extract tools from response and convert to Claude API format
            if result and "result" in result and "tools" in result["result"]:
                mcp_tools = result["result"]["tools"]
                return self._convert_mcp_to_claude_format(mcp_tools)

            return []

        except Exception as e:
            print(f"Failed to discover tools from MCP server: {e}")
            return []

    def call_tool(self, tool_name, arguments=None):
        """
        Call an MCP tool using JSON-RPC 2.0 over HTTP.

        Args:
            tool_name: Name of the MCP tool to call (e.g., "list_databases")
            arguments: Dictionary of arguments to pass to the tool (default: {})

        Returns:
            dict: Result data from the tool, or error information
        """
        self.request_id += 1

        # Build HTTP headers
        headers = {
            "Content-Type": "application/json",
            "mcp-cluster-id": self.cluster_id,
            "Authorization": f"Bearer {self.api_key}"
        }

        # Build JSON-RPC 2.0 request payload
        payload = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            }
        }

        try:
            # Send POST request to MCP server
            response = self.client.post(
                self.mcp_server_url,
                headers=headers,
                json=payload
            )

            # Raise exception for 4xx/5xx status codes
            response.raise_for_status()

            # Parse response based on content type
            if 'text/event-stream' in response.headers.get('content-type', ''):
                result = self._parse_sse_response(response.text)
            else:
                result = response.json()

            # Check for JSON-RPC errors
            if result and "error" in result:
                return {
                    "error": True,
                    "message": result['error'].get('message', 'Unknown error'),
                    "code": result['error'].get('code', -1)
                }

            # Extract the actual data from the MCP response
            if result and "result" in result and "content" in result["result"]:
                # MCP wraps data in content array with text field
                content = result["result"]["content"]
                if content and len(content) > 0:
                    text_content = content[0].get("text", "{}")
                    # Parse the JSON string
                    data = json.loads(text_content)
                    return {
                        "error": False,
                        "data": data
                    }

            # Unexpected response format
            return {
                "error": True,
                "message": "Unexpected response format from MCP server",
                "raw_response": result
            }

        except httpx.HTTPError as e:
            return {
                "error": True,
                "message": f"HTTP request failed: {e}",
                "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            }

        except json.JSONDecodeError as e:
            return {
                "error": True,
                "message": f"Failed to parse JSON response: {e}"
            }

        except Exception as e:
            return {
                "error": True,
                "message": f"Unexpected error: {e}"
            }

    def execute_tool_call(self, tool_name, tool_input):
        """
        Execute a tool call from Claude API.

        This is the main entry point for the agent to call MCP tools.

        Args:
            tool_name: Name of the tool Claude wants to call
            tool_input: Input parameters for the tool (dict)

        Returns:
            str: JSON string containing the result or error
        """
        result = self.call_tool(tool_name, tool_input)

        if result.get("error"):
            # Return error information
            return json.dumps({
                "success": False,
                "error": result.get("message", "Unknown error"),
                "tool": tool_name,
                "input": tool_input
            }, indent=2)
        else:
            # Return successful result
            return json.dumps({
                "success": True,
                "tool": tool_name,
                "data": result.get("data", {})
            }, indent=2)

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def main():
    """
    Test the MCP client by calling a few tools.
    """
    import sys
    from pathlib import Path

    # Load config
    config_file = Path("config.json")
    if not config_file.exists():
        print("ERROR: config.json not found")
        print("Please copy config.template.json to config.json and add your credentials.")
        sys.exit(1)

    with open(config_file, 'r') as f:
        config = json.load(f)

    # Create MCP client
    with MCPClient(
        mcp_server_url=config["mcp_server_url"],
        cluster_id=config["cluster_id"],
        api_key=config["api_key"]
    ) as client:
        print("=" * 80)
        print("Testing MCP Client")
        print("=" * 80)
        print()

        # Test 1: Get cluster info
        print("Test 1: get_cluster")
        print("-" * 80)
        result = client.execute_tool_call("get_cluster", {})
        print(result)
        print()

        # Test 2: List databases
        print("Test 2: list_databases")
        print("-" * 80)
        result = client.execute_tool_call("list_databases", {})
        print(result)
        print()

        # Test 3: Select query
        print("Test 3: select_query")
        print("-" * 80)
        result = client.execute_tool_call("select_query", {
            "database": "defaultdb",
            "query": "SELECT version()"
        })
        print(result)


if __name__ == "__main__":
    main()
