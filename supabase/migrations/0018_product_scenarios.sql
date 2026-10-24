-- Phase two, Workstream 4: a product's own simulator assumptions, and dated scenarios a founder saves to compare runs.
alter table products add column if not exists sim_assumptions jsonb not null default '{}'::jsonb;

create table if not exists product_scenarios (
  id uuid primary key default gen_random_uuid(),
  product_id uuid not null references products (id) on delete cascade,
  created_at timestamptz not null default now(),
  assumptions jsonb not null,           -- the effective assumptions of this run
  inputs jsonb not null,                -- the labelled inputs (market, finance, customers) as shown
  recommended_price_inr numeric not null,
  result jsonb not null                 -- reason, flags and the options table
);
create index if not exists product_scenarios_product_id_created_at_idx on product_scenarios (product_id, created_at desc);
alter table product_scenarios enable row level security;
