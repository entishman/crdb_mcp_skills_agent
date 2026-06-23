#!/usr/bin/env python3
"""
Setup AI Demo Database and Index Skills

This script:
1. Creates the ai_demo database
2. Creates the skills table
3. Indexes all SKILL.md files with embeddings
"""

import json
import sys
import getpass
from pathlib import Path
import psycopg2
from skill_fetcher import SkillFetcher
from embedding_manager import EmbeddingManager
from skills_vectorstore import SkillsVectorStore


def get_connection_string(database='defaultdb'):
    """Get connection string with password prompt."""
    config_file = Path("config.json")
    with open(config_file, 'r') as f:
        config = json.load(f)

    conn_str = config.get('database_connection_string', '')

    # Expand $HOME
    import os
    conn_str = conn_str.replace('$HOME', os.path.expanduser('~'))

    # Replace database name
    conn_str = conn_str.replace('/defaultdb?', f'/{database}?')

    # Check if password is in the string
    if ':@' in conn_str or '@' in conn_str and 'tim@' in conn_str:
        # No password, prompt for it
        print(f"\nConnecting to CockroachDB cluster...")
        password = getpass.getpass("Enter database password for user 'tim': ")

        # Insert password into connection string
        conn_str = conn_str.replace('tim@', f'tim:{password}@')

    return conn_str


def main():
    print("\n" + "=" * 80)
    print("AI Demo Database Setup")
    print("=" * 80)
    print()

    # Load config
    config_file = Path("config.json")
    with open(config_file, 'r') as f:
        config = json.load(f)

    project_id = config.get("vertex_ai_project", "vertex-model-runners")
    region = config.get("vertex_ai_region", "global")
    if region == "global":
        embedding_region = "us-central1"
    else:
        embedding_region = region

    print("Step 1: Create ai_demo database")
    print("-" * 80)

    # Get connection string for defaultdb (to create the new database)
    try:
        defaultdb_conn = get_connection_string('defaultdb')

        conn = psycopg2.connect(defaultdb_conn)
        conn.autocommit = True
        cur = conn.cursor()

        # Create database
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'ai_demo'")
        if cur.fetchone():
            print("  ✓ Database ai_demo already exists")
        else:
            cur.execute("CREATE DATABASE ai_demo")
            print("  ✓ Created database ai_demo")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"  ✗ Error creating database: {e}")
        print("\n  If authentication failed, make sure you have the correct password.")
        print("  You can also create the database manually:")
        print("    cockroach sql --url <connection-string> --execute 'CREATE DATABASE ai_demo;'")
        sys.exit(1)

    print()

    # Now proceed with indexing in ai_demo
    print("Step 2: Initialize components")
    print("-" * 80)

    skill_fetcher = SkillFetcher(verbose=True)
    embedding_manager = EmbeddingManager(project_id=project_id, region=embedding_region)

    # Get connection string for ai_demo
    ai_demo_conn = get_connection_string('ai_demo')
    vector_store = SkillsVectorStore(ai_demo_conn)

    print()

    print("Step 3: Load skills")
    print("-" * 80)
    if not skill_fetcher.load_from_cache():
        skill_fetcher.fetch_all_skills()
    print(f"✓ Loaded {len(skill_fetcher.skills)} skills")
    print()

    print("Step 4: Create skills table in ai_demo")
    print("-" * 80)
    vector_store.create_table()
    print()

    print("Step 5: Generate embeddings")
    print("-" * 80)

    skill_names = []
    skill_contents = []
    skill_metadata = []

    for skill_name, skill_data in sorted(skill_fetcher.skills.items()):
        skill_names.append(skill_name)
        skill_contents.append(skill_data['content'])

        parts = skill_name.split('/')
        category = parts[0] if len(parts) > 0 else "unknown"
        short_name = parts[1] if len(parts) > 1 else skill_name

        skill_metadata.append({'category': category, 'short_name': short_name})

    print(f"Generating embeddings for {len(skill_contents)} skills...")
    embeddings = embedding_manager.generate_embeddings_batch(skill_contents, batch_size=5)
    print(f"✓ Generated {len(embeddings)} embeddings")
    print()

    print("Step 6: Store in ai_demo database")
    print("-" * 80)

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

    count = vector_store.get_skill_count()
    print(f"✓ Total skills in ai_demo: {count}")
    print()

    print("Step 7: Test semantic search")
    print("-" * 80)

    test_query = "How do I check cluster health?"
    print(f"Test query: \"{test_query}\"")
    print()

    query_embedding = embedding_manager.generate_embedding(test_query)
    results = vector_store.search_similar_skills(query_embedding, limit=3)

    print("Top 3 relevant skills:")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result['skill_name']} (similarity: {result['similarity']:.3f})")
    print()

    print("Step 8: Update config.json")
    print("-" * 80)

    # Update connection string to use ai_demo
    config['database_connection_string'] = config['database_connection_string'].replace(
        '/defaultdb?', '/ai_demo?'
    )
    config['use_vector_search'] = True

    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)

    print("  ✓ Updated database_connection_string to use ai_demo")
    print("  ✓ Enabled use_vector_search")
    print()

    print("=" * 80)
    print("✓ Setup Complete!")
    print("=" * 80)
    print()
    print("The skills are now indexed in the ai_demo database.")
    print("Run the agent with: python3 agent.py")
    print()


if __name__ == "__main__":
    main()
