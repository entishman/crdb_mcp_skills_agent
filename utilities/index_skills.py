#!/usr/bin/env python3
"""
Index SKILL.md Files into CockroachDB Vector Store

This script:
1. Loads all SKILL.md files (from cache or GitHub)
2. Generates vector embeddings using Vertex AI
3. Stores skills + embeddings in CockroachDB

Usage:
    python3 index_skills.py [connection_string]

If connection_string is not provided, it will prompt for it.
"""

import json
import sys
from pathlib import Path
from skill_fetcher import SkillFetcher
from embedding_manager import EmbeddingManager
from skills_vectorstore import SkillsVectorStore


def get_connection_string():
    """
    Get the CockroachDB connection string.

    Returns:
        str: PostgreSQL connection string
    """
    # Check if provided as command line argument
    if len(sys.argv) > 1:
        return sys.argv[1]

    # Check if in config file
    config_file = Path("config.json")
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
            if "database_connection_string" in config:
                return config["database_connection_string"]

    # Prompt user
    print("=" * 80)
    print("CockroachDB Connection String Required")
    print("=" * 80)
    print()
    print("To index skills into CockroachDB, you need a connection string.")
    print()
    print("To get your connection string:")
    print("  1. Go to CockroachDB Cloud Console: https://cockroachlabs.cloud")
    print("  2. Select your cluster")
    print("  3. Click 'Connect'")
    print("  4. Choose 'General connection string'")
    print("  5. Copy the connection string")
    print()
    print("Example format:")
    print("  postgresql://user:password@host:26257/defaultdb?sslmode=verify-full")
    print()

    connection_string = input("Enter connection string: ").strip()

    if not connection_string:
        print("ERROR: No connection string provided")
        sys.exit(1)

    # Offer to save it to config
    save = input("\nSave to config.json? (y/n): ").strip().lower()
    if save == 'y':
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
        else:
            config = {}

        config["database_connection_string"] = connection_string

        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

        print("✓ Saved to config.json")

    return connection_string


def main():
    """
    Main indexing workflow.
    """
    print("\n" + "=" * 80)
    print("Skills Indexing Script")
    print("=" * 80)
    print()

    # Load configuration
    config_file = Path("config.json")
    if not config_file.exists():
        print("ERROR: config.json not found")
        print("Please copy config.template.json to config.json and configure it.")
        sys.exit(1)

    with open(config_file, 'r') as f:
        config = json.load(f)

    # Get project info for Vertex AI
    project_id = config.get("vertex_ai_project", "vertex-model-runners")
    region = config.get("vertex_ai_region", "global")

    # Embeddings API doesn't support "global" - use us-central1
    if region == "global":
        embedding_region = "us-central1"
    else:
        embedding_region = region

    print(f"Vertex AI Configuration:")
    print(f"  Project: {project_id}")
    print(f"  Region: {embedding_region}")
    print()

    # Get database connection string
    connection_string = get_connection_string()
    print()

    # Initialize components
    print("Initializing components...")
    skill_fetcher = SkillFetcher(verbose=True)
    embedding_manager = EmbeddingManager(
        project_id=project_id,
        region=embedding_region
    )
    vector_store = SkillsVectorStore(connection_string)
    print()

    # Step 1: Load skills
    print("=" * 80)
    print("Step 1: Loading Skills")
    print("=" * 80)
    print()

    if not skill_fetcher.load_from_cache():
        print("Cache not found, fetching from GitHub...")
        skill_fetcher.fetch_all_skills()

    print(f"✓ Loaded {len(skill_fetcher.skills)} skills")
    print()

    # Step 2: Create database table
    print("=" * 80)
    print("Step 2: Creating Database Table")
    print("=" * 80)
    print()

    vector_store.create_table()
    print()

    # Step 3: Generate embeddings
    print("=" * 80)
    print("Step 3: Generating Embeddings")
    print("=" * 80)
    print()

    # Prepare texts and metadata
    skill_names = []
    skill_contents = []
    skill_metadata = []

    for skill_name, skill_data in sorted(skill_fetcher.skills.items()):
        skill_names.append(skill_name)
        skill_contents.append(skill_data['content'])

        # Parse category and short name
        parts = skill_name.split('/')
        category = parts[0] if len(parts) > 0 else "unknown"
        short_name = parts[1] if len(parts) > 1 else skill_name

        skill_metadata.append({
            'category': category,
            'short_name': short_name
        })

    print(f"Generating embeddings for {len(skill_contents)} skills...")
    print("This may take a few minutes...")
    print()

    embeddings = embedding_manager.generate_embeddings_batch(skill_contents, batch_size=5)

    print(f"\n✓ Generated {len(embeddings)} embeddings")
    print(f"  Dimension: {len(embeddings[0])}")
    print()

    # Step 4: Store in database
    print("=" * 80)
    print("Step 4: Storing in CockroachDB")
    print("=" * 80)
    print()

    # Prepare batch data
    skills_batch = []
    for i, skill_name in enumerate(skill_names):
        skills_batch.append((
            skill_name,
            skill_metadata[i]['category'],
            skill_metadata[i]['short_name'],
            skill_contents[i],
            embeddings[i]
        ))

    vector_store.insert_skills_batch(skills_batch)
    print()

    # Verify
    count = vector_store.get_skill_count()
    print(f"✓ Total skills in database: {count}")
    print()

    # Step 5: Test search
    print("=" * 80)
    print("Step 5: Testing Semantic Search")
    print("=" * 80)
    print()

    test_query = "How do I check cluster health?"
    print(f"Test query: \"{test_query}\"")
    print()

    # Generate embedding for test query
    query_embedding = embedding_manager.generate_embedding(test_query)

    # Search
    results = vector_store.search_similar_skills(query_embedding, limit=3)

    print("Top 3 relevant skills:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['skill_name']}")
        print(f"   Similarity: {result['similarity']:.3f}")
        print(f"   Preview: {result['content'][:150]}...")

    print("\n" + "=" * 80)
    print("✓ Skills Indexing Complete!")
    print("=" * 80)
    print()
    print("The agent will now use semantic search to find relevant skills.")
    print("This will reduce token usage by ~90% and improve context retention.")
    print()


if __name__ == "__main__":
    main()
