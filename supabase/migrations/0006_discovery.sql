-- B08: discovery candidates with pass/fail reasons (specs §3).
create table if not exists discovery_candidates (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references profiles (id) on delete cascade,
  job_id uuid references jobs (id) on delete set null,
  name text not null,
  domain text not null,
  origin text not null,
  status text not null check (status in ('verified', 'rejected')),
  reasons text[] not null default '{}',
  india_signals jsonb not null default '{}'::jsonb,
  similarity real,
  created_at timestamptz not null default now()
);
create index if not exists discovery_candidates_profile_id_idx on discovery_candidates (profile_id);
create index if not exists discovery_candidates_job_id_idx on discovery_candidates (job_id);
alter table discovery_candidates enable row level security;
