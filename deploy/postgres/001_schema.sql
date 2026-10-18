-- Design starter. No SDK persistence adapter or application role is supplied yet.
CREATE TABLE agent_config (
  tenant_id text NOT NULL,
  agent_id text NOT NULL,
  revision bigint NOT NULL,
  config jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, agent_id, revision)
);
ALTER TABLE agent_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_config FORCE ROW LEVEL SECURITY;
CREATE POLICY agent_scope ON agent_config
  USING (tenant_id = current_setting('app.tenant_id', true)
     AND agent_id = current_setting('app.agent_id', true))
  WITH CHECK (tenant_id = current_setting('app.tenant_id', true)
     AND agent_id = current_setting('app.agent_id', true));
-- Authenticated gateway must SET LOCAL these values within EACH transaction.
-- Never grant agent clients SQL access: session variables are not credentials.
-- The bootstrap superuser bypasses RLS; create a non-owner NOSUPERUSER NOBYPASSRLS role.
