-- B14g: what customers say (uploads, own product pages, public web mentions) and social insight exports (UC-18).
create table if not exists customer_mentions (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references profiles (id) on delete cascade,
  source_type text not null check (source_type in ('upload', 'own_site', 'web')),
  source text not null,          -- file name or page URL
  url text,
  author text,
  text text not null,
  rating numeric,
  date date,
  product text,
  sentiment text check (sentiment in ('positive', 'neutral', 'negative')),
  is_demo_data boolean not null default false,
  created_at timestamptz not null default now()
);
create index if not exists customer_mentions_profile_idx on customer_mentions (profile_id, date desc);
alter table customer_mentions enable row level security;

create table if not exists customer_insights (
  profile_id uuid primary key references profiles (id) on delete cascade,
  themes jsonb not null default '[]'::jsonb,
  mention_count int not null default 0,
  ai boolean not null default true,
  analysed_at timestamptz not null default now()
);
alter table customer_insights enable row level security;

create table if not exists social_metrics (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references profiles (id) on delete cascade,
  source text not null,
  date date not null,
  metric text not null,
  value numeric not null
);
create index if not exists social_metrics_profile_idx on social_metrics (profile_id, metric, date);
alter table social_metrics enable row level security;
