# Detailed Code Comments: agent.py

## Architecture Overview

```
User Query
    ↓
Agent._build_system_prompt()
    ├─ Load 3 default skills OR
    └─ Load learned skills (from similar queries)
    ↓
Claude API (Vertex AI)
    ├─ System: Skills context + guardrails
    ├─ Tools: MCP tools + agent tools (fetch_skill, complete_task)
    └─ Messages: User query
    ↓
Tool Use Loop (while True)
    ├─ Claude calls tools (list_databases, fetch_skill, etc.)
    ├─ Agent executes tools
    ├─ Results sent back to Claude
    └─ Loop until complete_task called
    ↓
Display: Answer + Skill Usage Report
    ↓
Store: Query + skills_that_helped
```

## Initialization (__init__)

### Three Modes

**1. Query Learning Mode (CURRENT)**
```python
use_query_learning = True
```
- Stores user queries with embeddings (768-dim, all-mpnet-base-v2)
- Finds similar past queries using cosine similarity
- Loads only needed skills dynamically
- Uses sentence-transformers for embeddings (upgraded 2026-04-04)

**2. Vector Search Mode (ALTERNATIVE)**
```python
use_vector_search = True
```
- Stores SKILL.md files with embeddings
- Searches skills (not queries)
- Requires Vertex AI permissions

**3. Legacy Mode (FALLBACK)**
```python
use_query_learning = False
use_vector_search = False
```
- Loads ALL 25 skills into context
- No learning, no optimization
- Uses ~50k tokens per request

### Claude API Setup

**Vertex AI vs Standard Anthropic API:**
```python
if use_vertex_ai:
    self.claude = AnthropicVertex(
        project_id="vertex-model-runners",
        region="global"
    )
    # Model name: "claude-sonnet-4-6"
else:
    self.claude = Anthropic(api_key=...)
    # Model name: "claude-sonnet-4-20250514"
```

**Why Vertex AI?**
- Same Claude models, different billing
- Integrated with GCP quotas
- Region can be "global" for Claude (unlike embeddings)

## System Prompt Construction

### `_build_system_prompt(user_task)`

**The Decision Tree:**
```
if query_learning AND user_task:
    recommendation = query_store.get_skills_for_query(user_task)
    if recommendation['source'] == 'learned':
        Load skills from similar query ✓
    else:
        Load 3 default skills
elif vector_search AND user_task:
    Search skills table for relevant skills
else:
    Load all 25 skills (legacy)
```

### Critical Guardrails

**Write Operations with Safety (Updated 2026-04-05):**
```
WRITE OPERATIONS:
- You have access to: create_database, create_table, insert_rows
- User will be prompted to confirm BEFORE execution
- Show exact operation details to user
- NOT SUPPORTED: UPDATE, DELETE, DROP, ALTER, GRANT
```

**Safety Confirmation Layer:**
- Every write operation requires explicit user approval
- Dark orange warning displayed (high visibility)
- Shows exact tool name and parameters
- User can cancel by typing "no"
- Prevents accidental data modifications

**Why this approach?**
- Enables useful write operations (create databases/tables)
- Maintains safety through user confirmation
- Prevents destructive operations (no DELETE/DROP)
- User always has final say

### Skill Learning Instructions

```
When you complete a task, call complete_task with:
1. skills_that_helped: ONLY skills you actually referenced
2. answer: FULL response (not a summary!)
```

**Key Word: "ONLY"**
- Claude must not claim credit for unused skills
- If 3 skills loaded but 1 used → report 1, not 3
- Prevents polluting the learning database

## Tool Use Loop (`run_task`)

### Tracking Skills

```python
self._loaded_skills = set()  # Skills in context
```

**Updated in two places:**
1. `_build_system_prompt()` - tracks pre-loaded skills
2. `_handle_fetch_skill()` - tracks dynamically fetched skills

**Used in:**
- `_handle_complete_task()` - compares loaded vs used

### The Loop

```python
while True:
    response = claude.messages.create(...)

    if stop_reason == "end_turn":
        # Claude finished without calling complete_task
        # (Happens when query fails or is incomplete)
        return final_text

    elif stop_reason == "tool_use":
        # Claude wants to call a tool
        for tool_call in response.content:
            if tool_name == "fetch_skill":
                # Load additional skill into context
            elif tool_name == "complete_task":
                # Task done! Store learning and return
                return answer
            else:
                # Execute MCP tool (list_databases, etc.)
```

**Why a loop?**
- Claude calls tool → sees result → decides next action
- Might chain multiple tools: list_databases → select_query → complete_task
- Loop until Claude says "I'm done" (complete_task)

## Agent Tools

### `fetch_skill(skill_name)`

**Flow:**
```
Claude: "I need replication info"
    ↓
Call: fetch_skill("data-security/replication-configuration")
    ↓
Agent: Loads skill from SkillFetcher
    ↓
Returns: Full SKILL.md content
    ↓
Claude: Now has replication knowledge
```

**Tracking:**
```python
self._loaded_skills.add(skill_name)
```
- Remembers this skill was loaded
- Used later in skill usage report

### `complete_task(skills_that_helped, answer)`

**Two Critical Functions:**

**1. Display Skill Usage Report**
```
✓ Skills that helped:
  • skill-a
  • skill-b

✗ Skills loaded but not used:
  • default-1
  • default-2
```

**2. Store Learning**
```python
query_store.store_query(
    query_text=user_task,
    skills_used=skills_that_helped,  # ONLY the useful ones!
    was_successful=True,
    execution_time_ms=...
)
```

