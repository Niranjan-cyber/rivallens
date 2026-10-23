-- B14f: companies the user asked about stay on their Money page even when nothing was found (Unknown).
alter table money_settings add column if not exists rivals jsonb not null default '[]'::jsonb;
