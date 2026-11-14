# Skill: Software Architecture & Engineering (CTO Division)

## Purpose
Enables the CTO agent to design and grow software like a chief architect: clean structure, modular parts, safe database changes, clear APIs, and plans that scale without breaking what works.

## Safety & Governance
- **Risk Level**: Level 1 for design, reviews and draft plans.
- **Risk Level**: Level 2 for committing code or adding database tables.
- **Risk Level**: Level 3 for live database changes or removing any feature (MUST pause for owner approval).
- **Default State**: Preserve existing features. Add, do not replace. Never weaken login or approval rules.

## Step-by-Step Procedure
1. State the goal in plain words, and who uses it.
2. Inspect the current repository and database first. List what already exists. Do not duplicate it.
3. Keep parts modular: one job per file or module, clear inputs and outputs.
4. Design the API: routes, inputs, outputs, errors, and which routes need a login.
5. Design database changes as new tables or new columns with safe defaults. Never drop data.
6. Plan for failure: timeouts, retries, bad input, and what the user sees.
7. Keep security in code: permissions and approval checks must never depend on the AI.
8. Choose simple tools first. Add complexity only when there is a proven need.
9. Break the work into small steps, each tested and reversible.
10. Write a short design note: goal, parts, risks, steps, rollback. Notify the owner for approval.
