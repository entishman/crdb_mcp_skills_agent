# Quick Start: Enable Vector Search

> **📌 NOTE: Alternative Operating Mode**  
> This guide describes **Vector Search Mode**, an alternative to the currently active **Query Learning Mode**.
> 
> **Current Mode (Default):** Query Learning - Stores user queries with embeddings, learns from past questions  
> **This Guide:** Vector Search - Stores SKILL.md files with embeddings, searches skills directly
> 
> Both modes work well. Vector Search requires Vertex AI permissions for embeddings.  
> Query Learning uses local sentence-transformers (no cloud dependencies).
> 
> See [ARCHITECTURE.md](ARCHITECTURE.md) for mode comparison.

---

## ✨ What You'll Get

- **90% reduction** in tokens sent to Claude
- **Better conversation memory** - agent remembers more context
- **Smarter recommendations** - finds only relevant skills
- **Faster responses**
- **Lower costs**

## 🚀 Setup (5 minutes)

### Step 1: Set Quota Project

```bash
gcloud auth application-default set-quota-project vertex-model-runners
```

This fixes the "quota project" error when generating embeddings.

### Step 2: Get Database Connection String

1. Go to https://cockroachlabs.cloud
2. Click your cluster (`trs-demo`)
3. Click **"Connect"** → **"Connection string"**
4. Copy it (looks like: `postgresql://user:pass@host:26257/defaultdb?...`)

### Step 3: Run Indexing Script

```bash
python3 utilities/index_skills.py
```

When prompted, paste your connection string.

**This will:**
- ✓ Load all 25 SKILL.md files
- ✓ Generate embeddings via Vertex AI (takes ~2 min)
- ✓ Create `skills` table in CockroachDB
- ✓ Store embeddings for semantic search
- ✓ Test that search works

### Step 4: Enable in Config

Edit `config.json`:

```json
{
  ...
  "use_vector_search": true,
  "database_connection_string": "postgresql://..."
}
```

### Step 5: Run Agent

```bash
python3 agent.py
```

Ask: **"How do I check cluster health?"**

The agent will now:
1. Generate embedding for your question
2. Search CockroachDB for top 3 relevant skills
3. Send ONLY those 3 to Claude (not all 25!)

## 📊 Before vs After

### Before (No Vector Search):
```
User: "How do I check cluster health?"
  ↓
Agent loads ALL 25 skills (~50k tokens)
  ↓
Claude gets overwhelmed with info
  ↓
Forgets recent conversation
```

### After (With Vector Search):
```
User: "How do I check cluster health?"
  ↓
Generate embedding → Search CockroachDB
  ↓
Find 3 relevant skills (~5k tokens):
  - reviewing-cluster-health (0.89 similarity)
  - monitoring-background-jobs (0.82 similarity)
  - managing-cluster-capacity (0.78 similarity)
  ↓
Claude gets focused, relevant info
  ↓
Better answers, remembers conversation
```

## 🔧 Troubleshooting

### "quota project" error
```bash
gcloud auth application-default set-quota-project vertex-model-runners
```

### "database_connection_string not in config"
Add it to `config.json`:
```json
"database_connection_string": "postgresql://..."
```

### "Permission denied" on Vertex AI
Make sure you're authenticated:
```bash
gcloud auth list
gcloud config set project vertex-model-runners
```

### Re-index skills
```bash
rm -rf .cache/
python3 utilities/index_skills.py
```

## 📚 More Info

See [VECTOR_SEARCH_README.md](VECTOR_SEARCH_README.md) for complete documentation.

## 🎯 Try It Now!

```bash
# Set quota project
gcloud auth application-default set-quota-project vertex-model-runners

# Index skills
python3 utilities/index_skills.py

# Update config
nano config.json  # Set "use_vector_search": true

# Run agent
python3 agent.py "How do I monitor query performance?"
```

The agent will intelligently find and use only the most relevant skills! 🎉
