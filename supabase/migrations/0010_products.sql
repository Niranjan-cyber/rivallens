-- B14c: a business's products, each in an exact Google product taxonomy category (UC-16).
create table if not exists products (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references profiles (id) on delete cascade,
  name text not null,
  stage text not null default 'existing' check (stage in ('existing', 'new')),
  description text,
  url text,
  taxonomy_id int,
  category_path text,
  niche text,
  category_source text not null default 'none' check (category_source in ('ai', 'top_match', 'user', 'none')),
  price numeric,
  currency text not null default 'INR',
  unit text not null default 'one_time' check (unit in ('one_time', 'month', 'year', 'hour', 'user')),
  unit_cost numeric,
  features jsonb not null default '[]'::jsonb,
  add_ons jsonb not null default '[]'::jsonb,
  source jsonb,  -- {url, observed_at, rating, review_count} when read from a public page
  is_demo_data boolean not null default false,
  created_at timestamptz not null default now()
);
create index if not exists products_profile_id_idx on products (profile_id);
create index if not exists products_taxonomy_id_idx on products (taxonomy_id);
alter table products enable row level security;
