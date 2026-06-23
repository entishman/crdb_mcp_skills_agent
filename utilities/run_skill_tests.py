#!/usr/bin/env python3
"""
Automated Skill Fetching Test Runner

Runs all 20 test tasks through the agent and verifies each fetches the correct skill.
"""

import subprocess
import sys
import time
import re
from pathlib import Path

# Test cases
test_cases = [
    {
        "id": 1,
        "task": "How do I check if data is evenly distributed across ranges in my cluster?",
        "expected_skill": "observability-and-diagnostics_analyzing-range-distribution",
    },
    {
        "id": 2,
        "task": "What's the best way to assess storage risk before running a schema change?",
        "expected_skill": "observability-and-diagnostics_analyzing-schema-change-storage-risk",
    },
    {
        "id": 3,
        "task": "How can I audit and verify the table statistics in my database?",
        "expected_skill": "observability-and-diagnostics_auditing-table-statistics",
    },
    {
        "id": 4,
        "task": "Show me how to monitor background jobs like backups and schema changes",
        "expected_skill": "observability-and-diagnostics_monitoring-background-jobs",
    },
    {
        "id": 5,
        "task": "I need to profile slow queries by their statement fingerprints",
        "expected_skill": "observability-and-diagnostics_profiling-statement-fingerprints",
    },
    {
        "id": 6,
        "task": "How do I analyze transaction performance using fingerprints?",
        "expected_skill": "observability-and-diagnostics_profiling-transaction-fingerprints",
    },
    {
        "id": 7,
        "task": "Help me triage active SQL queries that might be causing performance issues",
        "expected_skill": "observability-and-diagnostics_triaging-live-sql-activity",
    },
    {
        "id": 8,
        "task": "What is MOLT Fetch and how do I use it for migrations?",
        "expected_skill": "onboarding-and-migrations_molt-fetch",
    },
    {
        "id": 9,
        "task": "I want to set up continuous data replication using MOLT Replicator",
        "expected_skill": "onboarding-and-migrations_molt-replicator",
    },
    {
        "id": 10,
        "task": "How can I verify data consistency after migration with MOLT?",
        "expected_skill": "onboarding-and-migrations_molt-verify",
    },
    {
        "id": 11,
        "task": "Guide me through managing TLS certificates and encryption for my cluster",
        "expected_skill": "operations-and-lifecycle_managing-certificates-and-encryption",
    },
    {
        "id": 12,
        "task": "How do I manage and plan for cluster storage and compute capacity?",
        "expected_skill": "operations-and-lifecycle_managing-cluster-capacity",
    },
    {
        "id": 13,
        "task": "What cluster settings should I configure for optimal performance?",
        "expected_skill": "operations-and-lifecycle_managing-cluster-settings",
    },
    {
        "id": 14,
        "task": "Walk me through performing routine maintenance on my CockroachDB cluster",
        "expected_skill": "operations-and-lifecycle_performing-cluster-maintenance",
    },
    {
        "id": 15,
        "task": "What steps should I take to provision my cluster for production deployment?",
        "expected_skill": "operations-and-lifecycle_provisioning-cluster-for-production",
    },
    {
        "id": 16,
        "task": "How do I review overall cluster health and identify potential issues?",
        "expected_skill": "operations-and-lifecycle_reviewing-cluster-health",
    },
    {
        "id": 17,
        "task": "I need to upgrade my CockroachDB cluster to a newer version safely",
        "expected_skill": "operations-and-lifecycle_upgrading-cluster-version",
    },
    {
        "id": 18,
        "task": "What are the CockroachDB-specific SQL best practices I should follow?",
        "expected_skill": "query-and-schema-design_cockroachdb-sql",
    },
    {
        "id": 19,
        "task": "Help me audit the security posture of my CockroachDB Cloud cluster",
        "expected_skill": "security-and-governance_auditing-cloud-cluster-security",
    },
    {
        "id": 20,
        "task": "How do I enable and configure audit logging for compliance requirements?",
        "expected_skill": "security-and-governance_configuring-audit-logging",
    }
]

# ANSI colors
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'


