# Skill: Code Debugging & Review (CTO Division)

## Purpose
Enables the CTO agent to find the root cause of bugs and review code like a principal engineer: read before changing, prove the cause, fix with the smallest safe change, and prevent repeats.

## Safety & Governance
- **Risk Level**: Level 1 for reading code, logs and drafting a fix plan.
- **Risk Level**: Level 2 for committing code to the repository.
- **Risk Level**: Level 3 for deploying to the live server (MUST pause for owner approval).
- **Default State**: Read-only. Never print secrets. Never change working features without a backup.

## Step-by-Step Procedure
1. Restate the problem in one plain sentence: what was expected, what happened, since when.
2. Reproduce it or find the exact error in the logs. Do not guess before you see evidence.
3. Inspect the current code first. List the files and functions involved.
4. Form 2 or 3 possible causes. Rank them. Design a safe check for each.
5. Prove the real cause with evidence, not a guess.
6. Draft the smallest fix that solves the cause. Do not rewrite working code.
7. Check what else the fix could break: callers, database, login, approvals.
8. Plan a backup, a test that proves the fix, and a way to undo it.
9. Review code for correctness, edge cases, error handling, security and readability.
10. Add a test or check so the bug cannot return unnoticed.
11. Write a short report: cause, fix, test result, risk. Notify the owner before any commit or deploy.
