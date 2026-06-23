#!/usr/bin/env python3
"""
Query Store - Manages query history and similarity search

This module handles:
1. Storing user queries with embeddings
2. Finding similar past queries
3. Retrieving skill mappings from successful queries
4. Learning from usage patterns
"""

import psycopg2
import json
from typing import List, Dict, Optional
from ollama_embedding_manager import OllamaEmbeddingManager


class QueryStore:
    """
    Manages query history and similarity-based skill retrieval.
    """

    def __init__(self, connection_string, embedding_manager=None):
        """
        Initialize the query store.

        Args:
            connection_string: PostgreSQL connection string for ai_demo database
            embedding_manager: Optional embedding manager (creates one if not provided)
        """
        self.connection_string = connection_string
        self.embedding_manager = embedding_manager or OllamaEmbeddingManager()

    def _get_connection(self):
        """Get database connection."""
        return psycopg2.connect(self.connection_string)

    def store_query(
        self,
        query_text: str,
        skills_used: List[str],
        was_successful: bool = True,
        execution_time_ms: Optional[int] = None
    ) -> str:
        """
        Store a query and its associated skills.

        Args:
            query_text: The user's question
            skills_used: List of skill names that were used
            was_successful: Whether the query was answered successfully
            execution_time_ms: Optional execution time in milliseconds

        Returns:
            str: UUID of the stored query
        """
        # Generate embedding
        embedding = self.embedding_manager.generate_embedding(query_text)

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # Insert or update query
                cur.execute("""
                    INSERT INTO query_history
                        (query_text, query_embedding, skills_used, was_successful, execution_time_ms)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (query_text)
                    DO UPDATE SET
                        query_embedding = EXCLUDED.query_embedding,
                        skills_used = EXCLUDED.skills_used,
                        was_successful = EXCLUDED.was_successful,
                        execution_time_ms = EXCLUDED.execution_time_ms,
                        created_at = NOW()
                    RETURNING query_id;
                """, (query_text, json.dumps(embedding), skills_used, was_successful, execution_time_ms))

                query_id = cur.fetchone()[0]
                conn.commit()

                return str(query_id)

    def find_similar_queries(
        self,
        query_text: str,
        limit: int = 3,
        similarity_threshold: float = 0.3
    ) -> List[Dict]:
        """
        Find similar past queries and their skill mappings.

        Args:
            query_text: The current user query
            limit: Maximum number of results to return
            similarity_threshold: Minimum similarity score (0-1, default: 0.3)

        Returns:
            list: List of dicts with query_text, skills_used, similarity
        """
        # Generate embedding for query
        query_embedding = self.embedding_manager.generate_embedding(query_text)

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # Search for similar queries
                # Use cosine distance operator: <->
                # Convert to similarity: 1 - distance
                cur.execute("""
                    SELECT
                        query_text,
                        skills_used,
                        1 - (query_embedding <-> %s::vector) AS similarity
                    FROM query_history
                    WHERE was_successful = true
                        AND 1 - (query_embedding <-> %s::vector) >= %s
                    ORDER BY query_embedding <-> %s::vector
                    LIMIT %s;
                """, (
                    json.dumps(query_embedding),
                    json.dumps(query_embedding),
                    similarity_threshold,
                    json.dumps(query_embedding),
                    limit
                ))

                results = []
                for row in cur.fetchall():
                    results.append({
                        'query_text': row[0],
                        'skills_used': row[1],
                        'similarity': float(row[2])
                    })

                return results

    def get_skills_for_query(
        self,
        query_text: str,
        default_skills: Optional[List[str]] = None
    ) -> Dict:
        """
        Get recommended skills for a query based on similar past queries.

        Args:
            query_text: The user's question
            default_skills: Skills to use if no similar queries found

        Returns:
            dict: {
                'skills': list of skill names,
                'source': 'learned' or 'default',
                'similarity': similarity score (if learned),
                'matched_query': the similar query that was matched (if learned)
            }
        """
        similar = self.find_similar_queries(query_text, limit=1, similarity_threshold=0.3)

        if similar:
            best_match = similar[0]
            return {
                'skills': best_match['skills_used'],
                'source': 'learned',
                'similarity': best_match['similarity'],
                'matched_query': best_match['query_text']
            }
        else:
            return {
                'skills': default_skills or [],
                'source': 'default',
                'similarity': None,
                'matched_query': None
            }

    def get_query_stats(self) -> Dict:
        """
        Get statistics about the query history.

        Returns:
            dict: Statistics including total queries, success rate, etc.
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        COUNT(*) as total_queries,
                        COUNT(*) FILTER (WHERE was_successful) as successful_queries,
                        (SELECT COUNT(DISTINCT skill)
                         FROM query_history, UNNEST(skills_used) as skill) as unique_skills_used,
                        AVG(execution_time_ms) as avg_execution_time_ms
                    FROM query_history;
                """)

                row = cur.fetchone()
                return {
                    'total_queries': row[0] or 0,
                    'successful_queries': row[1] or 0,
                    'unique_skills_used': row[2] or 0,
                    'avg_execution_time_ms': float(row[3]) if row[3] else 0
                }

    def get_most_used_skills(self, limit: int = 10) -> List[Dict]:
        """
        Get the most frequently used skills.

        Args:
            limit: Number of skills to return

        Returns:
            list: List of dicts with skill_name and usage_count
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT skill, COUNT(*) as usage_count
                    FROM query_history,
                         UNNEST(skills_used) as skill
                    WHERE was_successful = true
                    GROUP BY skill
                    ORDER BY usage_count DESC
                    LIMIT %s;
                """, (limit,))

                results = []
                for row in cur.fetchall():
                    results.append({
                        'skill_name': row[0],
                        'usage_count': row[1]
                    })

                return results


