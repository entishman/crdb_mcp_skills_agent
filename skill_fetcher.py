#!/usr/bin/env python3
"""
CockroachDB Skills Fetcher

This module fetches all SKILL.md files from the cockroachdb-skills GitHub repository
and provides them as context for the LLM agent to understand CockroachDB best practices.

The skills are organized into categories:
- application-development
- cost-and-usage-management
- integrations-and-ecosystem
- observability-and-diagnostics
- onboarding-and-migrations
- operations-and-lifecycle
- performance-and-scaling
- query-and-schema-design
- resilience-and-disaster-recovery
- security-and-governance
"""

import httpx
from pathlib import Path
import json
import psycopg2
import os


class SkillFetcher:
    """
    Fetches and caches SKILL.md files from the CockroachDB skills repository.
    """

    # GitHub repository details
    REPO_OWNER = "cockroachlabs"
    REPO_NAME = "cockroachdb-skills"
    REPO_BRANCH = "main"
    SKILLS_PATH = "skills"

    # GitHub API base URL
    GITHUB_API_BASE = "https://api.github.com"

    # Raw content base URL
    GITHUB_RAW_BASE = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{REPO_BRANCH}"

    def __init__(self, cache_dir=".cache", verbose=False, connection_string=None):
        """
        Initialize the skill fetcher.

        Args:
            cache_dir: Directory to cache downloaded skills (default: .cache)
            verbose: Enable verbose output (default: False)
            connection_string: PostgreSQL connection string for ai_demo database (optional)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.client = httpx.Client(timeout=30.0)
        self.skills = {}
        self.verbose = verbose
        self.connection_string = connection_string

        # Prepare database connection string for ai_demo if provided
        if self.connection_string:
            self.db_connection_string = self.connection_string.replace('$HOME', os.path.expanduser('~'))
            self.db_connection_string = self.db_connection_string.replace('/defaultdb?', '/ai_demo?')
        else:
            self.db_connection_string = None

    def _get_directory_contents(self, path):
        """
        Get contents of a directory in the GitHub repository using the GitHub API.

        Args:
            path: Path within the repository (e.g., "skills" or "skills/operations-and-lifecycle")

        Returns:
            list: List of items in the directory (each item is a dict with name, path, type, etc.)
        """
        url = f"{self.GITHUB_API_BASE}/repos/{self.REPO_OWNER}/{self.REPO_NAME}/contents/{path}"

        try:
            response = self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"ERROR: Failed to fetch directory {path}: {e}")
            return []

    def _fetch_file_content(self, file_path):
        """
        Fetch raw content of a file from GitHub.

        Args:
            file_path: Path to the file in the repository (e.g., "skills/operations-and-lifecycle/reviewing-cluster-health/SKILL.md")

        Returns:
            str: File content, or None if fetch failed
        """
        url = f"{self.GITHUB_RAW_BASE}/{file_path}"

        try:
            response = self.client.get(url)
            response.raise_for_status()
            return response.text
        except httpx.HTTPError as e:
            print(f"ERROR: Failed to fetch file {file_path}: {e}")
            return None

    def _find_skill_files(self, base_path):
        """
        Recursively find all SKILL.md files in the repository.

        This traverses the GitHub repository structure to discover all skill files.

        Args:
            base_path: Starting path (e.g., "skills")

        Returns:
            list: List of paths to SKILL.md files
        """
        skill_files = []

        # Get contents of the current directory
        items = self._get_directory_contents(base_path)

        for item in items:
            if item['type'] == 'file' and item['name'] == 'SKILL.md':
                # Found a skill file
                skill_files.append(item['path'])
            elif item['type'] == 'dir':
                # Recursively search subdirectories
                skill_files.extend(self._find_skill_files(item['path']))

        return skill_files

    def fetch_all_skills(self):
        """
        Fetch all SKILL.md files from the repository.

        This method:
        1. Discovers all SKILL.md files in the repository
        2. Fetches their content
        3. Caches them locally
        4. Returns them as a dictionary

        Returns:
            dict: Dictionary mapping skill path to content
                  Example: {"skills/operations-and-lifecycle/reviewing-cluster-health/SKILL.md": "content..."}
        """
        if self.verbose:
            print("Fetching CockroachDB skills from GitHub...")

        # Find all SKILL.md files
        skill_files = self._find_skill_files(self.SKILLS_PATH)
        if self.verbose:
            print(f"Found {len(skill_files)} skill files")

        # Fetch content for each skill
        for skill_path in skill_files:
            # Create a readable name from the path
            # e.g., "skills/operations-and-lifecycle/reviewing-cluster-health/SKILL.md"
            # becomes "operations-and-lifecycle/reviewing-cluster-health"
            skill_name = "/".join(skill_path.split("/")[1:-1])

            if self.verbose:
                print(f"  Fetching: {skill_name}")

            # Fetch the content
            content = self._fetch_file_content(skill_path)

            if content:
                self.skills[skill_name] = {
                    'path': skill_path,
                    'content': content
                }

                # Cache the skill to disk
                cache_file = self.cache_dir / f"{skill_name.replace('/', '_')}.md"
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                cache_file.write_text(content)

        if self.verbose:
            print(f"✓ Successfully fetched {len(self.skills)} skills from GitHub\n")

        # Save to database if connection is available
        if self.db_connection_string:
            self.save_to_database()

        return self.skills

    def get_skills_context(self):
        """
        Get all skills formatted as context for the LLM.

        Returns:
            str: Formatted string containing all skill documentation
        """
        if not self.skills:
            self.fetch_all_skills()

        context_parts = [
            "# CockroachDB Skills Documentation",
            "",
            "The following are skill documents that describe best practices for working with CockroachDB.",
            "Use these as reference when planning how to fulfill user requests.",
            ""
        ]

        for skill_name, skill_data in sorted(self.skills.items()):
            context_parts.append(f"## Skill: {skill_name}")
            context_parts.append("")
            context_parts.append(skill_data['content'])
            context_parts.append("")
            context_parts.append("-" * 80)
            context_parts.append("")

        return "\n".join(context_parts)

    def load_from_database(self):
        """
        Load skills from CockroachDB ai_demo.skills table.

        Returns:
            bool: True if skills were loaded successfully, False otherwise
        """
        if not self.db_connection_string:
            return False

        try:
            conn = psycopg2.connect(self.db_connection_string)
            cur = conn.cursor()

            # Check if skills table exists and has data
            cur.execute("SELECT COUNT(*) FROM skills")
            count = cur.fetchone()[0]

            if count == 0:
                cur.close()
                conn.close()
                return False

            if self.verbose:
                print(f"Loading {count} skills from database...")

            # Load all skills
            cur.execute("""
                SELECT skill_name, category, short_name, content
                FROM skills
                ORDER BY skill_name
            """)

            for row in cur.fetchall():
                skill_name = row[0]
                content = row[3]

                self.skills[skill_name] = {
                    'path': f"skills/{skill_name}/SKILL.md",
                    'content': content
                }

            cur.close()
            conn.close()

            if self.verbose:
                print(f"✓ Loaded {len(self.skills)} skills from database\n")
            return True

        except Exception as e:
            if self.verbose:
                print(f"Could not load from database: {e}")
            return False

    def save_to_database(self):
        """
        Save all current skills to the CockroachDB ai_demo.skills table.

        Returns:
            bool: True if saved successfully, False otherwise
        """
        if not self.db_connection_string or not self.skills:
            return False

        try:
            conn = psycopg2.connect(self.db_connection_string)
            cur = conn.cursor()

            if self.verbose:
                print(f"Saving {len(self.skills)} skills to database...")

            # Clear existing skills
            cur.execute("TRUNCATE TABLE skills")

            # Insert all skills
            for skill_name, skill_data in self.skills.items():
                # Parse category and short_name from skill_name
                # e.g., "operations-and-lifecycle/reviewing-cluster-health"
                parts = skill_name.split('/')
                category = parts[0] if len(parts) > 0 else ''
                short_name = parts[1] if len(parts) > 1 else skill_name

                cur.execute("""
                    INSERT INTO skills (skill_name, category, short_name, content)
                    VALUES (%s, %s, %s, %s)
                """, (skill_name, category, short_name, skill_data['content']))

            conn.commit()
            cur.close()
            conn.close()

            if self.verbose:
                print(f"✓ Saved {len(self.skills)} skills to database\n")
            return True

        except Exception as e:
            if self.verbose:
                print(f"Could not save to database: {e}")
            return False

    def load_from_cache(self):
        """
        Load skills from local cache instead of fetching from GitHub.

        Returns:
            bool: True if cache was loaded successfully, False otherwise
        """
        if not self.cache_dir.exists():
            return False

        cached_files = list(self.cache_dir.glob("*.md"))

        if not cached_files:
            return False

        if self.verbose:
            print(f"Loading {len(cached_files)} skills from local cache...")

        for cache_file in cached_files:
            # Convert filename back to skill name
            # e.g., "operations-and-lifecycle_reviewing-cluster-health.md"
            # becomes "operations-and-lifecycle/reviewing-cluster-health"
            skill_name = cache_file.stem.replace('_', '/', 1)

            content = cache_file.read_text()
            self.skills[skill_name] = {
                'path': f"skills/{skill_name}/SKILL.md",
                'content': content
            }

        if self.verbose:
            print(f"✓ Loaded {len(self.skills)} skills from local cache\n")
        return True


def main():
    """
    Test the skill fetcher by downloading and displaying all skills.
    """
    # Load config to get database connection string
    import os
    config_file = Path("config.json")
    connection_string = None

    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
            connection_string = config.get('database_connection_string')

    fetcher = SkillFetcher(verbose=True, connection_string=connection_string)

    # Try to load from database first, then cache, then GitHub
    if not fetcher.load_from_database():
        if not fetcher.load_from_cache():
            # Fetch from GitHub if no cache
            fetcher.fetch_all_skills()

    # Display summary
    print("\n" + "="*80)
    print("Skills Summary")
    print("="*80 + "\n")

    for skill_name in sorted(fetcher.skills.keys()):
        print(f"  - {skill_name}")

    print(f"\nTotal: {len(fetcher.skills)} skills")

    # Display sample content
    if fetcher.skills:
        first_skill = list(fetcher.skills.keys())[0]
        print(f"\n\nSample content from '{first_skill}':")
        print("-" * 80)
        print(fetcher.skills[first_skill]['content'][:500])
        print("...")


if __name__ == "__main__":
    main()
