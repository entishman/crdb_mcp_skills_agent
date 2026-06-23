# AIdemo2 - Complete Architecture Documentation

## System Overview

**What it does:** An intelligent CockroachDB assistant that learns from every interaction.

**How it works:** 
1. User asks a question in natural language
2. System finds similar past questions using AI embeddings
3. Loads only the relevant documentation (SKILL.md files)
4. Claude (LLM) answers using MCP tools to query the database
5. Stores which skills helped for future similar questions
6. Gets smarter over time!

## Component Map

```
┌─────────────┐
│    User     │
└──────┬──────┘
       │ Natural language query
       ↓
┌─────────────────────────────────────────┐
│         agent.py (Orchestrator)         │
│  ┌────────────────────────────────┐    │
│  │ 1. Generate query embedding    │    │
│  │ 2. Find similar past queries   │    │
│  │ 3. Load relevant skills        │    │
│  │ 4. Call Claude API             │    │
│  │ 5. Execute tools               │    │
│  │ 6. Store learning              │    │
│  └────────────────────────────────┘    │
└────┬──────────────┬───────────┬────────┘
     │              │           │
     │              │           │
┌────▼─────┐   ┌───▼──────┐  ┌▼─────────┐
│ Query    │   │  Skill   │  │   MCP    │
│ Store    │   │ Fetcher  │  │  Client  │
└────┬─────┘   └───┬──────┘  └──┬───────┘
     │             │             │
┌────▼────────┐  ┌▼─────────┐  ┌▼────────┐
│ CockroachDB │  │ CockroachDB│  │  MCP   │
│ ai_demo.    │  │ ai_demo.   │  │ Server │
│ query_      │  │ skills     │  └──┬─────┘
│ history     │  └────────────┘     │
└─────────────┘                ┌────▼──────┐
                               │CockroachDB│
                               │  Cluster  │
                               └───────────┘
```

## Data Flow: Example Query

**User:** "Are there any hotspots in testdb?"

### Step 1: Embedding Generation
```
"Are there any hotspots in testdb?"
    ↓
[ollama_embedding_manager.py]
    ↓
SentenceTransformer(all-mpnet-base-v2)
    ↓
[0.23, 0.89, -0.41, ...] (768 dimensions)
```

### Step 2: Similarity Search
```
[query_store.py]
    ↓
SQL: SELECT * FROM query_history
     WHERE 1 - (embedding <-> query_embedding) >= 0.3
     ORDER BY embedding <-> query_embedding
     LIMIT 1
    ↓
Match: "Check for hot ranges in testdb" (similarity: 0.53)
Skills: ["observability-and-diagnostics/analyzing-range-distribution"]
```

### Step 3: Load Skills
```
[skill_fetcher.py]
    ↓
1. Try: ai_demo.skills table (DATABASE)
2. Fallback: .cache/ directory (LOCAL)
3. Fallback: GitHub API (REMOTE)
    ↓
Returns: Full SKILL.md content
```

### Step 4: Call Claude
```
[agent.py]
    ↓
System Prompt:
  - Base instructions + guardrails
  - Loaded skill: analyzing-range-distribution
  - Available tools: MCP + agent tools
    ↓
Claude API (Vertex AI, region: global)
    ↓
Model: claude-sonnet-4-6
```

### Step 5: Tool Execution Loop
```
Claude: "I need to see the ranges"
    ↓
Tool Call: select_query(
    database="testdb",
    query="SHOW RANGES FROM TABLE t1"
)
    ↓
[mcp_client.py] → MCP Server → CockroachDB
    ↓
Result: [range data...]
    ↓
Back to Claude
    ↓
Claude: "I can answer now"
    ↓
Tool Call: complete_task(
    skills_that_helped=["analyzing-range-distribution"],
    answer="Here are the hotspots..."
)
```

### Step 6: Store Learning
```
[query_store.py]
    ↓
INSERT INTO query_history (
    query_text,
    query_embedding,
    skills_used,
    was_successful,
    execution_time_ms
) VALUES (
    'Are there any hotspots in testdb?',
    [0.23, 0.89, ...],
    ['analyzing-range-distribution'],
    true,
    8500
)
```

## Database Schema

