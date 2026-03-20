alter table public.user_profiles
  add column if not exists linkedin_url text,
  add column if not exists github_url text,
  add column if not exists resume_text text,
  add column if not exists resume_file_name text,
  add column if not exists resume_uploaded_at timestamptz,
  add column if not exists hindsight_synced_at timestamptz,
  add column if not exists onboarding_completed_at timestamptz;

alter table public.user_profiles enable row level security;

drop policy if exists "profile owner only" on public.user_profiles;

create policy "profile owner only" on public.user_profiles
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);