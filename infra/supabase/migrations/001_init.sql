-- Core profile table linked to Supabase auth.users
create table if not exists public.user_profiles (
  user_id uuid primary key,
  full_name text,
  created_at timestamptz default now()
);

create table if not exists public.skills (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  name text not null,
  level int not null check (level between 1 and 5),
  created_at timestamptz default now()
);

create table if not exists public.projects (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  name text not null,
  summary text not null,
  created_at timestamptz default now()
);

create table if not exists public.applications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  company text not null,
  role text not null,
  status text not null check (status in ('applied','interview','rejected','offer')),
  applied_on date,
  created_at timestamptz default now()
);

create table if not exists public.daily_recommendations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  recommendation_date date not null,
  jobs jsonb not null,
  created_at timestamptz default now(),
  unique(user_id, recommendation_date)
);

alter table public.skills enable row level security;
alter table public.projects enable row level security;
alter table public.applications enable row level security;
alter table public.daily_recommendations enable row level security;

create policy "skills owner only" on public.skills
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "projects owner only" on public.projects
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "applications owner only" on public.applications
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "daily recs owner only" on public.daily_recommendations
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