### ai_demo.query_history
```sql
CREATE TABLE query_history (
    query_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_text TEXT UNIQUE,                    -- The user's question
    query_embedding VECTOR(768),               -- Semantic embedding (768-dim, upgraded 2026-04-04)
    skills_used TEXT[],                        -- Which SKILL.md files helped
    was_successful BOOLEAN DEFAULT true,       -- Did we answer it?
    response_quality INT CHECK (...),          -- Optional 1-5 rating
    execution_time_ms INT,                     -- How long it took
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- HNSW index for fast similarity search
CREATE INDEX idx_query_embedding 
ON query_history USING hnsw (query_embedding vector_cosine_ops);
```

**Why HNSW?**
- Brute force: O(n) - compare to every query
- HNSW: O(log n) - graph-based approximate nearest neighbor
- For 1000 queries: 1000x faster, 99% accuracy

### ai_demo.skills
```sql
CREATE TABLE skills (
    skill_name TEXT PRIMARY KEY,               -- e.g., "operations/reviewing-cluster-health"
    category TEXT,                             -- e.g., "operations-and-lifecycle"
    short_name TEXT,                           -- e.g., "reviewing-cluster-health"
    content TEXT,                              -- Full SKILL.md markdown
    embedding VECTOR(768),                     -- 768-dim (NULL in query-learning mode)
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Why store skills in DB?**
- Persistent across restarts
- Shared by multiple agent instances
- Faster than reading 25 files from disk
- Single source of truth

## Technology Stack

### Core
- **Python 3.12** - Main language
- **Claude Sonnet 4.6** - LLM (via Vertex AI)
- **CockroachDB** - Database (with pgvector)
- **sentence-transformers** - Embeddings (all-mpnet-base-v2, 768-dim)

### Key Libraries
- **anthropic[vertex]** - Claude API client
- **psycopg2** - PostgreSQL/CockroachDB driver
- **sentence-transformers** - Embedding generation
- **httpx** - HTTP client for MCP/GitHub
- **numpy** - Vector operations

### External Services
- **Vertex AI** - Claude API (region: global)
- **MCP Server** - CockroachDB operations (cockroachlabs.cloud/mcp)
- **GitHub** - SKILL.md file repository

## Configuration (config.json)

```json
{
  "mcp_server_url": "https://cockroachlabs.cloud/mcp",
  "cluster_id": "...",
  "api_key": "...",
  
  "use_vertex_ai": true,
  "vertex_ai_project": "vertex-model-runners",
  "vertex_ai_region": "global",
  
  "use_query_learning": true,
  "database_connection_string": "postgresql://..."
}
```

### Mode Selection

**Query Learning (RECOMMENDED):**
```json
"use_query_learning": true,
"use_vector_search": false
```
- Stores user queries (not skills)
- Uses sentence-transformers locally
- No Vertex AI permissions needed
- 0.3 similarity threshold

**Vector Search (ALTERNATIVE):**
```json
"use_query_learning": false,
"use_vector_search": true
```
- Stores skill embeddings
- Requires Vertex AI for embeddings
- Searches skills, not queries

**Legacy Mode (FALLBACK):**
```json
"use_query_learning": false,
"use_vector_search": false
```
- Loads all 25 skills every time
- No learning, no optimization
- Uses ~50k tokens per request

## MCP (Model Context Protocol)

### What is MCP?
Protocol for LLMs to interact with external systems (like databases).

### Architecture
```
Claude → Agent → MCP Client → HTTP POST → MCP Server → CockroachDB
                                   ↓ SSE (streaming)
                                 Results
```

### Available Tools (MCP)
1. **list_databases** - SHOW DATABASES
2. **list_tables** - SHOW TABLES FROM db
3. **get_table_schema** - SHOW CREATE TABLE
4. **select_query** - Execute SELECT (read-only)
5. **explain_query** - EXPLAIN query plan
6. **list_running_queries** - SHOW QUERIES
7. **get_cluster** - Cluster metadata
8. **list_clusters** - All clusters

### Available Tools (Agent)
1. **fetch_skill** - Load additional SKILL.md
2. **complete_task** - Mark task done + store learning

### Read-Only Enforcement
```
if tool_name in ['create_database', 'insert_rows', 'update_rows']:
    return "CANNOT EXECUTE - READ-ONLY CONNECTION"
