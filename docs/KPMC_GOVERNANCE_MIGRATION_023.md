# KPMC governance migration 023

## Scope and separation
This is an additive migration for the existing PostgreSQL 16 AI database (app_db) only. It creates a separate kpmc_gov schema. It does not connect to or modify Superbajaar's PostgreSQL 15 sb_app database, the existing ai schema objects, the AROX orchestrator source, existing Docker containers, network rules, or AWS resources.

## Objects
- brands and connectors: brand-scoped connector registry; connector credentials are represented only by an opaque credential_ref, never stored in this database migration.
- data_classes and group_policies: classification and per-brand group policy registry. Critical classification requires owner approval.
- provider_allowlist: provider host/model/data-class allowlist; providers are disabled until reviewed and explicitly activated.
- approval_requests and approval_decisions: approval queue with a 24-hour expiry default and immutable decisions.
- executor_runs: idempotent, attempt-tracked executor run registry.
- audit_events: append-only governance audit history.

## Access
Two NOLOGIN group roles are created: kpmc_control_role and kpmc_executor_role. The owner must provision LOGIN members and keep credentials outside Git/source code. The AI orchestrator receives no access to kpmc_gov. It loses only direct DELETE and TRUNCATE on ai.audit_log and ai.approvals; its other privileges are not changed. No blanket table or sequence grants are used.

## Important enforcement boundary
This migration establishes the data model and database permissions. It does not by itself implement owner identity verification, critical-data access checks, automatic expiry processing, Telegram approval cards, provider proxy enforcement, or an executor API. Those must be enforced by the separate kpmc-control and kpmc-executor services before any production use. Expired requests must be treated as rejected/no by those services; a pending row past expires_at is not an approval.

## Verification
The new GitHub Actions workflow starts a disposable pgvector/PostgreSQL 16 database, applies 022 once, applies 023 twice, and verifies:
- orchestrator DELETE/TRUNCATE are revoked only on ai.audit_log and ai.approvals;
- existing SELECT/INSERT privileges remain;
- the orchestrator has no direct kpmc_gov schema access;
- the two service roles have only their declared grants;
- audit events and approval decisions reject UPDATE/DELETE.

No production backup, migration, smoke test or live container change is performed by CI.

## Rollback
The migration is additive and must not be edited or removed after application. The permission-only rollback is:
GRANT DELETE, TRUNCATE ON TABLE ai.audit_log, ai.approvals TO ai_orchestrator_role;

Do not drop the kpmc_gov schema or its tables as a routine rollback. If an approved rollback is required, use a separately reviewed forward migration that first disables the new service integration and restores only the intended grants.
