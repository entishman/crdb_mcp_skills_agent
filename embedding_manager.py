#!/usr/bin/env python3
"""
Embedding Manager for SKILL.md Files

This module generates vector embeddings using Vertex AI Text Embeddings API.
These embeddings are used for semantic search to find relevant skills for user queries.

Vertex AI Text Embeddings:
- Model: textembedding-gecko@003 (768 dimensions)
- Or: text-embedding-004 (768 dimensions, newer)
"""

from google.cloud import aiplatform
from google.cloud.aiplatform_v1.types import content as aiplatform_content
import time


class EmbeddingManager:
    """
    Manages embedding generation using Vertex AI.
    """

    def __init__(self, project_id, region="us-central1", model="text-embedding-004"):
        """
        Initialize the embedding manager.

        Args:
            project_id: GCP project ID
            region: Region for Vertex AI (default: us-central1)
            model: Embedding model to use (default: text-embedding-004)
                   Options: text-embedding-004 (768-dim), textembedding-gecko@003 (768-dim)
        """
        self.project_id = project_id
        self.region = region
        self.model_name = model
        self.embedding_dimension = 768  # Standard for these models

        # Initialize Vertex AI
        aiplatform.init(project=project_id, location=region)

    def generate_embedding(self, text):
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            list: Embedding vector (768 dimensions)
        """
        from vertexai.language_models import TextEmbeddingModel

        model = TextEmbeddingModel.from_pretrained(self.model_name)

        # Generate embedding
        embeddings = model.get_embeddings([text])

        # Return the first (and only) embedding's values
        return embeddings[0].values

    def generate_embeddings_batch(self, texts, batch_size=5):
        """
        Generate embeddings for multiple texts in batches.

        Vertex AI has rate limits, so we batch the requests and add delays.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts per batch (default: 5)

        Returns:
            list: List of embedding vectors
        """
        from vertexai.language_models import TextEmbeddingModel

        model = TextEmbeddingModel.from_pretrained(self.model_name)

        all_embeddings = []

        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            print(f"  Generating embeddings for batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")

            # Generate embeddings for this batch
            embeddings = model.get_embeddings(batch)

            # Extract the values
            for embedding in embeddings:
                all_embeddings.append(embedding.values)

            # Rate limiting: wait between batches
            if i + batch_size < len(texts):
                time.sleep(1)  # 1 second delay between batches

        return all_embeddings

    def get_dimension(self):
        """
        Get the dimension of embeddings produced by this model.

        Returns:
            int: Embedding dimension (768)
        """
        return self.embedding_dimension


def main():
    """
    Test the embedding manager.
    """
    import json
    from pathlib import Path

    # Load config
    config_file = Path("config.json")
    if not config_file.exists():
        print("ERROR: config.json not found")
        return

    with open(config_file, 'r') as f:
        config = json.load(f)

    # Get project ID from config
    project_id = config.get("vertex_ai_project", "vertex-model-runners")
    region = config.get("vertex_ai_region", "global")

    # If region is "global", use us-central1 for embeddings (global isn't valid for embeddings)
    if region == "global":
        region = "us-central1"

    print(f"Testing Embedding Manager")
    print(f"  Project: {project_id}")
    print(f"  Region: {region}")
    print()

    # Create embedding manager
    manager = EmbeddingManager(project_id=project_id, region=region)

    # Test with a few sample texts
    test_texts = [
        "How do I check the health of my CockroachDB cluster?",
        "What are the best practices for database schema design?",
        "How do I monitor query performance?"
    ]

    print("Generating embeddings for test texts...")
    embeddings = manager.generate_embeddings_batch(test_texts)

    print(f"\n✓ Generated {len(embeddings)} embeddings")
    print(f"  Dimension: {len(embeddings[0])}")
    print(f"  Sample embedding (first 10 values): {embeddings[0][:10]}")


if __name__ == "__main__":
    main()
