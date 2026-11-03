# KPMC Governance Services — Design Specification
Date: 2026-11-03
Repository: siinghniibandhan-wq/KPMC-Ai
Base: main, via feature branch feature/kpmc-governance-control-plane-023-20261103
Status: Design proposal for review; not implementation approval.

## 1. Purpose and scope
Build an isolated governance control plane for KPMC-Ai. It will manage trusted identities, approval requests, policy decisions, and execution of explicitly registered actions. It must not change the existing AROX/AI Workforce orchestrator behavior during the first release.
This is a KPMC-Ai-only design. It does not modify or connect to Superbajaar or its PostgreSQL 15 sb_app database.
The work is split into separately reviewable slices: (1) Control API and authenticated owner decisions; (2) Executor worker with safe claiming, idempotency, leases, and execution records; (3) Runtime policy enforcement for brand, group, data class, and provider; (4) Telegram approval delivery after identity mapping is agreed.
The first deliverable is the Control API; executor and integrations remain disabled until independently reviewed.

## 2. Approaches considered
### A. Extend the existing orchestrator
Lowest initial deployment effort, but increases blast radius, couples approval logic to existing dispatch routes, and risks changing working AROX behavior.
### B. Separate control and executor services (recommended)
Two small FastAPI services with separate database credentials and deployment configurations. The control service owns approval decisions; the executor can only claim approved work and record execution. Existing orchestrator remains unchanged. This is the recommended isolation and rollback boundary.
### C. External workflow engine first
Could provide durable queues and human approval primitives, but introduces a new runtime and operational dependency before the core identity and policy contracts are stable.

## 3. Architecture
- services/kpmc_control/: independent FastAPI application for authenticated request intake, approval listing, approve/reject decisions, expiry handling, and audit writes.
- services/kpmc_executor/: independent worker/API for claiming approved jobs and running registered handlers.
- services/kpmc_policy/: shared pure policy module; evaluates brand, requester group, action key, data class, risk, provider, and approval requirements. It must fail closed.
- Existing app/main.py, existing AROX routes, Docker Compose files, production containers, and environment configuration remain unchanged in this phase.
- Each service gets its own dependency manifest and deployment recipe. No service is added to the existing Compose stack until a separate deployment approval.

## 4. Identity and authorization
- Owner decisions require authenticated credentials supplied through deployment secrets, never request-body identity claims.
- Compare bearer credentials in constant time; never log tokens.
- The authenticated principal is derived from credential-to-principal configuration, not caller-supplied decided_by.
- Control API endpoints are deny-by-default. Missing, malformed, expired, or unknown credentials are rejected.
- Service-to-service request creation must authenticate the calling service. Do not trust arbitrary requester_id or requester_group fields without a verified service identity.
- Executor credentials cannot approve, reject, or alter approval decisions.
- Telegram is deferred until the owner account and Telegram user/chat identity mapping are explicitly configured and verified.

## 5. Approval lifecycle and data flow
1. An authenticated internal caller submits an action request with brand, action key, target reference, risk, data-class, idempotency key, and a redacted payload.
2. The service validates payload shape and computes the canonical payload digest server-side. It does not accept a caller-provided digest as authoritative.
3. Policy evaluation checks brand state, group policy, data class, provider allowlist, and risk. Unknown policy or provider state fails closed.
4. Actions requiring approval create a pending request with a bounded expiry. Critical data/actions require owner approval.
5. Owner approval/rejection is a single atomic transaction: lock the request row, verify it is pending and unexpired, insert exactly one immutable decision, update request status, and append audit event.
6. A pending request past expiry is never treated as approved. Expiry is enforced synchronously during reads/decisions and by a periodic cleanup task; the executor independently checks expiry before claiming.
7. Only approved, unexpired, policy-valid requests may be claimed by the executor.

