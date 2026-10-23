-- B10: versioned launch simulations (specs §3, §4.4). result holds the full computed payload for that version.
create table if not exists simulations (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references profiles (id) on delete cascade,
  version int not null,
  assumptions jsonb not null default '{}'::jsonb,
  options jsonb not null default '{}'::jsonb,
  recommended_option text,
  recommended_price_inr numeric,
  reason text,
  viability_flags jsonb not null default '[]'::jsonb,
  result jsonb not null,
  replanned_from_version int,
  trigger_change_event_id uuid references change_events (id) on delete set null,
  replan_summary text,
  created_at timestamptz not null default now(),
  unique (profile_id, version)
);
create index if not exists simulations_trigger_change_event_id_idx on simulations (trigger_change_event_id);
alter table simulations enable row level security;