def main():
    """Test the query store."""
    import os
    from pathlib import Path

    # Load config
    config_file = Path("config.json")
    with open(config_file, 'r') as f:
        config = json.load(f)

    conn_str = config.get('database_connection_string', '')
    conn_str = conn_str.replace('$HOME', os.path.expanduser('~'))
    conn_str = conn_str.replace('/defaultdb?', '/ai_demo?')

    print("Testing Query Store")
    print("=" * 80)
    print()

    store = QueryStore(conn_str)

    # Test storing queries
    print("1. Storing test queries...")
    test_queries = [
        ("How do I check cluster health?", ["operations-and-lifecycle/reviewing-cluster-health"]),
        ("Is my cluster healthy?", ["operations-and-lifecycle/reviewing-cluster-health"]),
        ("Show me all databases", ["query-and-schema-design/cockroachdb-sql"]),
        ("List tables in my database", ["query-and-schema-design/cockroachdb-sql"]),
    ]

    for query, skills in test_queries:
        query_id = store.store_query(query, skills)
        print(f"  ✓ Stored: '{query}' (ID: {query_id[:8]}...)")

    print()

    # Test finding similar queries
    print("2. Testing similarity search...")
    new_query = "How can I monitor my cluster's health?"
    print(f"   Query: '{new_query}'")
    print()

    similar = store.find_similar_queries(new_query, limit=3)
    for i, result in enumerate(similar, 1):
        print(f"   {i}. Similar: '{result['query_text']}'")
        print(f"      Similarity: {result['similarity']:.3f}")
        print(f"      Skills: {', '.join(result['skills_used'])}")
        print()

    # Test getting skills recommendation
    print("3. Getting skill recommendations...")
    recommendation = store.get_skills_for_query(new_query)
    print(f"   Source: {recommendation['source']}")
    print(f"   Skills: {recommendation['skills']}")
    if recommendation['similarity']:
        print(f"   Similarity: {recommendation['similarity']:.3f}")
    print()

    # Test stats
    print("4. Query statistics...")
    stats = store.get_query_stats()
    print(f"   Total queries: {stats['total_queries']}")
    print(f"   Successful: {stats['successful_queries']}")
    print(f"   Unique skills used: {stats['unique_skills_used']}")
    print()

    print("=" * 80)
    print("✓ Query store tests complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
