# Utilities - One-Time Setup Scripts

This directory contains scripts that are used only once during initial setup.

## Quick Start

**To populate the skills database (recommended first step):**
```bash
python3 utilities/populate_skills_db.py
```

This loads all 25 SKILL.md files into the `ai_demo.skills` table for fast, persistent access.

---

## Setup Scripts

### `populate_skills_db.py`
**Purpose:** Load all SKILL.md files into the `ai_demo.skills` table.

**When to run:** Once, during initial setup (after creating the `ai_demo` database).

**Usage:**
```bash
python3 utilities/populate_skills_db.py
```

**What it does:**
- Loads 25 SKILL.md files from local cache (or fetches from GitHub if needed)
- Saves all skills to `ai_demo.skills` table
- Enables fast, persistent skill access without hitting GitHub

**Benefits:**
- ✅ Skills persist across server restarts
- ✅ No need to fetch from GitHub every time
- ✅ Multiple agent instances can share the same skills
- ✅ Faster startup (database query vs. 25 file reads)

**Prerequisites:**
- `ai_demo` database exists
- `skills` table exists (created by `create_query_table.py` or `setup_ai_demo.py`)
- Database connection string in `config.json`

**Note:** After running this once, the agent will automatically load skills from the database. You only need to re-run this if skills are updated on GitHub and you want to refresh.

---

### `create_query_table.py`
**Purpose:** Create the `query_history` table in the `ai_demo` database.

**When to run:** Once, before using the query learning system.

**Usage:**
```bash
python3 utilities/create_query_table.py
```

**What it does:**
- Creates the `ai_demo.query_history` table
- Enables pgvector extension
- Creates HNSW index for fast similarity search
- Creates indexes on timestamps and skills

**Prerequisites:**
- Database connection string in `config.json`
- CockroachDB cluster with pgvector support (v23.2+)

---

### `setup_ai_demo.py`
**Purpose:** Set up the `ai_demo` database and initial schema.

**When to run:** Once, during initial project setup.

**Usage:**
```bash
python3 utilities/setup_ai_demo.py
```

**What it does:**
- Creates the `ai_demo` database
- Sets up initial tables and schemas

---

### `index_skills.py`
**Purpose:** Index CockroachDB skill guides with vector embeddings for semantic search.

**When to run:** Once, if you want to enable vector search mode (alternative to query learning).

**Usage:**
```bash
python3 utilities/index_skills.py
```

Or with connection string:
```bash
python3 utilities/index_skills.py "postgresql://user:password@host:26257/defaultdb"
```

**What it does:**
- Loads all 25 SKILL.md files
- Generates embeddings using Vertex AI
- Creates `skills` table in CockroachDB
- Stores skills with embeddings for semantic search

**Prerequisites:**
- Vertex AI authentication configured
- Database connection string
- CockroachDB cluster with pgvector support

**Note:** Vector search is an alternative to query learning. Most users should use query learning (enabled by default) instead.

---

## When to Use These Scripts

These scripts are **one-time setup only**. Once run successfully, they don't need to be run again unless:
- You're setting up a new database
- You've dropped the tables and need to recreate them
- You want to re-index skills after major updates

For normal operation, use:
- `python3 agent.py` to run the agent
- Query learning is enabled by default in `config.json`
