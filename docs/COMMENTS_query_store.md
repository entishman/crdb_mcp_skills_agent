# Detailed Code Comments: query_store.py

## Overview
The QueryStore is the brain of the learning system. It:
1. Stores every user query with its semantic embedding
2. Records which skills helped answer each query
3. Finds similar past queries using vector similarity
4. Recommends skills based on learned patterns

## Key Concepts

### Embeddings & Similarity
- Each query becomes a 768-dimensional vector (embedding) - upgraded 2026-04-04
- Model: all-mpnet-base-v2 (768-dim, higher quality than previous 384-dim)
- Similar queries have similar vectors (measured by cosine distance)
- CockroachDB's pgvector extension enables fast similarity search

### The Learning Loop
```
User asks query
  ↓
Generate embedding (sentence-transformers)
  ↓
Search for similar past queries (cosine similarity)
  ↓
If found: Use learned skills
If not: Use defaults
  ↓
After task completes: Store query + skills that helped
  ↓
Next similar query: Instant skill recommendation!
```

## Method-by-Method Breakdown

### `store_query(query_text, skills_used, ...)`
**What it does:** Saves a query-to-skills mapping for future learning

**Key SQL:** `ON CONFLICT (query_text) DO UPDATE`
- Prevents duplicates
- If user asks same question twice, update the record

**Why store embeddings as JSON?**
- pgvector expects `::vector` type
- We pass as JSON string `[0.23, 0.89, ...]` (768 floats) and cast to vector
- CockroachDB handles the conversion to VECTOR(768)

### `find_similar_queries(query_text, limit, similarity_threshold)`
**What it does:** Find past queries with similar meaning

**The Magic SQL:**
```sql
1 - (query_embedding <-> %s::vector) AS similarity
```
- `<->` = cosine distance operator (pgvector)
- Returns 0 for identical, 1 for opposite
- `1 - distance` converts to similarity (0-1 scale)
- `>= 0.3` threshold filters out weak matches

**Why pass embedding 4 times?**
1. SELECT: Calculate similarity score
2. WHERE: Filter by threshold
3. WHERE: Same calculation (could optimize with CTE)
4. ORDER BY: Sort by distance (ascending = most similar first)

### `get_skills_for_query(query_text, default_skills)`
**What it does:** Main entry point for skill recommendation

**The Decision:**
```
similar_query = find_similar_queries(query_text, limit=1)
if similar_query:
    return learned_skills (from past query)
else:
    return default_skills (fallback)
```

**Threshold: 0.3**
- Lower = more matches (may be wrong)
- Higher = fewer matches (more conservative)
- 0.3 balances recall vs precision for sentence-transformers (all-mpnet-base-v2, 768-dim)

## Database Schema

```sql
CREATE TABLE query_history (
    query_id UUID PRIMARY KEY,
    query_text TEXT UNIQUE,              -- "How do I check cluster health?"
    query_embedding VECTOR(768),         -- [0.23, 0.89, -0.41, ...] (768-dim, upgraded 2026-04-04)
    skills_used TEXT[],                  -- ["reviewing-cluster-health"]
    was_successful BOOLEAN DEFAULT true,
    execution_time_ms INT,
    created_at TIMESTAMPTZ
);

-- HNSW index for fast similarity search (instead of brute-force)
CREATE INDEX ON query_history 
USING hnsw (query_embedding vector_cosine_ops);
```

## Performance Considerations

### Why HNSW Index?
- Brute force: Compare query to ALL past queries (slow for >1000s)
- HNSW: Hierarchical graph-based search (sub-millisecond)
- Trade-off: 99% accuracy, 100x faster

### Batch vs Individual Queries
```python
# Bad (slow)
for text in texts:
    embedding = manager.generate_embedding(text)
    store.store_query(text, skills)

# Good (fast)
embeddings = manager.generate_embeddings_batch(texts)
for text, embedding in zip(texts, embeddings):
    # Use pre-computed embeddings
```

## Common Gotchas

### Mixed Embeddings
- Old hash-based vs sentence-transformers = incompatible
- Old 384-dim vs new 768-dim embeddings = incompatible (migrated 2026-04-04)
- Solution: Truncate table or re-embed old queries with current model

### Threshold Too High
- If 0.6+: May never find matches with sentence-transformers
- Symptom: Always using defaults, never learning

### Empty Skills Array
- If Claude uses no skills, we store `[]`
- Future similar queries get `[]` recommendation
- Actually correct! (query answered without needing skills)
