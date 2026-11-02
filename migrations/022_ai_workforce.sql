CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

CREATE SCHEMA IF NOT EXISTS ai;
CREATE SCHEMA IF NOT EXISTS business;
CREATE SCHEMA IF NOT EXISTS personal;

CREATE TABLE IF NOT EXISTS ai.departments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    division VARCHAR(20) NOT NULL CHECK (division IN ('business', 'personal')),
    head_position_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai.positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    department_id UUID NOT NULL REFERENCES ai.departments(id) ON DELETE CASCADE,
    reports_to_position_id UUID REFERENCES ai.positions(id),
    permission_set JSONB NOT NULL DEFAULT '{}'::jsonb,
    approval_limits JSONB NOT NULL DEFAULT '{"max_spend_level": 1, "requires_human_approval_level": 2}'::jsonb,
    allowed_tools JSONB NOT NULL DEFAULT '[]'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_no_self_report CHECK (id != reports_to_position_id)
);

ALTER TABLE ai.departments
    ADD CONSTRAINT fk_dept_head
    FOREIGN KEY (head_position_id) REFERENCES ai.positions(id) ON DELETE SET NULL;

CREATE TABLE IF NOT EXISTS ai.agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    system_prompt TEXT NOT NULL,
    model_combo VARCHAR(50) NOT NULL DEFAULT 'local_ram',
    skills JSONB NOT NULL DEFAULT '[]'::jsonb,
    memory_scope VARCHAR(20) NOT NULL CHECK (memory_scope IN ('business', 'personal', 'global')),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai.assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    position_id UUID NOT NULL REFERENCES ai.positions(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES ai.agents(id) ON DELETE CASCADE,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    handover_note TEXT
);

CREATE TABLE IF NOT EXISTS ai.skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    file_path VARCHAR(255) NOT NULL,
    version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai.tools (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    kind VARCHAR(10) NOT NULL CHECK (kind IN ('read', 'write')),
    n8n_webhook VARCHAR(255),
    function_signature JSONB,
    risk_level INT NOT NULL DEFAULT 0 CHECK (risk_level BETWEEN 0 AND 3),
    is_active BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS ai.tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_task_id UUID REFERENCES ai.tasks(id) ON DELETE SET NULL,
    position_id UUID NOT NULL REFERENCES ai.positions(id),
    requester VARCHAR(100) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'waiting_approval', 'completed', 'failed', 'rejected')),
    input JSONB NOT NULL,
    output JSONB,
    cost NUMERIC(10, 6) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai.approvals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES ai.tasks(id) ON DELETE CASCADE,
    tool_id UUID NOT NULL REFERENCES ai.tools(id),
    payload JSONB NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    decided_by VARCHAR(100),
    decided_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai.audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor VARCHAR(100) NOT NULL,
    action VARCHAR(100) NOT NULL,
    target VARCHAR(100) NOT NULL,
    before JSONB,
    after JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai.knowledge_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scope VARCHAR(20) NOT NULL CHECK (scope IN ('business', 'personal')),
    source VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    embedding vector(768),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai.budgets (
    position_id UUID PRIMARY KEY REFERENCES ai.positions(id) ON DELETE CASCADE,
    daily_limit NUMERIC(10, 2) NOT NULL DEFAULT 5.00,
    monthly_limit NUMERIC(10, 2) NOT NULL DEFAULT 100.00,
    spent NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    last_reset TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

DO $$
DECLARE
    dept_id UUID;
    pos_id UUID;
    agent_id UUID;
BEGIN
    INSERT INTO ai.departments (name, division)
    VALUES ('Executive Management', 'business')
    RETURNING id INTO dept_id;

    INSERT INTO ai.positions (name, department_id, permission_set, approval_limits)
    VALUES ('Chief of Staff', dept_id, '{"all": true}'::jsonb, '{"max_spend_level": 3, "requires_human_approval_level": 2}'::jsonb)
    RETURNING id INTO pos_id;

    UPDATE ai.departments SET head_position_id = pos_id WHERE id = dept_id;

    INSERT INTO ai.agents (name, system_prompt, model_combo, memory_scope)
    VALUES (
        'Chief of Staff Core',
        'You are the Chief of Staff. You route incoming tasks, enforce read-only defaults, and queue Level 2/3 write actions for human approval.',
        'local_ram',
        'global'
    )
    RETURNING id INTO agent_id;

    INSERT INTO ai.assignments (position_id, agent_id, handover_note)
    VALUES (pos_id, agent_id, 'Initialized in Option 2 hybrid topology.');
END $$;
