-- 023_kpmc_governance.sql
-- Additive KPMC governance registry for the separate PostgreSQL 16 app_db.
-- Does not alter the existing AROX orchestrator, ai schema, or Superbajaar DB.
-- No secrets or login passwords are stored here.

CREATE SCHEMA IF NOT EXISTS kpmc_gov;

DO $roles$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'kpmc_control_role') THEN
        CREATE ROLE kpmc_control_role NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'kpmc_executor_role') THEN
        CREATE ROLE kpmc_executor_role NOLOGIN;
    END IF;
END
$roles$;

CREATE TABLE IF NOT EXISTS kpmc_gov.brands (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_key text NOT NULL UNIQUE,
    display_name text NOT NULL,
    status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','suspended','retired')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (length(trim(brand_key)) > 0),
    CHECK (length(trim(display_name)) > 0)
);

CREATE TABLE IF NOT EXISTS kpmc_gov.data_classes (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    class_key text NOT NULL UNIQUE,
    display_name text NOT NULL,
    sensitivity_rank smallint NOT NULL CHECK (sensitivity_rank BETWEEN 0 AND 3),
    requires_owner_approval boolean NOT NULL DEFAULT false,
    description text NOT NULL DEFAULT '',
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (length(trim(class_key)) > 0),
    CHECK (length(trim(display_name)) > 0),
    CHECK (sensitivity_rank < 3 OR requires_owner_approval)
);

CREATE TABLE IF NOT EXISTS kpmc_gov.connectors (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id uuid NOT NULL REFERENCES kpmc_gov.brands(id) ON DELETE RESTRICT,
    connector_key text NOT NULL,
    display_name text NOT NULL,
    connector_type text NOT NULL,
    data_class_id uuid NOT NULL REFERENCES kpmc_gov.data_classes(id) ON DELETE RESTRICT,
    access_mode text NOT NULL DEFAULT 'read_only' CHECK (access_mode IN ('read_only','approved_write')),
    status text NOT NULL DEFAULT 'disabled' CHECK (status IN ('disabled','active','suspended')),
    credential_ref text,
    configuration jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (brand_id, connector_key),
    CHECK (length(trim(connector_key)) > 0),
    CHECK (length(trim(display_name)) > 0),
    CHECK (length(trim(connector_type)) > 0),
    CHECK (credential_ref IS NULL OR length(trim(credential_ref)) > 0),
    CHECK (jsonb_typeof(configuration) = 'object')
);

CREATE TABLE IF NOT EXISTS kpmc_gov.group_policies (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id uuid NOT NULL REFERENCES kpmc_gov.brands(id) ON DELETE RESTRICT,
    group_key text NOT NULL,
    data_class_id uuid NOT NULL REFERENCES kpmc_gov.data_classes(id) ON DELETE RESTRICT,
    allowed_actions jsonb NOT NULL DEFAULT '[]'::jsonb,
    allowed_principals text[] NOT NULL DEFAULT ARRAY['owner']::text[],
    requires_owner_approval boolean NOT NULL DEFAULT false,
    max_risk_level smallint NOT NULL DEFAULT 0 CHECK (max_risk_level BETWEEN 0 AND 3),
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (brand_id, group_key, data_class_id),
    CHECK (length(trim(group_key)) > 0),
    CHECK (jsonb_typeof(allowed_actions) = 'array'),
    CHECK (cardinality(allowed_principals) > 0)
);

