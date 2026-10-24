-- Phase two, Workstream 1: who a product is for, when it differs from the business's target customer.
alter table products add column if not exists target_customer text;