## 6. Executor safety
- Claim rows transactionally using row locks (FOR UPDATE SKIP LOCKED) and a bounded lease.
- Enforce unique idempotency at both approval request and executor-run levels.
- Use a fixed action-handler registry. No arbitrary shell, Python, SQL, URL fetch, or unrestricted API execution.
- First release supports dry-run/no-op handlers only. External write handlers require separate connector-specific design, scoped credentials, policy tests, and explicit approval.
- Re-check approval status, expiry, payload digest, brand status, and policy immediately before execution.
- Persist attempt number, lease/claim owner, start/end timestamps, outcome, and redacted result summary.
- Retry only classified transient failures within a configured attempt limit. Unknown errors fail closed and require review.
- Executor cannot mutate immutable approval decisions or audit history.

## 7. Database contract and migration follow-up
Migration 023 is the additive foundation in kpmc_gov. Do not edit it after it has been published/applied. Before service implementation, review and add a new numbered migration if necessary for narrowly scoped grants or fields; never rewrite migration 023.
Known boundary: migration 023 grants the executor SELECT on approval requests and UPDATE on executor_runs, but does not grant it UPDATE on approval_requests. The initial executor therefore records execution in executor_runs and must not directly change approval_requests. If lifecycle status updates are required, they must be performed by the control service through an authenticated internal callback or a separately reviewed least-privilege migration.
Service database URLs must map to separate LOGIN members of kpmc_control_role and kpmc_executor_role. Credentials are provisioned outside Git. A production preflight must verify effective privileges, role membership, ownership, and superuser status; direct REVOKE statements alone do not neutralize inherited privileges or object ownership.

## 8. API boundary (initial proposal)
Control API: GET /health (liveness only); POST /v1/approval-requests (authenticated service-to-service intake); GET /v1/approval-requests (owner-only paginated queue); POST /v1/approval-requests/{id}/decision (owner-only approve/reject with reason and idempotency protection); GET /v1/approval-requests/{id} (owner-only detail, redacted by default).
Executor: no public endpoint in the first release. A worker process polls/claims through its restricted database role. Dry-run action handlers only; no outbound connector writes.
Exact request/response schemas and error codes will be specified in the implementation plan after this design is approved.

## 9. Failure handling and observability
- Fail closed on DB outage, invalid identity, unknown policy, missing connector, expired approval, digest mismatch, or handler not registered.
- Use structured logs with correlation IDs and redaction. Never log authorization headers, credentials, raw sensitive payloads, or provider secrets.
- Audit all request creation, policy outcomes, owner decisions, expiry transitions, claims, execution attempts, and failures.
- Readiness checks verify DB connectivity and required schema version; liveness checks do not leak infrastructure detail.
- No automatic fallback to the existing orchestrator or an unapproved provider.

## 10. Testing and acceptance criteria
- Unit tests for authentication, authorization, canonical digest, expiry, policy evaluation, redaction, and action allowlisting.
- PostgreSQL integration tests for concurrent decisions, duplicate idempotency keys, row-lock behavior, immutable history, and least-privilege database roles.
- Executor tests proving pending/rejected/expired requests cannot be claimed and duplicate claims cannot execute twice.
- Negative tests for arbitrary shell/URL/code execution and unregistered action keys.
- Regression tests proving existing app/main.py routes and existing orchestrator tests remain unchanged.
- CI runs on disposable PostgreSQL 16 only. No production database or cloud resource is touched.
- Acceptance: all tests pass, security scan passes, no changes to existing orchestrator runtime, no secrets in Git, and an operator-reviewed deployment/rollback runbook exists.

## 11. Rollout and rollback
- Merge and deployment are separate decisions. This design does not authorize either.
- First deploy, if separately approved, runs the control API in an isolated disabled/private environment with no executor and no connector writes.
- Enable authenticated request intake only after owner identity and service identity are provisioned and verified.
- Add the dry-run executor only after concurrency and least-privilege tests pass.
- Telegram and external write handlers are later, separate approvals.
- Rollback disables the new service processes and revokes their credentials. Do not drop kpmc_gov data or rewrite applied migrations. Preserve audit and approval history.

## 12. Explicit non-goals
- No changes to Superbajaar.
- No changes to existing AROX/AI Workforce dispatch behavior.
- No production deployment, container restart, DB migration, environment-variable update, network/security-group change, or credential creation.
- No arbitrary agent tool execution, unrestricted browser access, or automatic external writes.