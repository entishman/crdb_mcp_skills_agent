# Vector Search for Skills - Setup Guide

> **📌 NOTE: Alternative Operating Mode**  
> This guide describes **Vector Search Mode**, an alternative to the currently active **Query Learning Mode**.
> 
> **Current Mode (Default):** Query Learning Mode - Stores user queries, learns from experience  
> **This Guide:** Vector Search Mode - Stores SKILL.md files, searches skills semantically
> 
> The current system uses Query Learning with zero-skill-preloading optimization (2026-04-04).  
> Vector Search is a valid alternative if you prefer to search skills directly rather than learn from queries.
> 
> See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed mode comparison.

---

This guide explains how to enable vector search for CockroachDB skills, which dramatically improves the agent's performance.

## Why Vector Search?

### Problem with Current Approach:
- Loads all 25 SKILL.md files (~50k tokens) into every Claude API call
- Wastes context window space
- Causes the agent to "forget" recent conversation
- Slower and more expensive

### Solution with Vector Search:
- Finds only the 3 most relevant skills per query (~5k tokens)
- **90% reduction in token usage**
- Better context retention (more room for conversation history)
- Faster responses
- Smarter recommendations (semantic understanding)

## Architecture

```
User Query: "How do I check cluster health?"
    ↓
Generate Embedding (768-dim vector via Vertex AI)
    ↓
Search CockroachDB for Similar Skills (cosine similarity)
    ↓
Return Top 3 Relevant Skills
    ↓
Send ONLY those 3 to Claude (not all 25!)
```

## Setup Instructions

### Step 1: Get Database Connection String

