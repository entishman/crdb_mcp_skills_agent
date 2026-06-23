# Requirements: Enabling Write Operations in CockroachDB Agent

## Overview
This document details the exact steps taken to enable write operations (create_database, create_table, insert_rows) in the CockroachDB Intelligent Agent with safety confirmations.

## Date Implemented
2026-04-05

## Components Modified

### 1. MCP Server Configuration (OAuth Authentication)

**File**: `~/.claude.json` (project-specific config for `/var/www/ai/aidemo2`)

**What We Did**:
1. **Removed API Key Configuration** (initial attempt that failed):
   ```bash
   claude mcp remove cockroachdb-cloud
   ```

2. **Added OAuth Configuration** (successful approach):
   ```bash
   claude mcp add cockroachdb-cloud https://cockroachlabs.cloud/mcp --transport http --header "mcp-cluster-id: c4130e1a-0736-4618-9abc-9cbd32e563a5"
   ```

3. **Authenticated via OAuth**:
   - Ran `/mcp` command in Claude Code
   - Selected `cockroachdb-cloud` server
   - Clicked **Authenticate**
   - Logged in to CockroachDB Cloud in browser
   - Selected organization
   - **Granted BOTH read AND write permissions** in the "Authorize MCP Access" modal
   - Clicked **Authorize**

**Result**: MCP server configured with write permissions via OAuth (recommended method)

**Configuration Added to ~/.claude.json**:
```json
{
  "mcpServers": {
    "cockroachdb-cloud": {
      "type": "http",
      "url": "https://cockroachlabs.cloud/mcp",
      "headers": {
        "mcp-cluster-id": "c4130e1a-0736-4618-9abc-9cbd32e563a5"
      }
    }
  }
}
```

**Why OAuth vs API Key**:
- API key authentication required an active session established through OAuth first
- OAuth is the recommended method by CockroachDB (more secure with short-lived tokens)
- The error "GET requires an active session" confirmed this requirement

---

### 2. Agent Code Modifications

#### A. Import Statement (Line 54)

**File**: `/var/www/ai/aidemo2/agent.py`

**Before**:
```python
from mcp_tools import get_tool_definitions, get_read_only_tools, get_all_tools
```

**After**:
```python
from mcp_tools import get_tool_definitions, get_read_only_tools, get_all_tools, get_agent_tools
```

**Reason**: Need access to `get_agent_tools()` to combine with write-enabled MCP tools

---

#### B. Tool Definitions (Line 700)

**File**: `/var/www/ai/aidemo2/agent.py`

**Before**:
```python
tools=get_all_tools(),  # MCP read-only + agent tools
```

**After**:
```python
tools=get_tool_definitions() + get_agent_tools(),  # All MCP tools + agent tools
```

**Reason**: 
- `get_all_tools()` returns only read-only MCP tools + agent tools
- `get_tool_definitions()` returns ALL MCP tools including write operations (create_database, create_table, insert_rows)
- This gives Claude API access to the write tools

---

#### C. System Prompt - Write Operations Section (Lines 306-318)

**File**: `/var/www/ai/aidemo2/agent.py`

**Before**:
```python
CRITICAL GUARDRAILS:
- This MCP connection is READ-ONLY - you CANNOT and MUST NOT attempt to:
  * INSERT, UPDATE, DELETE, or TRUNCATE data
  * CREATE, ALTER, or DROP databases, tables, schemas, or indexes
  * GRANT or REVOKE permissions
  * Modify any cluster configuration or settings
  * Execute any write operations whatsoever

- If a user asks you to modify, update, write to, create, delete, or change anything in the database:
  1. Immediately refuse with: "I cannot perform write operations on the database."
  2. Explain this is a read-only connection for safety
  3. Provide the exact SQL statement they can run themselves with direct database access
  4. Do NOT attempt to call any MCP tools for write operations
```

**After**:
```python
WRITE OPERATIONS:
- You have access to the following write operations via MCP tools:
  * create_database - Create new databases
  * create_table - Create new tables with SQL CREATE TABLE statements
  * insert_rows - Insert rows into existing tables

- IMPORTANT: The user will be prompted to confirm before ANY write operation executes
- When the user requests a write operation:
  1. Use the appropriate MCP tool (create_database, create_table, insert_rows)
  2. The system will ask the user: "Execute this operation? (yes/no)"
  3. The operation only executes if the user confirms with "yes"

- LIMITATIONS - You CANNOT:
  * UPDATE or DELETE existing data
  * DROP or ALTER databases, tables, or schemas
  * GRANT or REVOKE permissions
  * Modify cluster configuration
  * Execute raw DDL/DML beyond the available tools
```

**Reason**: 
- Old prompt explicitly told Claude to refuse all write operations
- New prompt informs Claude that write operations are available and explains the confirmation flow
- Sets clear boundaries on what IS and ISN'T supported

---

#### D. System Prompt - Guidelines Section (Lines 320-324)

**File**: `/var/www/ai/aidemo2/agent.py`

