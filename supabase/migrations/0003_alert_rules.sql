-- B05: alert rules (specs §3), created now for receipt feedback mutes; B06 adds the rest of the alerting.
create table if not exists alert_rules (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null unique references profiles (id) on delete cascade,
  change_types jsonb not null default '[]'::jsonb,
  min_priority int not null default 40,
  email_enabled boolean not null default true,
  muted jsonb not null default '[]'::jsonb, -- [{id, competitor_id, field_path, change_event_id}]
  created_at timestamptz not null default now()
);

alter table alert_rules enable row level security;
