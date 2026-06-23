#!/usr/bin/env python3
"""
Create query_history table in ai_demo database.

This table stores user queries with embeddings to enable
query-based learning and similarity search.
"""

import psycopg2
import json
import os
from pathlib import Path


def create_query_history_table():
    """Create the query_history table in ai_demo database."""

    # Load config
    config_file = Path("config.json")
    with open(config_file, 'r') as f:
        config = json.load(f)

    conn_str = config.get('database_connection_string', '')

    # Expand $HOME
    conn_str = conn_str.replace('$HOME', os.path.expanduser('~'))

    # Connect to ai_demo database
    conn_str = conn_str.replace('/defaultdb?', '/ai_demo?')

    print("Creating query_history table in ai_demo database...")
    print()

    conn = psycopg2.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor()

    try:
        # Enable pgvector extension
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        print("✓ Vector extension enabled")

        # Create query_history table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS query_history (
                query_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                query_text TEXT NOT NULL,
                query_embedding VECTOR(768),
                skills_used TEXT[],
                was_successful BOOLEAN DEFAULT true,
                response_quality INT CHECK (response_quality BETWEEN 1 AND 5),
                execution_time_ms INT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                CONSTRAINT unique_query UNIQUE (query_text)
            );
        """)
        print("✓ query_history table created")

        # Create index on embeddings for fast similarity search
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_query_embedding
            ON query_history USING hnsw (query_embedding vector_cosine_ops);
        """)
        print("✓ Vector similarity index created")

        # Create index on created_at for recent queries
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_query_created_at
            ON query_history (created_at DESC);
        """)
        print("✓ Timestamp index created")

        # Create index on skills_used for reverse lookup
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_query_skills
            ON query_history USING GIN (skills_used);
        """)
        print("✓ Skills index created")

        print()
        print("=" * 80)
        print("✓ Query history table setup complete!")
        print("=" * 80)
        print()
        print("Table structure:")
        print("  - query_text: The user's question")
        print("  - query_embedding: Vector embedding (768-dim)")
        print("  - skills_used: Array of skill names that helped answer")
        print("  - was_successful: Whether the query was answered successfully")
        print("  - response_quality: Optional rating (1-5)")
        print("  - execution_time_ms: How long the query took")
        print()

    except psycopg2.Error as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    create_query_history_table()
