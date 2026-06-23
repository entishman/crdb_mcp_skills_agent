# CockroachDB Intelligent Agent (aidemo2)

An intelligent agent that uses Claude API to handle CockroachDB tasks through natural language.

## Overview

This agent demonstrates how an LLM (Claude) can dynamically handle database operations by:
1. Loading CockroachDB best practices from SKILL.md files
2. Using Claude API's tool use feature to call MCP tools
3. Executing operations against a CockroachDB cluster
4. Following documented best practices

## Architecture

```
User Input (natural language)
    ↓
Agent loads SKILL.md files from GitHub
    ↓
Claude API receives:
    - User task
    - Skills documentation (best practices)
    - MCP tool definitions
    ↓
Claude creates a plan and calls tools
    ↓
Agent executes tools via MCP server
    ↓
Results sent back to Claude
    ↓
Claude interprets results and responds to user
```

## Key Components

### 1. `skill_fetcher.py`
- Fetches all SKILL.md files from the cockroachdb-skills GitHub repository
- Caches them locally for faster subsequent runs
- Provides skills as context for Claude API

### 2. `mcp_tools.py`
- Defines all available MCP tools in Claude API format
- Includes read-only tools (list databases, select queries, etc.)
- Includes write tools (create database, insert data, etc.)

### 3. `mcp_client.py`
- Handles communication with CockroachDB Cloud MCP server
- Executes tool calls from Claude and returns results
- Parses SSE (Server-Sent Events) responses

### 4. `agent.py`
- Main agent implementation
- Integrates Claude API with MCP tools
- Handles the tool use loop
- Provides interactive and single-task modes

## Comparison to aidemo1

| Feature | aidemo1 | aidemo2 |
|---------|---------|---------|
| **Task Flexibility** | Hardcoded health checks only | Any database task via natural language |
| **LLM Usage** | No LLM in runtime | Claude API at runtime |
| **Planning** | Fixed workflow | Dynamic planning by Claude |
| **Best Practices** | Follows one SKILL.md | Consults all 25+ SKILL.md files |
| **Tool Selection** | Predefined tools | Claude selects tools based on task |
| **Extensibility** | Add new checks = new code | Add new tools = new definitions |

## Setup

### 1. Install Dependencies

```bash
cd /var/www/ai/aidemo2
pip install -r requirements.txt
```

### 2. Configure Credentials

Copy the template and add your credentials:

```bash
cp config.template.json config.json
```

Edit `config.json`:

```json
{
  "mcp_server_url": "https://cockroachlabs.cloud/mcp",
  "cluster_id": "your-cluster-id",
  "auth_method": "api_key",
  "api_key": "your-cockroachdb-api-key",
  "anthropic_api_key": "your-anthropic-api-key"
}
```

You need:
- **CockroachDB Cluster ID**: From CockroachDB Cloud console
- **CockroachDB API Key**: Create in Cloud console → API Access
- **Anthropic API Key**: Get from https://console.anthropic.com

### 3. Test Individual Components

```bash
# Test skill fetcher
python3 skill_fetcher.py

# Test MCP tools definitions
python3 mcp_tools.py

# Test MCP client
python3 mcp_client.py
```

## Usage

### Interactive Mode

```bash
python3 agent.py
```

Then enter tasks:
```
Task: show me all databases
Task: list tables in defaultdb
Task: run a query to check the cockroachdb version
Task: what tables exist in my cluster?
```

### Single Task Mode

```bash
python3 agent.py "show me all databases"
python3 agent.py "list all tables in the defaultdb database"
python3 agent.py "run SELECT version()"
```

## Example Tasks

### List Databases
```
Task: show me all databases
```

Claude will:
1. Recognize this requires the `list_databases` tool
2. Call the tool via MCP
3. Format the results for you

### List Tables
```
Task: what tables are in the defaultdb database?
```

Claude will:
1. Use the `list_tables` tool with database="defaultdb"
2. Show you all tables

### Execute Query
```
Task: check the CockroachDB version
```

Claude will:
1. Use the `select_query` tool with query="SELECT version()"
2. Display the version information

### Get Table Schema
```
Task: show me the schema for the users table in mydb
```

Claude will:
1. Use the `get_table_schema` tool
2. Display the CREATE TABLE statement

### Complex Task
```
Task: I want to understand what data is in my cluster
```

Claude will:
1. Consult the skills documentation
2. Call `list_databases` to see all databases
3. For each database, call `list_tables`
4. Summarize the findings

## How It Works

### Skills-Based Planning

When you ask a question, Claude:
1. Reviews the 25+ SKILL.md files loaded into its context
2. Identifies relevant best practices
3. Creates a plan based on those practices
4. Executes the plan using MCP tools

For example, if you ask about "cluster health," Claude will:
- Find the "reviewing-cluster-health" skill
- Follow its guidance on what checks to perform
- Call appropriate MCP tools (get_cluster, list_databases, show_running_queries, etc.)
- Present results following the skill's recommendations

### Tool Use Loop

