-- B09: per-profile comparison criteria (specs §3, §1 C-10).
create table if not exists criteria_configs (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null unique references profiles (id) on delete cascade,
  template text not null,
  criteria jsonb not null,
  created_at timestamptz not null default now()
);
alter table criteria_configs enable row level security;
