-- B06: alerts (specs §3). Rules rows are created lazily with these defaults.
create table if not exists alerts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  profile_id uuid not null references profiles (id) on delete cascade,
  change_event_id uuid not null references change_events (id) on delete cascade,
  bucket text not null check (bucket in ('high', 'medium', 'low')),
  priority int not null,
  text text not null,
  read boolean not null default false,
  seen_again int not null default 0,
  email_status text not null default 'not_sent' check (email_status in ('not_sent', 'sent', 'failed', 'skipped')),
  created_at timestamptz not null default now()
);
create index if not exists alerts_user_id_read_created_at_idx on alerts (user_id, read, created_at desc);
create index if not exists alerts_profile_id_idx on alerts (profile_id);
create index if not exists alerts_change_event_id_idx on alerts (change_event_id);

alter table alert_rules alter column change_types
  set default '{"price": true, "feature": true, "plan": true, "positioning": true, "announcement": false}'::jsonb;
update alert_rules set change_types = '{"price": true, "feature": true, "plan": true, "positioning": true, "announcement": false}'::jsonb
  where change_types = '[]'::jsonb;

alter table alerts enable row level security;