1. Go to [CockroachDB Cloud Console](https://cockroachlabs.cloud)
2. Select your cluster (e.g., `trs-demo`)
3. Click **"Connect"**
4. Choose **"General connection string"**
5. Copy the connection string

Example format:
```
postgresql://user:password@host:26257/defaultdb?sslmode=verify-full&sslrootcert=path/to/ca.crt
```

### Step 2: Update Config

Edit `config.json`:

```json
{
  "mcp_server_url": "https://cockroachlabs.cloud/mcp",
  "cluster_id": "your-cluster-id",
  "auth_method": "api_key",
  "api_key": "your-api-key",
  "use_vertex_ai": true,
  "vertex_ai_project": "vertex-model-runners",
  "vertex_ai_region": "global",
  
  "use_vector_search": true,
  "database_connection_string": "postgresql://..."
}
```

**Important:**
- Set `use_vector_search: true`
- Add your `database_connection_string`

### Step 3: Index Skills into CockroachDB

Run the indexing script:

```bash
python3 utilities/index_skills.py
```

Or provide the connection string directly:

```bash
python3 utilities/index_skills.py "postgresql://user:password@host:26257/defaultdb"
```

This script will:
1. ✓ Load all 25 SKILL.md files
2. ✓ Generate embeddings using Vertex AI
3. ✓ Create `skills` table in CockroachDB
4. ✓ Store skills + embeddings
5. ✓ Test semantic search

**Expected output:**
```
Step 1: Loading Skills
✓ Loaded 25 skills from cache

Step 2: Creating Database Table
✓ Skills table created with vector support

Step 3: Generating Embeddings
Generating embeddings for 25 skills...
✓ Generated 25 embeddings (768 dimensions)

Step 4: Storing in CockroachDB
✓ Inserted 25 skills into vector store

Step 5: Testing Semantic Search
Top 3 relevant skills:
1. operations-and-lifecycle/reviewing-cluster-health (similarity: 0.847)
2. observability-and-diagnostics/monitoring-background-jobs (similarity: 0.782)
3. operations-and-lifecycle/managing-cluster-capacity (similarity: 0.731)
```

### Step 4: Run the Agent

```bash
python3 agent.py
```

The agent will now use vector search automatically!

## How It Works

### Database Schema

```sql
CREATE TABLE skills (
    skill_name TEXT PRIMARY KEY,              -- e.g., "operations-and-lifecycle/reviewing-cluster-health"
    category TEXT NOT NULL,                   -- e.g., "operations-and-lifecycle"
    short_name TEXT NOT NULL,                 -- e.g., "reviewing-cluster-health"
    content TEXT NOT NULL,                    -- Full SKILL.md content
    embedding VECTOR(768),                    -- Vertex AI embedding (768 dimensions)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vector index for fast similarity search
CREATE INDEX idx_skills_embedding
ON skills USING hnsw (embedding vector_cosine_ops);
```

### Semantic Search Query

```sql
-- Find top 3 skills similar to user's question
SELECT skill_name, content, 
       1 - (embedding <-> query_embedding) AS similarity
FROM skills
ORDER BY embedding <-> query_embedding
LIMIT 3;
```

The `<->` operator computes cosine distance. Closer to 0 = more similar.

### Embedding Model

- **Model:** `text-embedding-004` (Vertex AI)
- **Dimensions:** 768
- **Provider:** Google Cloud Vertex AI
- **Cost:** ~$0.025 per 1M tokens

## Testing

### Test Vector Search Manually

```bash
python3 skills_vectorstore.py
```

### Test Embedding Generation

```bash
python3 embedding_manager.py
```

### Test Full Integration

```bash
python3 agent.py "How do I check cluster health?"
```

Expected behavior:
- Agent finds "reviewing-cluster-health" skill
- Uses it to answer your question
- Does NOT load all 25 skills

## Performance Comparison

| Metric | Without Vector Search | With Vector Search |
|--------|----------------------|-------------------|
| **Tokens per query** | ~50,000 | ~5,000 |
| **Token reduction** | 0% | **90%** |
| **Context for conversation** | ~150k tokens | ~195k tokens |
| **Skills sent to Claude** | All 25 | Top 3 relevant |
| **Response time** | Slower | **Faster** |
| **Cost per query** | Higher | **Lower** |
| **Accuracy** | All skills (noisy) | **Relevant skills** |

## Troubleshooting

### Error: "pgvector extension not available"

CockroachDB supports pgvector natively in v23.2+. Make sure your cluster is updated.

### Error: "database_connection_string not in config"

Add the connection string to `config.json`:
```json
"database_connection_string": "postgresql://..."
```

### Error: "Vertex AI quota exceeded"

Embedding generation hits Vertex AI rate limits. The script includes 1-second delays between batches. If you still hit limits, reduce batch size in `utilities/index_skills.py`.

### Search returns no results

Run the indexing script again:
```bash
python3 utilities/index_skills.py
```

Check that skills are in the database:
```sql
SELECT COUNT(*) FROM skills;  -- Should return 25
```

### Agent still slow

Verify vector search is enabled:
```bash
python3 -c "
import json
with open('config.json') as f:
    config = json.load(f)
    print(f'Vector search enabled: {config.get(\"use_vector_search\", False)}')
"
```

Should print: `Vector search enabled: True`

## Legacy Mode (No Vector Search)

To disable vector search and use the old approach:

In `config.json`:
```json
{
  "use_vector_search": false
}
```

The agent will fall back to loading all 25 skills.

## Maintenance

### Re-index Skills

If skills are updated on GitHub:

```bash
# Clear cache
rm -rf .cache/

# Re-fetch and re-index
python3 utilities/index_skills.py
```

### View Indexed Skills

```bash
python3 -c "
from skills_vectorstore import SkillsVectorStore
import json

with open('config.json') as f:
    config = json.load(f)

store = SkillsVectorStore(config['database_connection_string'])
skills = store.get_all_skills()

for skill in skills:
    print(f'- {skill[\"skill_name\"]}')
"
```

### Clear Vector Store

```bash
python3 -c "
from skills_vectorstore import SkillsVectorStore
import json

with open('config.json') as f:
    config = json.load(f)

store = SkillsVectorStore(config['database_connection_string'])
store.drop_table()
print('✓ Skills table dropped')
"
```

Then re-run `python3 utilities/index_skills.py` to rebuild.

## Next Steps

1. ✅ Enable vector search
2. ✅ Index all skills
3. ✅ Run the agent
4. 🎉 Enjoy 90% faster, smarter responses!

For questions or issues, see the main [README.md](README.md).
