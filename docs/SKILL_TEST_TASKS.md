# 20 Tasks to Test Skill.md File Fetching

## Purpose
Test that each task triggers the agent to fetch a unique skill.md file based on the query content.

## Test Date
2026-04-05

---

## Tasks and Expected Skills

### 1. Range Distribution Analysis
**Task**: "How do I check if data is evenly distributed across ranges in my cluster?"
**Expected Skill**: `observability-and-diagnostics_analyzing-range-distribution`
**Category**: Observability and Diagnostics

---

### 2. Schema Change Storage Impact
**Task**: "What's the best way to assess storage risk before running a schema change?"
**Expected Skill**: `observability-and-diagnostics_analyzing-schema-change-storage-risk`
**Category**: Observability and Diagnostics

---

### 3. Table Statistics Review
**Task**: "How can I audit and verify the table statistics in my database?"
**Expected Skill**: `observability-and-diagnostics_auditing-table-statistics`
**Category**: Observability and Diagnostics

---

### 4. Background Jobs Monitoring
**Task**: "Show me how to monitor background jobs like backups and schema changes"
**Expected Skill**: `observability-and-diagnostics_monitoring-background-jobs`
**Category**: Observability and Diagnostics

---

### 5. Statement Performance Profiling
**Task**: "I need to profile slow queries by their statement fingerprints"
**Expected Skill**: `observability-and-diagnostics_profiling-statement-fingerprints`
**Category**: Observability and Diagnostics

---

### 6. Transaction Performance Analysis
**Task**: "How do I analyze transaction performance using fingerprints?"
**Expected Skill**: `observability-and-diagnostics_profiling-transaction-fingerprints`
**Category**: Observability and Diagnostics

---

### 7. Live SQL Activity Diagnosis
**Task**: "Help me triage active SQL queries that might be causing performance issues"
**Expected Skill**: `observability-and-diagnostics_triaging-live-sql-activity`
**Category**: Observability and Diagnostics

---

### 8. MOLT Fetch Tool Usage
**Task**: "What is MOLT Fetch and how do I use it for migrations?"
**Expected Skill**: `onboarding-and-migrations_molt-fetch`
**Category**: Onboarding and Migrations

---

### 9. MOLT Replicator Setup
**Task**: "I want to set up continuous data replication using MOLT Replicator"
**Expected Skill**: `onboarding-and-migrations_molt-replicator`
**Category**: Onboarding and Migrations

---

### 10. MOLT Verify Data Validation
**Task**: "How can I verify data consistency after migration with MOLT?"
**Expected Skill**: `onboarding-and-migrations_molt-verify`
**Category**: Onboarding and Migrations

---

### 11. Certificate and Encryption Management
**Task**: "Guide me through managing TLS certificates and encryption for my cluster"
**Expected Skill**: `operations-and-lifecycle_managing-certificates-and-encryption`
**Category**: Operations and Lifecycle

---

### 12. Cluster Capacity Planning
**Task**: "How do I manage and plan for cluster storage and compute capacity?"
**Expected Skill**: `operations-and-lifecycle_managing-cluster-capacity`
**Category**: Operations and Lifecycle

---

### 13. Cluster Settings Configuration
**Task**: "What cluster settings should I configure for optimal performance?"
**Expected Skill**: `operations-and-lifecycle_managing-cluster-settings`
**Category**: Operations and Lifecycle

---

### 14. Cluster Maintenance Tasks
**Task**: "Walk me through performing routine maintenance on my CockroachDB cluster"
**Expected Skill**: `operations-and-lifecycle_performing-cluster-maintenance`
**Category**: Operations and Lifecycle

---

### 15. Production Readiness Checklist
**Task**: "What steps should I take to provision my cluster for production deployment?"
**Expected Skill**: `operations-and-lifecycle_provisioning-cluster-for-production`
**Category**: Operations and Lifecycle

---

### 16. Cluster Health Review
**Task**: "How do I review overall cluster health and identify potential issues?"
**Expected Skill**: `operations-and-lifecycle_reviewing-cluster-health`
**Category**: Operations and Lifecycle

---

### 17. Cluster Version Upgrade
**Task**: "I need to upgrade my CockroachDB cluster to a newer version safely"
**Expected Skill**: `operations-and-lifecycle_upgrading-cluster-version`
**Category**: Operations and Lifecycle

---

### 18. SQL Best Practices
**Task**: "What are the CockroachDB-specific SQL best practices I should follow?"
**Expected Skill**: `query-and-schema-design_cockroachdb-sql`
**Category**: Query and Schema Design

---

### 19. Cloud Cluster Security Audit
**Task**: "Help me audit the security posture of my CockroachDB Cloud cluster"
**Expected Skill**: `security-and-governance_auditing-cloud-cluster-security`
**Category**: Security and Governance

---

