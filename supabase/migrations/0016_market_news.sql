-- B14h: category news and funding for a business's market, from a news search; refreshed on request.
create table if not exists market_news (
  profile_id uuid primary key references profiles (id) on delete cascade,
  queries jsonb not null default '[]'::jsonb,
  items jsonb not null default '[]'::jsonb,
  fetched_at timestamptz not null default now()
);
alter table market_news enable row level security;
