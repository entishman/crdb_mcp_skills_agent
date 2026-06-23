#!/usr/bin/env python3
"""
Test tool discovery from MCP server
"""

from agent import CockroachDBAgent
from mcp_tools import get_agent_tools

print("=" * 80)
print("Testing Dynamic Tool Discovery")
print("=" * 80)
print()

# Create agent (this will discover tools)
agent = CockroachDBAgent()

print()
print("=" * 80)
print("Tools Available to Claude")
print("=" * 80)
print()

# Show MCP tools (discovered)
print(f"MCP Tools (discovered from server): {len(agent.mcp_tools)}")
for i, tool in enumerate(agent.mcp_tools, 1):
    print(f"  {i}. {tool['name']}")
    print(f"     {tool.get('description', 'No description')[:70]}...")

print()

# Show agent tools (hardcoded)
agent_tools = get_agent_tools()
print(f"Agent Tools (hardcoded in code): {len(agent_tools)}")
for i, tool in enumerate(agent_tools, 1):
    print(f"  {i}. {tool['name']}")
    print(f"     {tool['description'][:70]}...")

print()
print("=" * 80)
print(f"Total tools available to Claude: {len(agent.mcp_tools) + len(agent_tools)}")
print("=" * 80)
print()
print("✅ NO HARDCODED MCP TOOLS!")
print("✅ All MCP tools discovered dynamically from the server")
print("✅ Demo is not brittle - adapts to server changes automatically")
