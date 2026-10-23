-- B14e: the business's own money data, from uploads or manual entry (UC-17).
create table if not exists transactions (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references profiles (id) on delete cascade,
  date date not null,
  kind text not null check (kind in ('sale', 'expense', 'funding')),
  amount numeric not null,
  product text,
  quantity numeric,
  description text,
  source text not null default 'manual',  -- 'manual' or the uploaded file name
  is_demo_data boolean not null default false,
  created_at timestamptz not null default now()
);
create index if not exists transactions_profile_date_idx on transactions (profile_id, date);
alter table transactions enable row level security;

create table if not exists money_settings (
  profile_id uuid primary key references profiles (id) on delete cascade,
  cash numeric,
  cash_as_of date,
  industry text,  -- a Damodaran 'Margins by industry (India)' industry name
  updated_at timestamptz not null default now()
);
alter table money_settings enable row level security;
