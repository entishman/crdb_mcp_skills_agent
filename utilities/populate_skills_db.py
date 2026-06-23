#!/usr/bin/env python3
"""
Populate the ai_demo.skills table with all SKILL.md files.

This script:
1. Loads skills from local cache (or fetches from GitHub if needed)
2. Saves all skills to the ai_demo.skills table in CockroachDB
"""

import sys
import json
from pathlib import Path

# Add parent directory to path so we can import skill_fetcher
sys.path.insert(0, str(Path(__file__).parent.parent))

from skill_fetcher import SkillFetcher


def main():
    """Populate skills database."""
    # Load config
    config_file = Path(__file__).parent.parent / "config.json"

    if not config_file.exists():
        print("ERROR: config.json not found")
        print("Please create config.json with database_connection_string")
        return 1

    with open(config_file, 'r') as f:
        config = json.load(f)

    connection_string = config.get('database_connection_string')

    if not connection_string:
        print("ERROR: database_connection_string not in config.json")
        return 1

    print("=" * 80)
    print("Populating ai_demo.skills table")
    print("=" * 80)
    print()

    # Create fetcher with database connection
    fetcher = SkillFetcher(verbose=True, connection_string=connection_string)

    # Load from cache (or GitHub if cache doesn't exist)
    if not fetcher.load_from_cache():
        print("No local cache found, fetching from GitHub...")
        fetcher.fetch_all_skills()

    # Save to database
    print()
    if fetcher.save_to_database():
        print()
        print("=" * 80)
        print("✓ Successfully populated ai_demo.skills table")
        print(f"  Total skills: {len(fetcher.skills)}")
        print("=" * 80)
        return 0
    else:
        print("ERROR: Failed to save skills to database")
        return 1


if __name__ == "__main__":
    sys.exit(main())
