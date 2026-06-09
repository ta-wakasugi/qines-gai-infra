CREATE TABLE IF NOT EXISTS review_tasks (
    id UUID PRIMARY KEY,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    total_rules INTEGER NOT NULL DEFAULT 0,
    completed_rules INTEGER NOT NULL DEFAULT 0,
    summary TEXT NULL,
    error_message TEXT NULL,
    input_doc_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    knowhow_doc_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS review_results (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES review_tasks(id) ON DELETE CASCADE,
    rule_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    target VARCHAR(500) NULL,
    finding TEXT NOT NULL,
    reason TEXT NOT NULL,
    suggestion TEXT NOT NULL,
    evidences JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_review_results_task_id
    ON review_results(task_id);

CREATE INDEX IF NOT EXISTS ix_review_results_rule_id
    ON review_results(rule_id);