**Before**:
```python
GUIDELINES:
- Execute user requests directly when the intent is clear
- Maintain context across the conversation
- Format results clearly and concisely
- When in doubt about whether something is a write operation, err on the side of refusing
```

**After**:
```python
GUIDELINES:
- Execute user requests directly when the intent is clear
- Maintain context across the conversation
- Format results clearly and concisely
- For write operations (create_database, create_table, insert_rows), use the appropriate tool - the user will confirm before execution
- For operations not supported by the available tools, explain the limitation and provide SQL they can run directly
```

**Reason**: Updated guidance to reflect new write capabilities and confirmation workflow

---

#### E. Safety Confirmation Logic (Lines 771-789)

**File**: `/var/www/ai/aidemo2/agent.py`

**Before**:
```python
else:
    # Execute MCP tool via MCP server
    result = self.mcp_client.execute_tool_call(tool_name, tool_input)
```

**After**:
```python
else:
    # Check if this is a write operation that needs confirmation
    write_tools = {"create_database", "create_table", "insert_rows"}
    if tool_name in write_tools:
        # Ask for user confirmation before executing write operations
        print(f"\n{Colors.WARNING}⚠️  WRITE OPERATION REQUESTED{Colors.ENDC}")
        print(f"{Colors.BOLD}Tool:{Colors.ENDC} {tool_name}")
        print(f"{Colors.BOLD}Input:{Colors.ENDC} {json.dumps(tool_input, indent=2)}")

        confirm = input(f"\n{Colors.BOLD}Execute this operation? (yes/no): {Colors.ENDC}").strip().lower()

        if confirm not in ['yes', 'y']:
            result = json.dumps({
                "error": "Operation cancelled by user",
                "message": "User declined to execute write operation"
            })
            print(f"{Colors.FAIL}✗ Operation cancelled{Colors.ENDC}\n")
        else:
            # Execute MCP tool via MCP server
            result = self.mcp_client.execute_tool_call(tool_name, tool_input)
            print(f"{Colors.OKGREEN}✓ Write operation completed{Colors.ENDC}\n")
    else:
        # Execute read-only MCP tool via MCP server
        result = self.mcp_client.execute_tool_call(tool_name, tool_input)
```

**Reason**: 
- Intercepts write operations before execution
- Shows user exactly what will be executed
- Requires explicit "yes" confirmation
- Provides clear visual feedback with color coding
- If declined, returns error to Claude (who can explain to user)

---

#### F. Documentation Header Updates (Lines 33-40)

**File**: `/var/www/ai/aidemo2/agent.py`

**Before**:
```python
This creates an intelligent agent that can:
    - List databases and tables
    - Execute SELECT queries
    - Analyze schema
    - Run diagnostics
    - Follow CockroachDB best practices from SKILL.md files
    - Get smarter over time by learning which skills help each type of query
```

**After**:
```python
This creates an intelligent agent that can:
    - List databases and tables
    - Execute SELECT queries
    - Analyze schema
    - Run diagnostics
    - Create databases and tables (with user confirmation)
    - Insert rows (with user confirmation)
    - Follow CockroachDB best practices from SKILL.md files
    - Get smarter over time by learning which skills help each type of query
```

**Before (Recent Updates)**:
```python
Recent Updates:
    - 2026-04-05: Added color-coded UI (task in dark blue, skills in dark red)
    - 2026-04-05: Fixed stdout buffering for consistent output order
    - 2026-04-04: Upgraded to 768-dim embeddings (all-mpnet-base-v2)
    - 2026-04-04: Eliminated default skill pre-loading (zero-skill optimization)
```

**After (Recent Updates)**:
```python
Recent Updates:
    - 2026-04-05: Changed write operation warning color to dark orange for better visibility
    - 2026-04-05: Enabled write operations (create_database, create_table, insert_rows) with user confirmation
    - 2026-04-05: Added color-coded UI (task in dark blue, skills in dark red)
    - 2026-04-05: Fixed stdout buffering for consistent output order
    - 2026-04-04: Upgraded to 768-dim embeddings (all-mpnet-base-v2)
    - 2026-04-04: Eliminated default skill pre-loading (zero-skill optimization)
```

**Reason**: Keep documentation current with new capabilities

---

#### G. Color Enhancement for Write Operation Warnings (Lines 72-88, 786)

**File**: `/var/www/ai/aidemo2/agent.py`

**Change 1 - Add Dark Orange Color (Line 79)**:

**Before**:
```python
class Colors:
    """ANSI escape codes for colored terminal output"""
    HEADER = '\033[95m'      # Bright magenta
    OKBLUE = '\033[94m'      # Blue
    OKCYAN = '\033[96m'      # Cyan
    OKGREEN = '\033[92m'     # Green
    WARNING = '\033[93m'     # Yellow
    FAIL = '\033[91m'        # Red
    ENDC = '\033[0m'         # Reset
    BOLD = '\033[1m'         # Bold
    UNDERLINE = '\033[4m'    # Underline
    BG_BLUE = '\033[44m'     # Blue background
    BG_CYAN = '\033[46m'     # Cyan background
    BG_WHITE = '\033[47m'    # White background
    BLACK = '\033[30m'       # Black text (for use with light backgrounds)
```