### 20. Audit Logging Configuration
**Task**: "How do I enable and configure audit logging for compliance requirements?"
**Expected Skill**: `security-and-governance_configuring-audit-logging`
**Category**: Security and Governance

---

## How to Test

### Manual Testing (Individual Tasks)
```bash
cd /var/www/ai/aidemo2
python3 agent.py
```

Then enter each task one at a time and verify:
1. Agent calls `fetch_skill` tool
2. The correct skill.md file is fetched
3. Agent uses the skill content to answer the question

### Automated Testing Script
Create a test script to run all 20 tasks and log which skills are fetched:

```python
#!/usr/bin/env python3
import json
import subprocess

tasks = [
    "How do I check if data is evenly distributed across ranges in my cluster?",
    "What's the best way to assess storage risk before running a schema change?",
    "How can I audit and verify the table statistics in my database?",
    "Show me how to monitor background jobs like backups and schema changes",
    "I need to profile slow queries by their statement fingerprints",
    "How do I analyze transaction performance using fingerprints?",
    "Help me triage active SQL queries that might be causing performance issues",
    "What is MOLT Fetch and how do I use it for migrations?",
    "I want to set up continuous data replication using MOLT Replicator",
    "How can I verify data consistency after migration with MOLT?",
    "Guide me through managing TLS certificates and encryption for my cluster",
    "How do I manage and plan for cluster storage and compute capacity?",
    "What cluster settings should I configure for optimal performance?",
    "Walk me through performing routine maintenance on my CockroachDB cluster",
    "What steps should I take to provision my cluster for production deployment?",
    "How do I review overall cluster health and identify potential issues?",
    "I need to upgrade my CockroachDB cluster to a newer version safely",
    "What are the CockroachDB-specific SQL best practices I should follow?",
    "Help me audit the security posture of my CockroachDB Cloud cluster",
    "How do I enable and configure audit logging for compliance requirements?"
]

expected_skills = [
    "observability-and-diagnostics_analyzing-range-distribution",
    "observability-and-diagnostics_analyzing-schema-change-storage-risk",
    "observability-and-diagnostics_auditing-table-statistics",
    "observability-and-diagnostics_monitoring-background-jobs",
    "observability-and-diagnostics_profiling-statement-fingerprints",
    "observability-and-diagnostics_profiling-transaction-fingerprints",
    "observability-and-diagnostics_triaging-live-sql-activity",
    "onboarding-and-migrations_molt-fetch",
    "onboarding-and-migrations_molt-replicator",
    "onboarding-and-migrations_molt-verify",
    "operations-and-lifecycle_managing-certificates-and-encryption",
    "operations-and-lifecycle_managing-cluster-capacity",
    "operations-and-lifecycle_managing-cluster-settings",
    "operations-and-lifecycle_performing-cluster-maintenance",
    "operations-and-lifecycle_provisioning-cluster-for-production",
    "operations-and-lifecycle_reviewing-cluster-health",
    "operations-and-lifecycle_upgrading-cluster-version",
    "query-and-schema-design_cockroachdb-sql",
    "security-and-governance_auditing-cloud-cluster-security",
    "security-and-governance_configuring-audit-logging"
]

print("=" * 80)
print("SKILL FETCHING TEST - 20 Tasks")
print("=" * 80)
print()

for i, (task, expected_skill) in enumerate(zip(tasks, expected_skills), 1):
    print(f"\n[{i}/20] Testing: {task[:60]}...")
    print(f"Expected Skill: {expected_skill}")
    print("-" * 80)
    # Note: Actual implementation would need to capture agent output
    # and parse for fetch_skill calls to verify correct skill was fetched

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
```

---

## Expected Results

Each task should:
1. ✅ Trigger a `fetch_skill` tool call
2. ✅ Fetch a UNIQUE skill.md file (no duplicates across the 20 tasks)
3. ✅ Use the skill content to provide an informed answer
4. ✅ Call `complete_task` with the skill name in `skills_that_helped` array

## Validation

After running all 20 tasks:
- [ ] 20 unique skills were fetched (no duplicates)
- [ ] Each skill matches the expected skill for that task
- [ ] Agent provided relevant answers using skill content
- [ ] No errors or failed skill fetches

---

## Additional Skills Available (Not Tested)

These 5 skills are available but not included in the 20 test tasks:
1. `security-and-governance_configuring-ip-allowlists`
2. `security-and-governance_configuring-log-export`
3. `security-and-governance_configuring-private-connectivity`
4. `security-and-governance_configuring-sso-and-scim`
5. `security-and-governance_enabling-cmek-encryption`

Use these for additional testing or as backups if needed.

---

## Notes

- Tasks are designed to naturally trigger skill fetching without explicitly mentioning skill names
- Each task focuses on a specific domain that maps to one primary skill
- Questions are phrased as realistic user queries
- Testing should be done with verbose mode enabled to see fetch_skill calls
- Results should be logged to verify skill uniqueness
