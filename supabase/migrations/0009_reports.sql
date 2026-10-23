-- B11: generated evidence reports (specs §3, §1 C-12).
create table if not exists reports (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references profiles (id) on delete cascade,
  job_id uuid references jobs (id) on delete set null,
  range jsonb not null,
  body jsonb not null,
  created_at timestamptz not null default now()
);
create index if not exists reports_profile_id_idx on reports (profile_id);
create index if not exists reports_job_id_idx on reports (job_id);
alter table reports enable row level security;
