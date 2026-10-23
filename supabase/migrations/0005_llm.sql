-- B07: global LLM response cache (specs §3, §1 C-14). Key = prompt_version:sha256(task | version | input).
create table if not exists llm_cache (
  key text primary key,
  task text not null,
  provider text not null,
  model text not null,
  prompt_version text not null,
  response jsonb not null,
  input_tokens int,
  output_tokens int,
  created_at timestamptz not null default now()
);
create index if not exists llm_cache_task_idx on llm_cache (task);
alter table llm_cache enable row level security;