```python
while True:
    # Claude processes the task
    response = claude.messages.create(...)
    
    if response.stop_reason == "end_turn":
        # Claude is done - return final answer
        return final_text
    
    elif response.stop_reason == "tool_use":
        # Claude wants to call tools
        for tool_call in response.content:
            # Execute tool via MCP
            result = mcp_client.execute_tool_call(...)
            
            # Send result back to Claude
            messages.append(tool_result)
        
        # Continue loop - Claude processes results
```

## Available MCP Tools

### Read-Only Tools (Always Safe)
- `list_clusters` - List all accessible clusters
- `get_cluster` - Get cluster details
- `list_databases` - List all databases
- `list_tables` - List tables in a database
- `get_table_schema` - Get table schema
- `select_query` - Execute SELECT queries
- `explain_query` - Show query execution plans
- `show_running_queries` - Show active queries

### Write Tools (Require Confirmation)
- `create_database` - Create a new database
- `create_table` - Create a new table
- `insert_rows` - Insert data

## Skills Documentation

The agent loads all skills from:
https://github.com/cockroachlabs/cockroachdb-skills/tree/main/skills

Current skills include:
- **operations-and-lifecycle**: cluster health, maintenance, upgrades, capacity
- **observability-and-diagnostics**: monitoring, profiling, troubleshooting
- **query-and-schema-design**: SQL best practices, schema design
- **security-and-governance**: authentication, encryption, audit logging
- **performance-and-scaling**: optimization, scaling strategies
- And many more...

## Advantages of This Approach

### 1. **Flexibility**
- Handles any database task without code changes
- Natural language interface
- No need to remember exact commands

### 2. **Intelligence**
- Claude understands intent, not just keywords
- Follows best practices automatically
- Can handle ambiguous requests

### 3. **Documentation-Aware**
- Consults 25+ skill documents
- Always follows CockroachDB best practices
- Knowledge updates when skills are updated

### 4. **Extensibility**
- Add new MCP tools → agent gains new capabilities
- Update SKILL.md files → agent learns new practices
- No code changes needed

### 5. **Safety**
- Read operations execute automatically
- Write operations ask for confirmation
- Claude explains what it's doing

## Limitations

1. **Requires Anthropic API Key**
   - Costs money per API call
   - Need internet connection

2. **Slower than aidemo1**
   - LLM inference takes time
   - Multiple tool calls add latency

3. **Token Limits**
   - Skills documentation uses ~50k tokens
   - Limits conversation length
   - May need to trim skills for very long conversations

4. **Less Predictable**
   - LLM may interpret tasks differently
   - Results may vary between runs
   - Need to validate critical operations

## Future Enhancements

1. **Streaming Responses**
   - Show Claude's thinking in real-time
   - Better user experience

2. **Conversation Memory**
   - Remember previous queries in session
   - Build on prior context

3. **Multi-Cluster Support**
   - Switch between clusters in one session
   - Compare clusters

4. **Skill Selection Optimization**
   - Only load relevant skills per task
   - Reduce token usage
   - Faster responses

5. **Autonomous Agent Mode**
   - Agent runs scheduled tasks
   - Proactive monitoring
   - Alert on anomalies

## Troubleshooting

### "No module named 'anthropic'"
```bash
pip install anthropic
```

### "Missing or incomplete configuration"
Make sure `config.json` has all fields filled in with real values.

### "API key not valid"
Check that your Anthropic API key is correct in `config.json`.

### "GitHub API rate limit"
The skill fetcher may hit rate limits. Skills are cached in `.cache/` directory,
so subsequent runs will use the cache instead of fetching from GitHub.

### "MCP connection failed"
Verify:
- CockroachDB cluster is running
- Cluster ID is correct
- API key is valid and has cluster access

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface                          │
│  "Show me all databases in the cluster"                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  CockroachDB Agent                           │
│  - Loads SKILL.md files (25+ skills)                        │
│  - Calls Claude API with skills context                     │
│  - Handles tool use loop                                     │
└────┬────────────────────────────────────────┬───────────────┘
     │                                         │
     │ Skills Context                          │ Tool Calls
     │ + User Task                             │
     ▼                                         ▼
┌─────────────────────────────────┐   ┌──────────────────────┐
│       Claude API                │   │    MCP Client        │
│  - Understands task             │   │  - Executes tools    │
│  - Consults skills              │   │  - Parses responses  │
│  - Selects tools                │   │                      │
│  - Calls tools                  │   │                      │
│  - Interprets results           │   │                      │
└─────────────────────────────────┘   └──────┬───────────────┘
                                              │
                                              │ JSON-RPC
                                              ▼
                                    ┌─────────────────────────┐
                                    │   MCP Server            │
                                    │  (CockroachDB Cloud)    │
                                    └──────┬──────────────────┘
                                           │
                                           │ SQL
                                           ▼
                                    ┌─────────────────────────┐
                                    │  CockroachDB Cluster    │
                                    │  - Databases            │
                                    │  - Tables               │
                                    │  - Data                 │
                                    └─────────────────────────┘
```

## License

This is a demonstration project for learning purposes.

## Related Projects

- **aidemo1**: Fixed health check agent (no LLM at runtime)
- **CockroachDB Skills**: https://github.com/cockroachlabs/cockroachdb-skills
- **MCP Protocol**: https://modelcontextprotocol.io
- **Claude API**: https://docs.anthropic.com
