CREATE TABLE IF NOT EXISTS summaries (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  item_id text NOT NULL,
  run_id uuid NOT NULL,
  summary text NOT NULL,
  created_at timestamptz DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_summaries_run ON summaries(run_id);
CREATE INDEX IF NOT EXISTS idx_summaries_item ON summaries(item_id);
