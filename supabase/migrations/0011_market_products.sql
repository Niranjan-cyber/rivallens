-- B14d: real products read from public product pages (schema.org JSON-LD), shared across businesses (UC-20).
create table if not exists market_products (
  id uuid primary key default gen_random_uuid(),
  url text not null unique,
  domain text not null,
  taxonomy_id int,
  category_path text,
  niche text,
  name text not null,
  brand text,
  description text,
  price numeric,          -- INR only; other currencies stay null (Unknown)
  currency text,
  rating numeric,
  review_count int,
  features jsonb not null default '[]'::jsonb,
  observed_at timestamptz not null
);
create index if not exists market_products_taxonomy_id_idx on market_products (taxonomy_id);
alter table market_products enable row level security;
