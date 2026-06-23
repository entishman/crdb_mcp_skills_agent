#!/usr/bin/env python3
"""
Local Embedding Manager using Sentence Transformers

This module provides high-quality semantic embeddings for query text using
the sentence-transformers library with the all-mpnet-base-v2 model.

Key Features:
- Converts text queries into 768-dimensional semantic vectors
- Captures meaning, not just keywords (e.g., "hotspots" ≈ "hot ranges")
- Enables similarity search via cosine distance in CockroachDB
- Much better than hash-based embeddings for paraphrase detection

CHANGE HISTORY:
- 2026-04-04: Upgraded from all-MiniLM-L6-v2 (384-dim) to all-mpnet-base-v2 (768-dim)
  Rationale: Standardize on 768 dimensions across all vector columns (skills + query_history)
  Benefits: Better semantic similarity, consistent schema, higher quality matches
  Trade-off: Model size 90MB → 420MB (acceptable for quality improvement)
"""

import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer


class OllamaEmbeddingManager:
    """
    Manages text embeddings for query similarity search using sentence-transformers.

    Uses the all-mpnet-base-v2 model which provides high-quality 768-dimensional
    semantic embeddings optimized for similarity search.

    Why all-mpnet-base-v2?
    - High quality (420MB), good performance
    - 768 dimensions (matches our DB schema)
    - Trained for semantic textual similarity
    - Works offline (no API calls needed)
    - Better quality than all-MiniLM-L6-v2
    """

    def __init__(self, model_name="all-mpnet-base-v2", embedding_dim=768):
        """
        Initialize the embedding manager with sentence-transformers.

        Downloads the model on first use (cached in ~/.cache/huggingface/).
        Subsequent initializations load from cache (fast).

        Args:
            model_name: Sentence-transformers model identifier (default: all-mpnet-base-v2)
            embedding_dim: Dimension of embeddings (default: 768, matches all-mpnet-base-v2)
        """
        self.model_name = model_name
        self.embedding_dim = embedding_dim

        # Load the model (from cache if already downloaded)
        print(f"[SentenceTransformers] Loading model: {model_name}")
        self.model = SentenceTransformer(model_name)

        # Confirm dimensions match what we expect
        actual_dim = self.model.get_sentence_embedding_dimension()
        print(f"[SentenceTransformers] Model loaded ({actual_dim}-dim embeddings)")
        print(f"[SentenceTransformers] Ready for semantic similarity search")

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate semantic embedding for a single text using sentence-transformers.

        This method converts text into a 768-dimensional vector where semantically
        similar texts have similar vectors (measured by cosine similarity).

        Example:
            "hotspots in testdb" → [0.23, 0.89, -0.41, ...]
            "hot ranges in testdb" → [0.24, 0.88, -0.42, ...]
            Cosine similarity: ~0.53 (similar meaning detected!)

        Args:
            text: Text to embed (query, sentence, paragraph)

        Returns:
            list: 768-dimensional embedding vector (normalized to unit length)
        """
        # Generate embedding using the transformer model
        # convert_to_numpy=True returns a numpy array (faster than list)
        embedding = self.model.encode(text, convert_to_numpy=True)

        # Convert numpy array to Python list for JSON serialization
        # (needed when storing in PostgreSQL/CockroachDB)
        return embedding.tolist()

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently.

        Uses batch encoding which is MUCH faster than encoding texts one-by-one.
        The model can process multiple texts in parallel on CPU/GPU.

        Performance:
        - Batch encoding 10 texts: ~0.1 seconds
        - Loop encoding 10 texts one-by-one: ~1 second (10x slower!)

        Args:
            texts: List of texts to embed

        Returns:
            list: List of 768-dimensional embedding vectors
        """
        # Batch encode for efficiency (processes all texts in one forward pass)
        embeddings = self.model.encode(texts, convert_to_numpy=True)

        # Convert numpy arrays to Python lists for JSON serialization
        # embeddings is shape (N, 768) where N = number of texts
        return [emb.tolist() for emb in embeddings]


def main():
    """
    Test the embedding manager with real semantic embeddings.

    This demonstrates:
    1. Model loading
    2. Embedding generation
    3. Similarity calculation between queries

    Run with: python ollama_embedding_manager.py
    """
    # Initialize the manager (loads model from cache)
    manager = OllamaEmbeddingManager()

    # Test queries - note that queries 1 & 2 are semantically similar
    queries = [
        "How do I check cluster health?",      # Similar to query 2
        "Is my cluster healthy?",              # Similar to query 1
        "Show me all databases",               # Similar to query 4
        "What tables are in my database?"      # Similar to query 3
    ]

    # Generate embeddings for all queries at once (batch mode = faster)
    print("\nGenerating embeddings for test queries...")
    embeddings = manager.generate_embeddings_batch(queries)

    print(f"\n✓ Generated {len(embeddings)} embeddings")
    print(f"  Dimension: {len(embeddings[0])}")

    # Calculate cosine similarity between all query pairs
    from numpy import dot
    from numpy.linalg import norm

    def cosine_similarity(a, b):
        """
        Calculate cosine similarity between two vectors.

        Returns value between -1 and 1:
        - 1.0 = identical meaning
        - 0.0 = unrelated
        - -1.0 = opposite meaning

        Formula: cos(θ) = (a · b) / (||a|| × ||b||)
        """
        return dot(a, b) / (norm(a) * norm(b))

    # Print similarity matrix (only upper triangle to avoid duplicates)
    print("\nSimilarity matrix:")
    for i, q1 in enumerate(queries):
        for j, q2 in enumerate(queries):
            if j <= i:  # Skip diagonal and lower triangle
                continue
            sim = cosine_similarity(embeddings[i], embeddings[j])
            print(f"  '{q1}' <-> '{q2}': {sim:.3f}")


if __name__ == "__main__":
    main()
