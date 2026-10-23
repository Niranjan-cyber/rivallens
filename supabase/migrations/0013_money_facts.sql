-- B14f: competitors' reported revenue, profit and funding, each a verbatim quote from a linked source (shared public data).
create table if not exists money_facts (
  id uuid primary key default gen_random_uuid(),
  company text not null,
  kind text not null check (kind in ('revenue', 'profit', 'funding')),
  amount_inr numeric not null,
  period text,
  round text,
  event_date text,
  quote text not null,
  source_url text not null,
  source_title text,
  added_by_user boolean not null default false,
  observed_at timestamptz not null default now(),
  unique (company, kind, source_url, amount_inr)
);
create index if not exists money_facts_company_idx on money_facts (lower(company));
alter table money_facts enable row level security;