def run_test(test_case):
    """Run a single test case and check if correct skill was fetched"""
    task_id = test_case["id"]
    task = test_case["task"]
    expected_skill = test_case["expected_skill"]

    print(f"\n{Colors.BLUE}[Test {task_id}/20]{Colors.ENDC} {task[:70]}...")
    print(f"  Expected: {Colors.BOLD}{expected_skill}{Colors.ENDC}")

    try:
        # Create a temporary Python script to run the task
        test_script = f'''
import sys
sys.path.insert(0, '/var/www/ai/aidemo2')
from agent import CockroachDBAgent

agent = CockroachDBAgent(
    verbose=False,
    use_query_learning=False,
    use_vector_search=False
)

# Capture output
import io
from contextlib import redirect_stdout, redirect_stderr

output_buffer = io.StringIO()
error_buffer = io.StringIO()

with redirect_stdout(output_buffer), redirect_stderr(error_buffer):
    result = agent.process_task("{task.replace('"', '\\"')}")

# Print captured output for parsing
print("===OUTPUT===")
print(output_buffer.getvalue())
print("===RESULT===")
print(result)
'''

        # Write temporary script
        with open('/tmp/test_agent_task.py', 'w') as f:
            f.write(test_script)

        # Run the script
        result = subprocess.run(
            ['python3', '/tmp/test_agent_task.py'],
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )

        output = result.stdout + result.stderr

        # Check if expected skill was mentioned in output
        skill_found = expected_skill in output

        # Look for fetch_skill pattern
        fetch_pattern = re.search(r'fetch_skill.*?' + re.escape(expected_skill), output, re.DOTALL)

        if skill_found or fetch_pattern:
            print(f"  {Colors.GREEN}✓ PASS{Colors.ENDC} - Skill fetched: {expected_skill}")
            return True
        else:
            print(f"  {Colors.RED}✗ FAIL{Colors.ENDC} - Expected skill not found in output")
            # Print snippet of output for debugging
            if len(output) > 200:
                print(f"  Output snippet: {output[:200]}...")
            return False

    except subprocess.TimeoutExpired:
        print(f"  {Colors.YELLOW}⚠ TIMEOUT{Colors.ENDC} - Test took too long")
        return False
    except Exception as e:
        print(f"  {Colors.RED}✗ ERROR{Colors.ENDC} - {str(e)}")
        return False


def main():
    print("=" * 100)
    print(f"{Colors.BOLD}AUTOMATED SKILL FETCHING TEST{Colors.ENDC}")
    print("=" * 100)
    print(f"\nTesting {len(test_cases)} tasks to verify unique skill fetching...")
    print("This will take several minutes...\n")

    results = []
    start_time = time.time()

    for test_case in test_cases:
        passed = run_test(test_case)
        results.append({
            "id": test_case["id"],
            "task": test_case["task"],
            "expected": test_case["expected_skill"],
            "passed": passed
        })

        # Small delay between tests
        time.sleep(1)

    elapsed = time.time() - start_time

    # Print summary
    print("\n" + "=" * 100)
    print(f"{Colors.BOLD}TEST RESULTS{Colors.ENDC}")
    print("=" * 100)

    passed_count = sum(1 for r in results if r["passed"])
    failed_count = len(results) - passed_count

    print(f"\n{Colors.GREEN}Passed: {passed_count}{Colors.ENDC}")
    print(f"{Colors.RED}Failed: {failed_count}{Colors.ENDC}")
    print(f"Total: {len(results)}")
    print(f"Time: {elapsed:.1f}s")

    if failed_count > 0:
        print(f"\n{Colors.RED}Failed Tests:{Colors.ENDC}")
        for r in results:
            if not r["passed"]:
                print(f"  [{r['id']:2d}] {r['task'][:60]}")
                print(f"       Expected: {r['expected']}")

    print("\n" + "=" * 100)

    if failed_count == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS PASSED!{Colors.ENDC}")
        print(f"All 20 tasks fetched their unique skills successfully.")
    else:
        print(f"{Colors.YELLOW}Some tests failed. Review output above for details.{Colors.ENDC}")

    print("=" * 100)

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
