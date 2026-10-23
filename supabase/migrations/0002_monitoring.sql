-- B04: monitoring tables (specs §3). Same model as 0001: API connects as owner, scopes by user_id; RLS on, no policies.

create table if not exists jobs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  profile_id uuid references profiles (id) on delete cascade,
  kind text not null,
  status text not null default 'queued' check (status in ('queued', 'running', 'done', 'failed', 'stale')),
  steps jsonb not null default '[]'::jsonb,
  result jsonb,
  error jsonb,
  heartbeat_at timestamptz,
  created_at timestamptz not null default now()
);
create index if not exists jobs_user_id_created_at_idx on jobs (user_id, created_at desc);
create index if not exists jobs_profile_id_idx on jobs (profile_id);

create table if not exists runs (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references profiles (id) on delete cascade,
  job_id uuid references jobs (id) on delete set null,
  kind text not null check (kind in ('baseline', 'run')),
  status text not null default 'running' check (status in ('running', 'done', 'failed', 'stale')),
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  counts jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists runs_profile_id_started_at_idx on runs (profile_id, started_at desc);
create index if not exists runs_job_id_idx on runs (job_id);

-- run_id is null for snapshots copied into a guest account (they share the seed's immutable storage objects).
create table if not exists snapshots (
  id uuid primary key default gen_random_uuid(),
  source_id uuid not null references sources (id) on delete cascade,
  run_id uuid references runs (id) on delete set null,
  observed_at timestamptz not null,
  status text not null,
  http_status int,
  storage_path text,
  sha256 text,
  text text,
  sections jsonb,
  bytes int,
  created_at timestamptz not null default now()
);
create index if not exists snapshots_source_id_observed_at_idx on snapshots (source_id, observed_at desc);
create index if not exists snapshots_run_id_idx on snapshots (run_id);

create table if not exists observations (
  id uuid primary key default gen_random_uuid(),
  snapshot_id uuid not null unique references snapshots (id) on delete cascade,
  source_id uuid not null references sources (id) on delete cascade,
  observed_at timestamptz not null,
  fields jsonb not null,
  origin text not null default 'observed' check (origin in ('observed', 'internet_archive', 'seed')),
  created_at timestamptz not null default now()
);
create index if not exists observations_source_id_observed_at_idx on observations (source_id, observed_at desc);

create table if not exists ledger_entries (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references runs (id) on delete cascade,
  source_id uuid not null references sources (id) on delete cascade,
  section_key text not null,
  reason text not null,
  summary text not null,
  created_at timestamptz not null default now()
);
create index if not exists ledger_entries_run_id_idx on ledger_entries (run_id);
create index if not exists ledger_entries_source_id_idx on ledger_entries (source_id);

create table if not exists change_events (
  id uuid primary key default gen_random_uuid(),
  run_id uuid references runs (id) on delete set null,
  source_id uuid not null references sources (id) on delete cascade,
  competitor_id uuid not null references competitors (id) on delete cascade,
  change_type text not null,
  field_path text not null,
  prev_value jsonb,
  curr_value jsonb,
  delta_pct real,
  status text not null check (status in ('confirmed', 'needs_review')),
  before_snapshot_id uuid references snapshots (id) on delete set null,
  after_snapshot_id uuid references snapshots (id) on delete set null,
  excerpt jsonb,
  observed_at timestamptz not null,
  prev_observed_at timestamptz,
  published_at timestamptz,
  wayback_url text,
  priority int,
  priority_breakdown jsonb,
  fingerprint text,
  is_demo_data boolean not null default false,
  created_at timestamptz not null default now()
);
create index if not exists change_events_competitor_id_observed_at_idx on change_events (competitor_id, observed_at desc);
create index if not exists change_events_fingerprint_idx on change_events (fingerprint);
create index if not exists change_events_run_id_idx on change_events (run_id);
create index if not exists change_events_source_id_idx on change_events (source_id);
create index if not exists change_events_before_snapshot_id_idx on change_events (before_snapshot_id);
create index if not exists change_events_after_snapshot_id_idx on change_events (after_snapshot_id);

alter table jobs enable row level security;
alter table runs enable row level security;
alter table snapshots enable row level security;
alter table observations enable row level security;
alter table ledger_entries enable row level security;
alter table change_events enable row level security;

-- The only anon-readable data: fictional mock page state (specs §1 C-02). Owner-privileged view by design.
create or replace view mock_pages_public as select instance_key, slug, version, overrides from mock_instances;
grant select on mock_pages_public to anon;
