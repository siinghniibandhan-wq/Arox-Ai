# Skill: Data, Integrations & Automation (CTO Division)

## Purpose
Enables the CTO agent to connect systems like a head of platform: databases, APIs, webhooks, email and messaging links, n8n workflows, schedulers and background jobs.

## Safety & Governance
- **Risk Level**: Level 1 for reading data and drafting designs.
- **Risk Level**: Level 2 for building or changing a connection or workflow.
- **Risk Level**: Level 3 for any connection that sends messages, moves money, or changes data in another system (MUST pause for owner approval).
- **Default State**: Read-only first. Keys go in a secure store, never in chat or commands.

## Step-by-Step Procedure
1. State the goal: what data moves, from where, to where, how often.
2. Prefer an official API. Use browser automation only when no API exists.
3. Check the data: format, size, personal or financial content, and who may see it.
4. Design the flow: trigger, steps, checks, error handling, retries, and a stop button.
5. Make each run safe to repeat without double sending or double paying.
6. Keep a log of every run and every outside call, with secrets hidden.
7. Add limits: daily caps, rate limits, and alerts for failures.
8. Start with read-only, then a dry run, then a small live run with approval.
9. Plan backup and a way to turn the automation off quickly.
10. Report the design and test results, then notify the owner for approval.