```

**Why?**
- Safety: Prevents accidental data loss
- MCP server is configured read-only anyway
- User might casually say "delete old data"

## Learning System Details

### Similarity Threshold: 0.3

**Why 0.3?**
```
Threshold | Behavior
----------|----------
0.7+      | Only near-exact matches (too strict)
0.5       | Moderate matches (good for production embeddings)
0.3       | Lenient matches (good for sentence-transformers)
0.1       | Too lenient (false positives)
```

With sentence-transformers:
- "hotspots" vs "hot ranges" = 0.53 ✓ (above 0.3)
- "database" vs "unrelated topic" = 0.05 ✗ (below 0.3)

### Cold Start Problem

**First Query Ever (Optimized 2026-04-04):**
```
No similar queries found
  ↓
Load 0 default skills (zero-preloading optimization)
  ↓
Claude fetches only what it needs via fetch_skill tool
  ↓
Stores: query → skills that actually helped
```

**Second Similar Query:**
```
Found similar query (0.45 similarity)
  ↓
Pre-load learned skills (only proven-helpful ones)
  ↓
Answer immediately!
```

**Progressive Learning:**
- Query 1-10: Mostly cold starts (fetch on-demand)
- Query 11-50: Starting to learn (pre-loading proven skills)
- Query 50+: Most queries have matches (efficient pre-loading)

**Benefit of Zero-Preloading:**
- Simple queries: ~30-40% token savings (no wasted skills)
- Complex queries: Only load what's needed (smart on-demand)
- Learning accuracy: Only store skills that actually helped

## Performance Metrics

### Typical Query Flow
```
Embedding generation:        50ms
Similarity search (HNSW):     5ms
Skill loading (from DB):     20ms
Claude API call:           2000ms
MCP tool execution:         100ms
Store learning:              10ms
────────────────────────────────
TOTAL:                    ~2200ms
```

### Token Usage

**Query Learning Mode:**
- System prompt: ~2k tokens (3 skills)
- User query: ~50 tokens
- MCP results: ~500 tokens
- Total: ~2.5k tokens/query

**Legacy Mode:**
- System prompt: ~50k tokens (25 skills!)
- Everything else: same
- Total: ~50k tokens/query
- **20x more expensive!**

### Database Storage

**Per query:**
- query_text: ~100 bytes
- query_embedding: 768 floats × 4 bytes = 3,072 bytes (upgraded 2026-04-04)
- skills_used: ~100 bytes
- Total: ~3.3 KB/query

**1000 queries = ~3.3 MB** (still tiny!)

## Deployment Considerations

### Disk Space
- sentence-transformers model: 92 MB
- Python packages: ~200 MB
- CockroachDB data: ~2 MB
- Logs/cache: ~50 MB
- **Total: ~350 MB needed**

Current system: 30GB disk, 98% full (923 MB available) ✓

### Memory
- sentence-transformers model: ~200 MB RAM
- Agent + dependencies: ~100 MB RAM
- **Total: ~300 MB RAM needed**

### Scaling

**Single Instance:**
- Can handle ~10 concurrent queries
- Claude API is the bottleneck (2s/query)
- Database is fast enough

**Multiple Instances:**
- Share same ai_demo.skills table ✓
- Share same ai_demo.query_history table ✓
- Each has own sentence-transformers model
- Learning compounds across all instances!

## User Experience & Demo Presentation

### Color-Coded Output (Added 2026-04-05)

**Enhanced visual clarity for professional demos and better user experience.**

#### Task Display (Dark Blue)
```
================================================================================
================================================================================
>>> TASK: how many databases are there?
================================================================================
================================================================================
```

**Features:**
- Bold dark blue color (ANSI escape code: `\033[1m\033[34m`)
- Double-line separators for prominence
- >>> arrows for clear indication
- Displayed before skill report and answer

**Purpose:**
- Makes user questions immediately visible
- Clear separation from agent output
- Professional demo appearance
- Works in both interactive and command-line modes

#### Skill Usage Report (Dark Red)
```
================================================================================
SKILL USAGE REPORT
================================================================================
✓ Skills that helped complete this task:
  • query-and-schema-design/cockroachdb-sql
  
✗ Skills that were loaded but not used:
  (rarely appears with zero-skill-preloading)
================================================================================
```

**Features:**
- Dark red color (ANSI escape code: `\033[31m`)
- Shows skills that helped (what Claude used)
- Shows skills loaded but unused (tracks accuracy)
- Displayed after task, before answer

**Purpose:**
- Shows learning system in action
- Demonstrates Claude's skill selection
- Tracks efficiency (unused skills indicate waste)
- Educational value for viewers

#### Output Flow
```
[Dark Blue]    Task: User's question
[Dark Red]     Skill Usage Report
[Default]      Answer from Claude
```

**Benefits:**
1. **Visual Hierarchy** - Clear progression from question to analysis to answer
2. **Professional** - Polished appearance for demos and presentations
3. **Educational** - Shows system internals (which skills were chosen)
4. **Debugging** - Easy to spot if wrong skills are being selected
5. **Consistent** - Fixed stdout buffering ensures correct order every time

#### Implementation Details

**Function:** `print_task_header(task_text)`
- Location: `agent.py`
- Called from: `main()` and `interactive_mode()`

**Skill Report Coloring:**
- Location: `_handle_complete_task()` in `agent.py`
- Includes: `sys.stdout.flush()` to prevent buffering issues

#### Terminal Compatibility

**Works in:**
- ✅ macOS Terminal
- ✅ Linux terminals (bash, zsh)
- ✅ Windows Terminal
- ✅ VS Code integrated terminal
- ✅ Most modern terminal emulators

**Graceful Degradation:**
- If ANSI colors not supported, escape codes appear as `[1m[34m` but text remains readable
- All functionality works regardless of color support

**See also:** `UI_IMPROVEMENTS_2026-04-05.md` for detailed documentation

## Future Improvements

### ~~Higher Quality Embeddings~~ ✅ COMPLETED (2026-04-04)
```python
# Old: all-MiniLM-L6-v2 (384-dim, 90MB)
# Current: all-mpnet-base-v2 (768-dim, 420MB) ✅

embedding_manager = OllamaEmbeddingManager(
    model_name="all-mpnet-base-v2",
    embedding_dim=768
)
```

**Status:** ✅ Implemented! Standardized on 768 dimensions across all vector columns.
**Next step:** Could consider nomic-embed-text for even better retrieval quality.

### Connection Pooling
```python
from psycopg2 import pool
self.db_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    dsn=connection_string
)
```

**Benefit:** Reuse connections, ~50% faster

### Caching
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_skills_for_query(query_text):
    # Cache skill lookups
```

**Benefit:** Instant repeat queries

### Metrics Dashboard
```python
# Track in real-time:
- Queries/hour
- Average similarity scores
- Most-used skills
- Learning effectiveness
```

## Troubleshooting Guide

### "No similar queries found"
- **Cause:** First time asking this type of question
- **Fix:** Normal! System will learn after this query

### "Skill not found"
- **Cause:** Claude asked for non-existent skill
- **Fix:** Run `python utilities/populate_skills_db.py`

### "Read-only connection" error
- **Cause:** User asked for write operation
- **Fix:** Intentional! Provide SQL for them to run manually

### High token usage
- **Cause:** Using legacy mode
- **Fix:** Enable query_learning in config.json

### Slow startup
- **Cause:** Loading sentence-transformers model
- **Fix:** Normal (3-5s). Model cached after first load

### Database connection failed
- **Cause:** Invalid connection string or network issue
- **Fix:** Check config.json, verify CockroachDB accessible

## Security Notes

### API Keys in config.json
```json
{
  "api_key": "CCDB1_..."  // CockroachDB API key
}
```
⚠️ **Never commit config.json to git!**
Add to .gitignore

### Database Credentials
```
postgresql://user:password@host:26257/...
```
⚠️ **Use environment variables in production:**
```python
conn_str = os.getenv('COCKROACH_CONNECTION_STRING')
```

### MCP Server Security
- Read-only access enforced server-side
- Agent double-checks (defense in depth)
- No raw SQL execution (only predefined tools)

## Success Metrics

### System is Working If:
✓ Queries are stored with embeddings
✓ Similar queries get similarity > 0.3
✓ Skill usage report shows accurate skills
✓ Response time < 5 seconds
✓ Learning database growing over time

### System Needs Attention If:
✗ No skills are ever fetched (Claude not using fetch_skill)
✗ Similarity always < 0.3 (threshold too high? or queries too diverse)
✗ Many skills loaded but unused (check pre-loading logic)
✗ Response time > 10 seconds (check API latency)
✗ Database errors (check connection string)

Enjoy your beer! 🍺 The system is well-documented now!
