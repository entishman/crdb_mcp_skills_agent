#!/usr/bin/env python3
"""
Skills Vector Store using CockroachDB

This module manages storage and retrieval of SKILL.md files with vector embeddings
in CockroachDB for semantic search.

Table Schema:
    - skill_name (TEXT PRIMARY KEY): e.g., "operations-and-lifecycle/reviewing-cluster-health"
    - category (TEXT): e.g., "operations-and-lifecycle"
    - short_name (TEXT): e.g., "reviewing-cluster-health"
    - content (TEXT): Full content of the SKILL.md file
    - embedding (VECTOR(768)): Vector embedding of the content
    - created_at (TIMESTAMPTZ): When the skill was indexed
"""

import psycopg2
from psycopg2.extras import execute_values
import json


class SkillsVectorStore:
    """
    Vector store for CockroachDB skills using pgvector extension.
    """

    def __init__(self, connection_string):
        """
        Initialize the vector store.

        Args:
            connection_string: PostgreSQL connection string
                Example: "postgresql://user:pass@host:port/database"
        """
        self.connection_string = connection_string
        self.embedding_dimension = 768  # Vertex AI text-embedding-004 dimension

    def _get_connection(self):
        """Get a database connection."""
        return psycopg2.connect(self.connection_string)

    def create_table(self):
        """
        Create the skills table with vector column.

        This enables the pgvector extension and creates the table structure.
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # Enable pgvector extension
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

                # Create skills table
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS skills (
                        skill_name TEXT PRIMARY KEY,
                        category TEXT NOT NULL,
                        short_name TEXT NOT NULL,
                        content TEXT NOT NULL,
                        embedding VECTOR({self.embedding_dimension}),
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """)

                # Create index on category for faster filtering
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_skills_category
                    ON skills(category);
                """)

                # Create vector index for faster similarity search
                # Using HNSW (Hierarchical Navigable Small World) algorithm
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_skills_embedding
                    ON skills USING hnsw (embedding vector_cosine_ops);
                """)

                conn.commit()

        print("✓ Skills table created with vector support")

    def insert_skill(self, skill_name, category, short_name, content, embedding):
        """
        Insert a single skill with its embedding.

        Args:
            skill_name: Full skill name (e.g., "operations-and-lifecycle/reviewing-cluster-health")
            category: Category (e.g., "operations-and-lifecycle")
            short_name: Short name (e.g., "reviewing-cluster-health")
            content: Full content of the SKILL.md file
            embedding: Vector embedding (list of 768 floats)
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO skills (skill_name, category, short_name, content, embedding)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (skill_name)
                    DO UPDATE SET
                        category = EXCLUDED.category,
                        short_name = EXCLUDED.short_name,
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        created_at = NOW();
                """, (skill_name, category, short_name, content, json.dumps(embedding)))

                conn.commit()

    def insert_skills_batch(self, skills):
        """
        Insert multiple skills in a batch.

        Args:
            skills: List of tuples (skill_name, category, short_name, content, embedding)
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # Convert embeddings to JSON strings
                skills_data = [
                    (name, cat, short, content, json.dumps(emb))
                    for name, cat, short, content, emb in skills
                ]

                execute_values(cur, """
                    INSERT INTO skills (skill_name, category, short_name, content, embedding)
                    VALUES %s
                    ON CONFLICT (skill_name)
                    DO UPDATE SET
                        category = EXCLUDED.category,
                        short_name = EXCLUDED.short_name,
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        created_at = NOW();
                """, skills_data)

                conn.commit()

        print(f"✓ Inserted {len(skills)} skills into vector store")

    def search_similar_skills(self, query_embedding, limit=3):
        """
        Search for skills most similar to the query embedding.

        Uses cosine similarity to find relevant skills.

        Args:
            query_embedding: Query vector (list of 768 floats)
            limit: Number of results to return (default: 3)

        Returns:
            list: List of dicts with skill_name, content, similarity_score
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # Use <-> operator for cosine distance (lower is more similar)
                # Convert to similarity score: 1 - distance
                cur.execute("""
                    SELECT
                        skill_name,
                        category,
                        short_name,
                        content,
                        1 - (embedding <-> %s::vector) AS similarity
                    FROM skills
                    ORDER BY embedding <-> %s::vector
                    LIMIT %s;
                """, (json.dumps(query_embedding), json.dumps(query_embedding), limit))

                results = []
                for row in cur.fetchall():
                    results.append({
                        'skill_name': row[0],
                        'category': row[1],
                        'short_name': row[2],
                        'content': row[3],
                        'similarity': float(row[4])
                    })

                return results

    def get_all_skills(self):
        """
        Get all skills from the database.

        Returns:
            list: List of dicts with skill information
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT skill_name, category, short_name, content
                    FROM skills
                    ORDER BY skill_name;
                """)

                results = []
                for row in cur.fetchall():
                    results.append({
                        'skill_name': row[0],
                        'category': row[1],
                        'short_name': row[2],
                        'content': row[3]
                    })

                return results

    def get_skill_count(self):
        """
        Get the total number of skills in the database.

        Returns:
            int: Number of skills
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM skills;")
                return cur.fetchone()[0]

    def drop_table(self):
        """
        Drop the skills table (use with caution!).
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DROP TABLE IF EXISTS skills CASCADE;")
                conn.commit()

        print("✓ Skills table dropped")


def main():
    """
    Test the vector store.
    """
    import sys
    from pathlib import Path

    # Load config
    config_file = Path("config.json")
    if not config_file.exists():
        print("ERROR: config.json not found")
        sys.exit(1)

    with open(config_file, 'r') as f:
        config = json.load(f)

    # Build connection string from config
    # For CockroachDB Cloud, we need to construct the connection string
    cluster_id = config.get("cluster_id")

    print("To test the vector store, you need a PostgreSQL connection string.")
    print("For CockroachDB Cloud, get it from the Cloud Console:")
    print("  1. Go to your cluster")
    print("  2. Click 'Connect'")
    print("  3. Copy the connection string")
    print()

    connection_string = input("Enter connection string (or press Enter to skip): ").strip()

    if not connection_string:
        print("Skipping test - no connection string provided")
        return

    # Create vector store
    store = SkillsVectorStore(connection_string)

    # Create table
    print("\nCreating skills table...")
    store.create_table()

    # Test with a sample skill
    print("\nInserting test skill...")
    test_embedding = [0.1] * 768  # Dummy embedding
    store.insert_skill(
        skill_name="test/sample-skill",
        category="test",
        short_name="sample-skill",
        content="This is a test skill for demonstrating vector search.",
        embedding=test_embedding
    )

    # Check count
    count = store.get_skill_count()
    print(f"\n✓ Skills in database: {count}")

    # Test search
    print("\nTesting similarity search...")
    results = store.search_similar_skills(test_embedding, limit=3)
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result['skill_name']} (similarity: {result['similarity']:.3f})")


if __name__ == "__main__":
    main()
