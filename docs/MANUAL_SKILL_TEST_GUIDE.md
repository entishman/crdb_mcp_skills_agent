# Manual Skill Fetching Test Guide

## Quick Manual Testing (Recommended)

Since automated testing has subprocess issues, use this manual approach:

### Setup:
```bash
cd /var/www/ai/aidemo2
python3 agent.py
```

### Test These 5 Tasks (Copy/Paste One at a Time):

#### Test 1: Observability
```
Help me triage active SQL queries that might be causing performance issues
```
**Expected**: Fetches `observability-and-diagnostics_triaging-live-sql-activity`

#### Test 2: Migrations  
```
What is MOLT Fetch and how do I use it for migrations?
```
**Expected**: Fetches `onboarding-and-migrations_molt-fetch`

#### Test 3: Operations
```
How do I review overall cluster health and identify potential issues?
```
**Expected**: Fetches `operations-and-lifecycle_reviewing-cluster-health`

#### Test 4: Security
```
Help me audit the security posture of my CockroachDB Cloud cluster
```
**Expected**: Fetches `security-and-governance_auditing-cloud-cluster-security`

#### Test 5: Schema Design
```
What are the CockroachDB-specific SQL best practices I should follow?
```
**Expected**: Fetches `query-and-schema-design_cockroachdb-sql`

### How to Verify:

Watch the agent output for lines like:
```
→ Claude is calling tool: fetch_skill
  Input: {
    "skill_name": "observability-and-diagnostics_triaging-live-sql-activity"
  }
```

Each task should fetch a DIFFERENT skill.

### Full 20-Task List:

See `SKILL_TEST_TASKS.md` for all 20 tasks if you want to test more.