**After**:
```python
class Colors:
    """ANSI escape codes for colored terminal output"""
    HEADER = '\033[95m'      # Bright magenta
    OKBLUE = '\033[94m'      # Blue
    OKCYAN = '\033[96m'      # Cyan
    OKGREEN = '\033[92m'     # Green
    WARNING = '\033[93m'     # Yellow
    DARK_ORANGE = '\033[38;5;208m'  # Dark orange (for write operation warnings)
    FAIL = '\033[91m'        # Red
    ENDC = '\033[0m'         # Reset
    BOLD = '\033[1m'         # Bold
    UNDERLINE = '\033[4m'    # Underline
    BG_BLUE = '\033[44m'     # Blue background
    BG_CYAN = '\033[46m'     # Cyan background
    BG_WHITE = '\033[47m'    # White background
    BLACK = '\033[30m'       # Black text (for use with light backgrounds)
```

**Change 2 - Use Dark Orange for Write Warnings (Line 786)**:

**Before**:
```python
print(f"\n{Colors.WARNING}⚠️  WRITE OPERATION REQUESTED{Colors.ENDC}")
```

**After**:
```python
print(f"\n{Colors.DARK_ORANGE}⚠️  WRITE OPERATION REQUESTED{Colors.ENDC}")
```

**Reason**: 
- Pale yellow (`Colors.WARNING`) was hard to read in terminal
- Dark orange (`\033[38;5;208m`) provides better contrast and visibility
- Visually distinctive for critical write operation confirmations

---

### 3. Python Cache Cleanup

**What We Did**:
```bash
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
```

**Reason**: Ensure Python loads the updated code, not cached bytecode

---

## Testing

### Test Command:
```bash
cd /var/www/ai/aidemo2
python3 agent.py
```

### Test Input:
```
Task: create a database called timbob
```

### Expected Output:
```
⚠️  WRITE OPERATION REQUESTED
Tool: create_database
Input: {
  "database": "timbob"
}

Execute this operation? (yes/no):
```

### On Confirmation (yes):
```
✓ Write operation completed

Database 'timbob' created successfully!
```

---

## Available Write Operations

### 1. create_database
**Description**: Create a new database in the cluster  
**Tool Input**: `{"database": "database_name"}`  
**Example**: "create a database called myapp"

### 2. create_table
**Description**: Create a new table with a CREATE TABLE statement  
**Tool Input**: `{"database": "database_name", "create_statement": "CREATE TABLE ..."}`  
**Example**: "create a users table in myapp with id and name columns"

### 3. insert_rows
**Description**: Insert rows into an existing table  
**Tool Input**: `{"database": "database_name", "table": "table_name", "rows": [{...}]}`  
**Example**: "insert a row into users with id 1 and name 'Alice'"

---

## Security Considerations

### Multi-Layer Safety:
1. **OAuth Authentication**: User must authenticate and grant write permissions explicitly
2. **User Confirmation**: Every write operation requires interactive "yes/no" confirmation
3. **Limited Scope**: Only create_database, create_table, insert_rows are supported
4. **No Destructive Ops**: Cannot DROP, TRUNCATE, UPDATE, or DELETE
5. **Clear Visibility**: User sees exact operation details before confirming

### Service Account Role Requirements:
- **Cluster Admin** OR **Cluster Operator** role required for write permissions
- Lower roles (e.g., Cluster Developer) only get read access

---

## Troubleshooting

### Issue: "This is a read-only connection"
**Cause**: System prompt still has old READ-ONLY instructions  
**Fix**: Update system prompt sections as shown in Section 2C and 2D above

### Issue: "Operation cancelled by user"
**Cause**: User typed "no" or something other than "yes"/"y"  
**Fix**: Re-run the task and type "yes" when prompted

### Issue: MCP tools not available
**Cause**: Using `get_all_tools()` instead of `get_tool_definitions()`  
**Fix**: Update line 700 as shown in Section 2B above

### Issue: Python still using old code
**Cause**: Cached bytecode  
**Fix**: Clear __pycache__ directories and .pyc files as shown in Section 3

---

## References

- **MCP Server Docs**: https://www.cockroachlabs.com/docs/cockroachcloud/connect-to-the-cockroachdb-cloud-mcp-server
- **Setup Documentation**: `/var/www/ai/aidemo2/COCKROACHDB_SETUP.md`
- **Agent Code**: `/var/www/ai/aidemo2/agent.py`
- **MCP Tools**: `/var/www/ai/aidemo2/mcp_tools.py`

---

## Summary

**What Changed**:
1. ✅ OAuth authentication with write permissions granted
2. ✅ Tool list expanded from read-only to all tools
3. ✅ System prompt updated to allow write operations
4. ✅ Safety confirmation added before execution
5. ✅ Documentation updated

**Result**: Fully functional CockroachDB agent with safe write operations enabled
