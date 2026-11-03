#!/usr/bin/env bash
set -euo pipefail

psql -X -v ON_ERROR_STOP=1 -q -f migrations/022_ai_workforce.sql

psql -X -v ON_ERROR_STOP=1 -q <<'SQL'
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ai_orchestrator_role') THEN
        CREATE ROLE ai_orchestrator_role NOLOGIN;
    END IF;
END
$$;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE ON ai.audit_log, ai.approvals TO ai_orchestrator_role;
SQL

psql -X -v ON_ERROR_STOP=1 -q -f migrations/023_kpmc_governance.sql
psql -X -v ON_ERROR_STOP=1 -q -f migrations/023_kpmc_governance.sql

psql -X -v ON_ERROR_STOP=1 <<'SQL'
DO $$
DECLARE
    v_brand uuid;
    v_class uuid;
    v_request uuid;
    v_decision uuid;
    v_event uuid;
BEGIN
    IF has_table_privilege('ai_orchestrator_role', 'ai.audit_log', 'DELETE')
       OR has_table_privilege('ai_orchestrator_role', 'ai.audit_log', 'TRUNCATE')
       OR has_table_privilege('ai_orchestrator_role', 'ai.approvals', 'DELETE')
       OR has_table_privilege('ai_orchestrator_role', 'ai.approvals', 'TRUNCATE') THEN
        RAISE EXCEPTION 'orchestrator still has destructive privileges on protected history';
    END IF;

    IF NOT has_table_privilege('ai_orchestrator_role', 'ai.audit_log', 'INSERT')
       OR NOT has_table_privilege('ai_orchestrator_role', 'ai.approvals', 'SELECT') THEN
        RAISE EXCEPTION 'existing non-destructive orchestrator privileges were not preserved';
    END IF;

    IF has_schema_privilege('ai_orchestrator_role', 'kpmc_gov', 'USAGE') THEN
        RAISE EXCEPTION 'orchestrator must not access KPMC governance schema directly';
    END IF;

    IF NOT has_table_privilege('kpmc_control_role', 'kpmc_gov.approval_requests', 'INSERT')
       OR has_table_privilege('kpmc_control_role', 'kpmc_gov.audit_events', 'DELETE')
       OR NOT has_table_privilege('kpmc_executor_role', 'kpmc_gov.executor_runs', 'UPDATE')
       OR has_table_privilege('kpmc_executor_role', 'kpmc_gov.approval_decisions', 'INSERT') THEN
        RAISE EXCEPTION 'KPMC governance role grants do not match the least-privilege contract';
    END IF;

    INSERT INTO kpmc_gov.brands(brand_key, display_name)
    VALUES ('ci-brand', 'CI Brand') RETURNING id INTO v_brand;
    INSERT INTO kpmc_gov.data_classes(class_key, display_name, sensitivity_rank, requires_owner_approval)
    VALUES ('critical', 'Critical', 3, true) RETURNING id INTO v_class;
    INSERT INTO kpmc_gov.approval_requests(
        brand_id, requester_id, requester_group, action_key, target_ref,
        data_class_id, risk_level, payload_digest, idempotency_key
    ) VALUES (
        v_brand, 'ci-owner', 'owner', 'ci.test', 'fixture',
        v_class, 3, repeat('a', 64), 'ci-approval-1'
    ) RETURNING id INTO v_request;
    INSERT INTO kpmc_gov.approval_decisions(approval_request_id, decision, decided_by)
    VALUES (v_request, 'approved', 'ci-owner') RETURNING id INTO v_decision;
    INSERT INTO kpmc_gov.audit_events(actor_id, event_key, target_type, target_ref)
    VALUES ('ci-owner', 'ci.created', 'test', 'fixture') RETURNING id INTO v_event;

    BEGIN
        UPDATE kpmc_gov.audit_events SET event_key = 'tampered' WHERE id = v_event;
        RAISE EXCEPTION 'audit event UPDATE unexpectedly succeeded';
    EXCEPTION WHEN raise_exception THEN
        IF SQLERRM = 'audit event UPDATE unexpectedly succeeded' THEN RAISE; END IF;
    END;

    BEGIN
        DELETE FROM kpmc_gov.audit_events WHERE id = v_event;
        RAISE EXCEPTION 'audit event DELETE unexpectedly succeeded';
    EXCEPTION WHEN raise_exception THEN
        IF SQLERRM = 'audit event DELETE unexpectedly succeeded' THEN RAISE; END IF;
    END;

    BEGIN
        UPDATE kpmc_gov.approval_decisions SET reason = 'tampered' WHERE id = v_decision;
        RAISE EXCEPTION 'approval decision UPDATE unexpectedly succeeded';
    EXCEPTION WHEN raise_exception THEN
        IF SQLERRM = 'approval decision UPDATE unexpectedly succeeded' THEN RAISE; END IF;
    END;

    BEGIN
        DELETE FROM kpmc_gov.approval_decisions WHERE id = v_decision;
        RAISE EXCEPTION 'approval decision DELETE unexpectedly succeeded';
    EXCEPTION WHEN raise_exception THEN
        IF SQLERRM = 'approval decision DELETE unexpectedly succeeded' THEN RAISE; END IF;
    END;
END
$$;
SQL