**Why separate loaded vs used?**
- Shows user what worked vs what didn't
- Only stores useful skills (cleaner learning)
- Helps debug: "Why did it load skill X?"

## Write Operation Handling (Added 2026-04-05)

### Safety Confirmation Flow

**When Claude requests a write operation:**
```python
if tool_name in ['create_database', 'create_table', 'insert_rows']:
    # 1. Display warning in dark orange
    print(f"{Colors.DARK_ORANGE}⚠️  WRITE OPERATION REQUESTED{Colors.ENDC}")
    print(f"Tool: {tool_name}")
    print(f"Input: {json.dumps(tool_input, indent=2)}")
    
    # 2. Ask for user confirmation
    confirmation = input("\nExecute this operation? (yes/no): ").strip().lower()
    
    # 3. Execute or cancel based on response
    if confirmation == 'yes':
        result = mcp_client.execute_tool_call(tool_name, tool_input)
        print(f"{Colors.OKGREEN}✓ Write operation completed{Colors.ENDC}")
    else:
        result = "Operation cancelled by user"
```

**Key Design Decisions:**

1. **Dark Orange Warning** - High visibility color for critical operations
2. **Show Full Details** - User sees exact tool name and all parameters
3. **Interactive Prompt** - Requires explicit "yes" to proceed
4. **Clear Feedback** - Shows success or cancellation message

**Operations Supported:**
- `create_database` - Create new databases
- `create_table` - Create tables with SQL DDL
- `insert_rows` - Insert data into tables

**Operations NOT Supported:**
- UPDATE, DELETE, DROP, ALTER, GRANT (too risky)

### OAuth Authentication

**Required for write operations:**
```json
{
  "cockroachdb-cloud": {
    "type": "http",
    "url": "https://cockroachlabs.cloud/mcp",
    "headers": {
      "mcp-cluster-id": "your-cluster-id"
    }
  }
}
```

**Authentication Flow:**
1. Run `/mcp` command in Claude Code
2. Browser opens → Login to CockroachDB Cloud
3. Grant read + write permissions
4. OAuth session established
5. Agent can now execute write operations (with user confirmation)

**Why OAuth over API Key?**
- More secure (short-lived tokens)
- Explicit permission grants
- User controls access level
- Can revoke without changing API keys

## Skill Loading Strategies

### Default Skills (Cold Start - Zero-Preloading Optimization)

**Updated 2026-04-04:**
```python
def _get_default_skills():
    return []  # Zero skills pre-loaded!
```

**Previous Approach (Before 2026-04-04):**
- Pre-loaded 3 default skills for every query
- Skills: reviewing-cluster-health, cockroachdb-sql, triaging-live-sql-activity
- Wasted ~8KB tokens on simple queries that didn't need skills

**Current Approach (Zero-Preloading):**
- Start with 0 pre-loaded skills
- Claude uses `fetch_skill` tool only when needed
- Simple queries (e.g., "how many databases?") use just MCP tools
- Complex queries fetch specific skills on-demand

**Benefits:**
- Token savings: ~30-40% on typical query mix
- Cleaner learning: Only store skills that actually helped
- Better accuracy: No false positives in skill usage tracking

### Learned Skills (Warm Start)
```python
if recommendation['source'] == 'learned':
    skills_to_load = recommendation['skills']
    print(f"Matched: '{recommendation['matched_query']}'")
    print(f"Similarity: {recommendation['similarity']:.2f}")
```

**The Magic:**
- User asks "How do I set up replication?"
- Finds similar: "Configure replication for cluster?" (0.78 similarity)
- Loads: ["replication-configuration", "cluster-topology"]
- No trial-and-error needed!

## Error Handling & Edge Cases

### MCP Tool Failures
```python
result = mcp_client.execute_tool_call(tool_name, tool_input)
# If error: result contains error message
# Claude sees error and can retry or explain to user
```

**No exceptions raised** - errors are returned as data
- Allows Claude to handle gracefully
- Can say "The database is unavailable" instead of crashing

### Empty Skill Recommendations
```python
skills = recommendation.get('skills', [])
if not skills:
    # Load defaults as fallback
```

**When this happens:**
- New type of query (no similar matches)
- Threshold too high (no matches above 0.3)
- Database empty (first query ever)

### Stopped Tool Loop
If user interrupts (Ctrl+C) during tool loop:
- Partial results returned
- Query NOT stored (wasn't successful)
- Safe - no corruption

## Performance Optimizations

### Lazy Skill Loading
```python
# DON'T load all 25 skills at startup
self.skill_fetcher = SkillFetcher()
skill_fetcher.load_from_database()  # Only loads on first use
```

**Why lazy?**
- Faster startup (0.1s vs 2s)
- May not need skills if defaults work
- Database query is fast anyway

### Connection Pooling (Future)
Currently: New psycopg2 connection per query
Future: Connection pool for better performance

```python
# TODO: Use connection pooling
from psycopg2 import pool
self.db_pool = pool.SimpleConnectionPool(1, 10, connection_string)
```

## Debugging Tips

### Verbose Mode
```python
agent = CockroachDBAgent()
agent.verbose = True  # Prints all decisions
```

Shows:
- Which skills were loaded
- Why (learned vs default)
- Tool calls in detail
- Execution times

### Check Learning Database
```sql
SELECT query_text, skills_used, 
       1 - (query_embedding <-> %s::vector) as similarity
FROM query_history
ORDER BY created_at DESC
LIMIT 10;
```

See what the system has learned!
