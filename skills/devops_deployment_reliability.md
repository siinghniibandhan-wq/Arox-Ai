# Skill: DevOps, Deployment & Reliability (CTO Division)

## Purpose
Enables the CTO agent to run servers and releases like a head of infrastructure: safe deploys, Docker and compose changes, backups, monitoring, rollbacks and incident response.

## Safety & Governance
- **Risk Level**: Level 1 for reading logs, status and drafting plans.
- **Risk Level**: Level 2 for committing config or code changes.
- **Risk Level**: Level 3 for any live deploy, restart, rebuild or database change (MUST pause for owner approval).
- **Default State**: Read-only. Never print secrets. Secrets live in a secure store, never in a command or chat.

## Step-by-Step Procedure
1. State what will change, which service it touches, and what the downtime will be.
2. Check the current health first: container status, logs, disk, memory.
3. Take a backup of the files and data that will change. Confirm the backup exists.
4. Change only the one service needed. Never rebuild everything without a reason.
5. Prepare the exact commands, short and safe for phone copy-paste.
6. Define a check that proves success, and a one-command rollback.
7. After the change, check health, logs, and one real test of the feature.
8. Watch for problems: restarts, errors, slow replies, full disk, expired certificates.
9. During an incident: stop the damage first, find the cause second, fix third, write notes last.
10. Keep backups automatic, and test a restore regularly.
11. Report: what changed, what was verified, what is not verified, next step. Notify the owner.
