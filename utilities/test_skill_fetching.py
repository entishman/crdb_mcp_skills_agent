#!/usr/bin/env python3
"""
Skill Fetching Test Script

Tests that 20 different tasks each trigger a unique skill.md file to be fetched.
"""

# Test tasks and their expected skills
test_cases = [
    {
        "id": 1,
        "task": "How do I check if data is evenly distributed across ranges in my cluster?",
        "expected_skill": "observability-and-diagnostics_analyzing-range-distribution",
        "category": "Observability and Diagnostics"
    },
    {
        "id": 2,
        "task": "What's the best way to assess storage risk before running a schema change?",
        "expected_skill": "observability-and-diagnostics_analyzing-schema-change-storage-risk",
        "category": "Observability and Diagnostics"
    },
    {
        "id": 3,
        "task": "How can I audit and verify the table statistics in my database?",
        "expected_skill": "observability-and-diagnostics_auditing-table-statistics",
        "category": "Observability and Diagnostics"
    },
    {
        "id": 4,
        "task": "Show me how to monitor background jobs like backups and schema changes",
        "expected_skill": "observability-and-diagnostics_monitoring-background-jobs",
        "category": "Observability and Diagnostics"
    },
    {
        "id": 5,
        "task": "I need to profile slow queries by their statement fingerprints",
        "expected_skill": "observability-and-diagnostics_profiling-statement-fingerprints",
        "category": "Observability and Diagnostics"
    },
    {
        "id": 6,
        "task": "How do I analyze transaction performance using fingerprints?",
        "expected_skill": "observability-and-diagnostics_profiling-transaction-fingerprints",
        "category": "Observability and Diagnostics"
    },
    {
        "id": 7,
        "task": "Help me triage active SQL queries that might be causing performance issues",
        "expected_skill": "observability-and-diagnostics_triaging-live-sql-activity",
        "category": "Observability and Diagnostics"
    },
    {
        "id": 8,
        "task": "What is MOLT Fetch and how do I use it for migrations?",
        "expected_skill": "onboarding-and-migrations_molt-fetch",
        "category": "Onboarding and Migrations"
    },
    {
        "id": 9,
        "task": "I want to set up continuous data replication using MOLT Replicator",
        "expected_skill": "onboarding-and-migrations_molt-replicator",
        "category": "Onboarding and Migrations"
    },
    {
        "id": 10,
        "task": "How can I verify data consistency after migration with MOLT?",
        "expected_skill": "onboarding-and-migrations_molt-verify",
        "category": "Onboarding and Migrations"
    },
    {
        "id": 11,
        "task": "Guide me through managing TLS certificates and encryption for my cluster",
        "expected_skill": "operations-and-lifecycle_managing-certificates-and-encryption",
        "category": "Operations and Lifecycle"
    },
    {
        "id": 12,
        "task": "How do I manage and plan for cluster storage and compute capacity?",
        "expected_skill": "operations-and-lifecycle_managing-cluster-capacity",
        "category": "Operations and Lifecycle"
    },
    {
        "id": 13,
        "task": "What cluster settings should I configure for optimal performance?",
        "expected_skill": "operations-and-lifecycle_managing-cluster-settings",
        "category": "Operations and Lifecycle"
    },
    {
        "id": 14,
        "task": "Walk me through performing routine maintenance on my CockroachDB cluster",
        "expected_skill": "operations-and-lifecycle_performing-cluster-maintenance",
        "category": "Operations and Lifecycle"
    },
    {
        "id": 15,
        "task": "What steps should I take to provision my cluster for production deployment?",
        "expected_skill": "operations-and-lifecycle_provisioning-cluster-for-production",
        "category": "Operations and Lifecycle"
    },
    {
        "id": 16,
        "task": "How do I review overall cluster health and identify potential issues?",
        "expected_skill": "operations-and-lifecycle_reviewing-cluster-health",
        "category": "Operations and Lifecycle"
    },
    {
        "id": 17,
        "task": "I need to upgrade my CockroachDB cluster to a newer version safely",
        "expected_skill": "operations-and-lifecycle_upgrading-cluster-version",
        "category": "Operations and Lifecycle"
    },
    {
        "id": 18,
        "task": "What are the CockroachDB-specific SQL best practices I should follow?",
        "expected_skill": "query-and-schema-design_cockroachdb-sql",
        "category": "Query and Schema Design"
    },
    {
        "id": 19,
        "task": "Help me audit the security posture of my CockroachDB Cloud cluster",
        "expected_skill": "security-and-governance_auditing-cloud-cluster-security",
        "category": "Security and Governance"
    },
    {
        "id": 20,
        "task": "How do I enable and configure audit logging for compliance requirements?",
        "expected_skill": "security-and-governance_configuring-audit-logging",
        "category": "Security and Governance"
    }
]


def print_test_summary():
    """Print summary of all test cases"""
    print("=" * 100)
    print("SKILL FETCHING TEST - 20 UNIQUE TASKS")
    print("=" * 100)
    print()

    # Group by category
    by_category = {}
    for test in test_cases:
        category = test["category"]
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(test)

    for category, tests in sorted(by_category.items()):
        print(f"\n{category} ({len(tests)} tasks):")
        print("-" * 100)
        for test in tests:
            print(f"  [{test['id']:2d}] {test['task'][:75]}")
            print(f"       → Expected: {test['expected_skill']}")

    print("\n" + "=" * 100)
    print(f"Total: {len(test_cases)} unique tasks")
    print("=" * 100)
    print()

    # Check for duplicate skills
    skills = [t["expected_skill"] for t in test_cases]
    unique_skills = set(skills)

    if len(skills) == len(unique_skills):
        print(f"✅ SUCCESS: All {len(skills)} skills are unique!")
    else:
        print(f"❌ ERROR: Found {len(skills) - len(unique_skills)} duplicate skills!")
        duplicates = [s for s in skills if skills.count(s) > 1]
        print(f"   Duplicates: {set(duplicates)}")

    print()


def print_tasks_for_manual_testing():
    """Print tasks in a format easy to copy/paste for manual testing"""
    print("\n" + "=" * 100)
    print("COPY/PASTE TASKS FOR MANUAL TESTING")
    print("=" * 100)
    print("\nRun: python3 agent.py")
    print("\nThen copy/paste each task below:\n")

    for test in test_cases:
        print(f"# Task {test['id']}: {test['expected_skill']}")
        print(test['task'])
        print()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--manual":
        print_tasks_for_manual_testing()
    else:
        print_test_summary()
        print("\nTo get tasks for manual testing, run:")
        print("  python3 test_skill_fetching.py --manual")
        print()
