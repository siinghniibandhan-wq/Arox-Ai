# KPMC Ai

KPMC Ai is an AI-assisted engineering workspace intended to help build, test, review, and maintain Financial OS and other projects while keeping each repository isolated.

## Mission

- Help inspect existing code and documentation before proposing changes.
- Turn approved requirements into small, reviewable changes.
- Add and run relevant tests where the environment permits.
- Report exactly what changed, what was tested, and what remains unverified.
- Keep project boundaries, credentials, and production data protected.

## Operating principles

1. **Inspect before editing.** Understand the target repository and current implementation first.
2. **Preserve working behavior.** Prefer focused changes; do not rewrite unrelated modules.
3. **Separate repositories.** KPMC Ai is the assistant/tooling project. Financial OS remains in its own repository and retains its own database, deployment, and configuration.
4. **No secrets in Git.** Never commit API keys, tokens, passwords, private keys, database URLs, or production data. Use environment variables or an approved secret manager.
5. **Test before merging.** Run applicable checks and report their results honestly.
6. **Review before production actions.** Do not deploy, alter production infrastructure, or make destructive data changes without explicit approval.
7. **Traceable changes.** Use small commits with clear messages and summarize changed files and test evidence.

## Initial project focus

- Define a safe, repeatable AI-assisted development workflow.
- Add provider-independent interfaces for AI models rather than tying the project to one provider.
- Add controlled, least-privilege access to project context.
- Introduce repository inspection, test execution, and change-review capabilities incrementally.
- Keep human approval in the loop for writes, merges, and deployments.

## Financial OS boundary

Financial OS is a separate project. Its existing working functionality must be preserved. In particular, avoid replacing financial calculations with AI-generated answers: deterministic, tested code should remain responsible for calculations, while AI may assist with explanations and information gathering. Do not copy Financial OS secrets, user financial data, or production configuration into this repository.

## Development status

This repository is at its initial setup stage. The README documents the intended direction; it does not mean an AI agent, model integration, repository automation, or deployment has already been implemented.

## Next steps

1. Agree on the first supported workflow and execution environment.
2. Add a minimal application skeleton and configuration validation.
3. Add tests for safety boundaries and repository separation.
4. Add one model provider behind a provider-independent interface.
5. Add read-only repository inspection before considering controlled write access.

## License

No license has been selected yet. Until a license is added, do not assume this project's code is licensed for reuse by others.
