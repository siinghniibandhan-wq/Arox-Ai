# AROX — AI Development Assistant

**AROX** is an AI-assisted engineering assistant being built in the `KPMC-Ai` repository. Its goal is to help inspect, build, test, review, and maintain Financial OS and other projects while keeping each repository isolated.

> AROX is the product name. `KPMC-Ai` remains the GitHub repository name.

## Mission

- Inspect existing code and documentation before proposing changes.
- Turn approved requirements into small, reviewable changes.
- Add and run relevant tests where the environment permits.
- Report exactly what changed, what was tested, and what remains unverified.
- Keep project boundaries, credentials, and production data protected.

## Operating principles

1. **Inspect before editing.** Understand the target repository and current implementation first.
2. **Preserve working behavior.** Prefer focused changes; do not rewrite unrelated modules.
3. **Separate repositories.** AROX is the assistant/tooling project. Financial OS remains in its own repository with its own database, deployment, and configuration.
4. **No secrets in Git.** Never commit API keys, tokens, passwords, private keys, database URLs, or production data. Use environment variables or an approved secret manager.
5. **Test before merging.** Run applicable checks and report their results honestly.
6. **Human approval for high-impact actions.** Do not deploy, alter production infrastructure, change repository visibility, or make destructive data changes without explicit approval.
7. **Least privilege.** Grant AROX access only to repositories and operations it needs. Repository access does not imply that every action is safe or supported.
8. **Traceable changes.** Use small commits with clear messages and summarize changed files and test evidence.

## Planned capabilities

- Repository and documentation inspection.
- AI model integration behind a provider-independent interface.
- Controlled code editing and test execution.
- Change summaries and code review assistance.
- Multi-repository project context with strict separation.
- Optional Git operations and deployment assistance, with approval gates.

These are planned capabilities; they are not all implemented yet.

## Financial OS boundary

Financial OS is a separate project. Its existing working functionality must be preserved. Deterministic, tested code should remain responsible for financial calculations; AI may assist with explanations, coding, and information gathering. Never copy Financial OS secrets, user financial data, or production configuration into this repository.

## Development status

AROX is at the initial setup stage. This README describes the intended direction; it does not mean an AI model, autonomous agent, repository automation, or deployment has already been implemented.

## Roadmap

1. Establish the execution environment and secure configuration.
2. Add a minimal application skeleton and configuration validation.
3. Add tests for safety boundaries and repository separation.
4. Integrate one AI model behind a provider-independent interface.
5. Begin with read-only repository inspection.
6. Add controlled edits, tests, and Git operations incrementally.

## License

No license has been selected yet. Until a license is added, do not assume this project's code is licensed for reuse by others.
