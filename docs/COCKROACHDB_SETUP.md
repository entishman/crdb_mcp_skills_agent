# CockroachDB MCP Server Setup

## Overview
This document describes the setup of CockroachDB Cloud MCP server integration with Claude Code to enable database operations via natural language.

## Configuration Details

### MCP Server Added
- **Server Name**: `cockroachdb-cloud`
- **URL**: `https://cockroachlabs.cloud/mcp`
- **Transport**: HTTP
- **Authentication**: API Key (Bearer token)

### Cluster Configuration
- **Cluster ID**: `c4130e1a-0736-4618-9abc-9cbd32e563a5`
- **Service Account API Key**: Configured (stored in `.claude.json`)

### Configuration Location
The MCP server configuration was added to:
```
~/.claude.json
```

Under the `mcpServers` section:
```json
{
  "cockroachdb-cloud": {
    "type": "http",
    "url": "https://cockroachlabs.cloud/mcp",
    "headers": {
      "mcp-cluster-id": "c4130e1a-0736-4618-9abc-9cbd32e563a5",
      "Authorization": "Bearer YOUR_COCKROACHDB_API_KEY_HERE"
    }
  }
}
```

## How Write Capabilities Are Enabled

With **API Key authentication**, write permissions are determined by the service account role:

### Read-Only Tools (always available):
- `list_clusters` - List all accessible clusters
- `get_cluster` - Get detailed cluster information
- `list_databases` - List databases in the cluster
- `list_tables` - List tables in a database
- `get_table_schema` - Get detailed schema for a table
- `select_query` - Execute SELECT statements
- `explain_query` - Execute EXPLAIN statements
- `show_running_queries` - List currently executing queries

### Write Tools (enabled with Cluster Admin or Cluster Operator role):
- `create_database` - Create a new database
- `create_table` - Create a new table
- `insert_rows` - Insert rows into a table

**Note**: Destructive operations (DROP, TRUNCATE) are not supported even with write permissions.

## Service Account Role Requirements

For write operations to work, ensure the service account has one of these roles:
- **Cluster Admin** - Full read and write access
- **Cluster Operator** - Full read and write access

Check role assignment in CockroachDB Cloud Console:
1. Go to **Access Management** > **Service Accounts**
2. Find your service account
3. Verify it has **Cluster Admin** or **Cluster Operator** role assigned

## Troubleshooting

### Connection Health Check Failing
If `claude mcp list` shows the server as "Failed to connect":

1. **Restart Claude Code**
   - The MCP server config was just added
   - Restart is required for changes to take full effect

2. **Verify Service Account Role**
   - Check that the service account has Cluster Admin or Cluster Operator role
   - Recreate API key if needed

3. **Verify Cluster ID**
   - Ensure cluster ID matches the one in your CockroachDB Cloud Console URL
   - Format: `https://cockroachlabs.cloud/cluster/{CLUSTER-ID}/overview`

4. **Verify API Key**
   - Ensure the API key is active and hasn't been revoked
   - API keys start with `CCDB1_`

### Write Tools Not Available
If read tools work but write tools are missing:
- Verify service account has Cluster Admin or Cluster Operator role (not just Cluster Developer or other roles)

## Next Steps

1. ✅ **MCP Server Configured** - OAuth authentication successful
2. ✅ **Write Permissions Granted** - Can use `create_database`, `create_table`, `insert_rows` tools

## Testing Write Operations

### From Claude Code (CLI):
The MCP server is now configured with write permissions. Test it:
```bash
cd /var/www/ai/aidemo2
claude
# Then type: create a database called timbob
```

### From Custom Application (agent.py):
✅ **Write operations now enabled** with safety confirmations!

Changes made:
- `agent.py` line 697: Now uses `get_tool_definitions()` to include write tools
- Safety confirmation: User must approve before any write operation executes
- Supported write operations:
  - `create_database` - Create new databases
  - `create_table` - Create new tables  
  - `insert_rows` - Insert data into tables

Test it:
```bash
python3 agent.py
# Try: create a database called timbob
# You'll be prompted to confirm before execution
```

## References
- [CockroachDB Cloud MCP Server Documentation](https://www.cockroachlabs.com/docs/cockroachcloud/connect-to-the-cockroachdb-cloud-mcp-server)
- [MCP Server Configuration](https://code.claude.com/docs/en/mcp)
