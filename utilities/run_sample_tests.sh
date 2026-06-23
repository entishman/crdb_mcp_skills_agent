#!/bin/bash
# Run 3 sample skill tests from different categories

echo "=================================================================================================="
echo "SAMPLE SKILL FETCHING TESTS (3 tasks from different categories)"
echo "=================================================================================================="
echo ""
echo "This tests a sample of tasks to verify the skill fetching works correctly."
echo "Each test will run the agent and check if the expected skill is fetched."
echo ""

# Test 1: Observability
echo ""
echo "[Test 1/3] Observability and Diagnostics"
echo "Task: Help me triage active SQL queries that might be causing performance issues"
echo "Expected skill: observability-and-diagnostics_triaging-live-sql-activity"
echo "--------------------------------------------------------------------------------"
python3 - << 'EOF'
import sys
sys.path.insert(0, '/var/www/ai/aidemo2')
from agent import CockroachDBAgent
import io
from contextlib import redirect_stdout

agent = CockroachDBAgent(verbose=False, use_query_learning=False, use_vector_search=False)
output_buffer = io.StringIO()

print("Running agent...")
with redirect_stdout(output_buffer):
    result = agent.process_task("Help me triage active SQL queries that might be causing performance issues")

output = output_buffer.getvalue()
expected = "observability-and-diagnostics_triaging-live-sql-activity"

if expected in output or expected in result:
    print(f"✓ PASS - Skill '{expected}' was fetched")
else:
    print(f"✗ FAIL - Expected skill not found")
    print(f"Result preview: {result[:200]}...")
EOF

sleep 2

# Test 2: Migrations
echo ""
echo "[Test 2/3] Onboarding and Migrations"
echo "Task: What is MOLT Fetch and how do I use it for migrations?"
echo "Expected skill: onboarding-and-migrations_molt-fetch"
echo "--------------------------------------------------------------------------------"
python3 - << 'EOF'
import sys
sys.path.insert(0, '/var/www/ai/aidemo2')
from agent import CockroachDBAgent
import io
from contextlib import redirect_stdout

agent = CockroachDBAgent(verbose=False, use_query_learning=False, use_vector_search=False)
output_buffer = io.StringIO()

print("Running agent...")
with redirect_stdout(output_buffer):
    result = agent.process_task("What is MOLT Fetch and how do I use it for migrations?")

output = output_buffer.getvalue()
expected = "onboarding-and-migrations_molt-fetch"

if expected in output or expected in result:
    print(f"✓ PASS - Skill '{expected}' was fetched")
else:
    print(f"✗ FAIL - Expected skill not found")
    print(f"Result preview: {result[:200]}...")
EOF

sleep 2

# Test 3: Operations
echo ""
echo "[Test 3/3] Operations and Lifecycle"
echo "Task: How do I review overall cluster health and identify potential issues?"
echo "Expected skill: operations-and-lifecycle_reviewing-cluster-health"
echo "--------------------------------------------------------------------------------"
python3 - << 'EOF'
import sys
sys.path.insert(0, '/var/www/ai/aidemo2')
from agent import CockroachDBAgent
import io
from contextlib import redirect_stdout

agent = CockroachDBAgent(verbose=False, use_query_learning=False, use_vector_search=False)
output_buffer = io.StringIO()

print("Running agent...")
with redirect_stdout(output_buffer):
    result = agent.process_task("How do I review overall cluster health and identify potential issues?")

output = output_buffer.getvalue()
expected = "operations-and-lifecycle_reviewing-cluster-health"

if expected in output or expected in result:
    print(f"✓ PASS - Skill '{expected}' was fetched")
else:
    print(f"✗ FAIL - Expected skill not found")
    print(f"Result preview: {result[:200]}...")
EOF

echo ""
echo "=================================================================================================="
echo "SAMPLE TESTS COMPLETE"
echo "=================================================================================================="
echo ""
echo "To run all 20 tests: python3 run_skill_tests.py"
echo "(Warning: This will take 10-20 minutes and use significant API credits)"
echo ""
