-- B03: core tables (specs §3). The API connects as the table owner and scopes every query by user_id.
-- RLS is enabled with no policies, so the Data API (anon/authenticated, incl. anonymous users) reads nothing.

create table if not exists profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  name text not null,
  kind text not null check (kind in ('business', 'idea')),
  offering_type text not null check (offering_type in ('product', 'service')),
  card jsonb not null default '{}'::jsonb,
  is_demo_data boolean not null default false,
  created_at timestamptz not null default now()
);
create index if not exists profiles_user_id_idx on profiles (user_id);

create table if not exists competitors (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references profiles (id) on delete cascade,
  name text not null,
  domain text not null,
  relation text not null check (relation in ('comparable', 'inspiration')),
  origin text not null check (origin in ('ai_suggested', 'added_by_user', 'seed')),
  selected boolean not null default true,
  monitorable boolean not null default true,
  india_signals jsonb not null default '{}'::jsonb,
  similarity real,
  is_demo_data boolean not null default false,
  created_at timestamptz not null default now(),
  unique (profile_id, domain)
);
create index if not exists competitors_profile_id_idx on competitors (profile_id);

create table if not exists sources (
  id uuid primary key default gen_random_uuid(),
  competitor_id uuid not null references competitors (id) on delete cascade,
  url text not null,
  page_type text not null default 'pricing' check (page_type in ('pricing', 'features', 'changelog', 'home')),
  is_mock boolean not null default false,
  created_at timestamptz not null default now(),
  unique (competitor_id, url)
);
create index if not exists sources_competitor_id_idx on sources (competitor_id);

-- One row per (user, fictional competitor): judges' Demo Lab changes never collide.
create table if not exists mock_instances (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  instance_key text not null unique,
  slug text not null,
  version text[] not null default '{v1}',
  overrides jsonb not null default '{}'::jsonb,
  unique (user_id, slug)
);

create table if not exists usage_counters (
  scope text not null,
  day date not null default current_date,
  kind text not null,
  count int not null default 0,
  primary key (scope, day, kind)
);

alter table profiles enable row level security;
alter table competitors enable row level security;
alter table sources enable row level security;
alter table mock_instances enable row level security;
alter table usage_counters enable row level security;