CREATE TABLE IF NOT EXISTS kpmc_gov.provider_allowlist (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider_key text NOT NULL UNIQUE,
    endpoint_host text NOT NULL,
    allowed_data_classes text[] NOT NULL DEFAULT ARRAY[]::text[],
    allowed_models text[] NOT NULL DEFAULT ARRAY[]::text[],
    status text NOT NULL DEFAULT 'disabled' CHECK (status IN ('disabled','active','suspended')),
    reviewed_by text,
    reviewed_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (length(trim(provider_key)) > 0),
    CHECK (length(trim(endpoint_host)) > 0),
    CHECK (status <> 'active' OR (reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS kpmc_gov.approval_requests (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id uuid REFERENCES kpmc_gov.brands(id) ON DELETE RESTRICT,
    requester_id text NOT NULL,
    requester_group text NOT NULL,
    action_key text NOT NULL,
    target_ref text NOT NULL,
    data_class_id uuid REFERENCES kpmc_gov.data_classes(id) ON DELETE RESTRICT,
    risk_level smallint NOT NULL CHECK (risk_level BETWEEN 0 AND 3),
    payload_digest char(64) NOT NULL,
    redacted_payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    idempotency_key text NOT NULL UNIQUE,
    status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected','expired','executed','failed')),
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL DEFAULT (now() + interval '24 hours'),
    CHECK (length(trim(requester_id)) > 0),
    CHECK (length(trim(requester_group)) > 0),
    CHECK (length(trim(action_key)) > 0),
    CHECK (length(trim(target_ref)) > 0),
    CHECK (payload_digest ~ '^[0-9a-f]{64}$'),
    CHECK (jsonb_typeof(redacted_payload) = 'object'),
    CHECK (expires_at > created_at)
);
CREATE INDEX IF NOT EXISTS kpmc_gov_approval_pending_expiry_idx
    ON kpmc_gov.approval_requests(status, expires_at);

CREATE TABLE IF NOT EXISTS kpmc_gov.approval_decisions (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    approval_request_id uuid NOT NULL UNIQUE
        REFERENCES kpmc_gov.approval_requests(id) ON DELETE RESTRICT,
    decision text NOT NULL CHECK (decision IN ('approved','rejected','expired')),
    decided_by text NOT NULL,
    reason text NOT NULL DEFAULT '',
    decided_at timestamptz NOT NULL DEFAULT now(),
    CHECK (length(trim(decided_by)) > 0)
);

CREATE TABLE IF NOT EXISTS kpmc_gov.executor_runs (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    approval_request_id uuid NOT NULL
        REFERENCES kpmc_gov.approval_requests(id) ON DELETE RESTRICT,
    attempt_no integer NOT NULL DEFAULT 1 CHECK (attempt_no > 0),
    idempotency_key text NOT NULL UNIQUE,
    executor_key text NOT NULL,
    status text NOT NULL DEFAULT 'queued' CHECK (status IN ('queued','running','succeeded','failed','cancelled')),
    started_at timestamptz,
    finished_at timestamptz,
    result_summary jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (approval_request_id, attempt_no),
    CHECK (length(trim(executor_key)) > 0),
    CHECK (jsonb_typeof(result_summary) = 'object'),
    CHECK (finished_at IS NULL OR (started_at IS NOT NULL AND finished_at >= started_at))
);
CREATE INDEX IF NOT EXISTS kpmc_gov_executor_status_created_idx
    ON kpmc_gov.executor_runs(status, created_at);

CREATE TABLE IF NOT EXISTS kpmc_gov.audit_events (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id uuid REFERENCES kpmc_gov.brands(id) ON DELETE RESTRICT,
    actor_id text NOT NULL,
    event_key text NOT NULL,
    target_type text NOT NULL,
    target_ref text NOT NULL,
    correlation_id text,
    before_state jsonb NOT NULL DEFAULT '{}'::jsonb,
    after_state jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (length(trim(actor_id)) > 0),
    CHECK (length(trim(event_key)) > 0),
    CHECK (length(trim(target_type)) > 0),
    CHECK (length(trim(target_ref)) > 0),
    CHECK (jsonb_typeof(before_state) = 'object'),
    CHECK (jsonb_typeof(after_state) = 'object')
);
CREATE INDEX IF NOT EXISTS kpmc_gov_audit_brand_created_idx
    ON kpmc_gov.audit_events(brand_id, created_at DESC);

CREATE OR REPLACE FUNCTION kpmc_gov.reject_history_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $function$
BEGIN
    RAISE EXCEPTION '% is immutable history and cannot be changed or deleted', TG_TABLE_NAME;
END;
$function$;

DO $triggers$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgrelid = 'kpmc_gov.audit_events'::regclass
           AND tgname = 'trg_kpmc_gov_audit_events_immutable'
           AND NOT tgisinternal
    ) THEN
        CREATE TRIGGER trg_kpmc_gov_audit_events_immutable
            BEFORE UPDATE OR DELETE ON kpmc_gov.audit_events
            FOR EACH ROW EXECUTE FUNCTION kpmc_gov.reject_history_mutation();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgrelid = 'kpmc_gov.approval_decisions'::regclass
           AND tgname = 'trg_kpmc_gov_approval_decisions_immutable'
           AND NOT tgisinternal
    ) THEN
        CREATE TRIGGER trg_kpmc_gov_approval_decisions_immutable
            BEFORE UPDATE OR DELETE ON kpmc_gov.approval_decisions
            FOR EACH ROW EXECUTE FUNCTION kpmc_gov.reject_history_mutation();
    END IF;
END
$triggers$;

-- Least-privilege NOLOGIN group roles. The owner provisions LOGIN members and
-- stores credentials outside source control; this migration stores no secrets.
GRANT USAGE ON SCHEMA kpmc_gov TO kpmc_control_role, kpmc_executor_role;

GRANT SELECT, INSERT, UPDATE ON
    kpmc_gov.brands,
    kpmc_gov.data_classes,
    kpmc_gov.connectors,
    kpmc_gov.group_policies,
    kpmc_gov.provider_allowlist,
    kpmc_gov.approval_requests,
    kpmc_gov.executor_runs
TO kpmc_control_role;
GRANT SELECT, INSERT ON
    kpmc_gov.approval_decisions,
    kpmc_gov.audit_events
TO kpmc_control_role;

GRANT SELECT ON
    kpmc_gov.brands,
    kpmc_gov.data_classes,
    kpmc_gov.connectors,
    kpmc_gov.group_policies,
    kpmc_gov.provider_allowlist,
    kpmc_gov.approval_requests,
    kpmc_gov.approval_decisions
TO kpmc_executor_role;
GRANT SELECT, INSERT, UPDATE ON kpmc_gov.executor_runs TO kpmc_executor_role;
GRANT INSERT ON kpmc_gov.audit_events TO kpmc_executor_role;

-- The orchestrator retains its existing read/write workflow but cannot erase
-- these two histories. Only direct privileges on these named tables change.
DO $permissions$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ai_orchestrator_role') THEN
        REVOKE DELETE, TRUNCATE ON TABLE ai.audit_log, ai.approvals FROM ai_orchestrator_role;
    END IF;
END
$permissions$;

-- Permission-only rollback (do not drop the additive governance schema):
-- GRANT DELETE, TRUNCATE ON TABLE ai.audit_log, ai.approvals TO ai_orchestrator_role;
