-- Linkshot leaderboard for a Supabase project of its own.
-- Run once in the project's SQL editor. The game calls only the two functions below,
-- with the project's publishable key; the table itself is closed to the public.

create table if not exists public.linkshot_runs (
  id          bigint generated always as identity primary key,
  player      text        not null check (char_length(player) between 8 and 64),
  name        text        not null check (char_length(name) between 1 and 20),
  score       integer     not null check (score between 0 and 10000000),
  multiplier  integer     not null default 1 check (multiplier between 1 and 1000),
  articles    integer     not null default 1 check (articles between 0 and 1000),
  target      text,
  reached     boolean     not null default false,
  daily       boolean     not null default false,
  day         integer,
  seconds     integer     check (seconds between 0 and 86400),
  version     text,
  created_at  timestamptz not null default now()
);
create index if not exists linkshot_runs_score on public.linkshot_runs (score desc);
create index if not exists linkshot_runs_day   on public.linkshot_runs (day, score desc) where daily;

alter table public.linkshot_runs enable row level security;   -- no policies: no direct reads or writes
revoke all on public.linkshot_runs from anon, authenticated;

-- Save a run and return where the player's best now ranks (one row per player, best score counts).
create or replace function public.linkshot_submit(
  p_player text, p_name text, p_score integer, p_multiplier integer, p_articles integer,
  p_target text, p_reached boolean, p_daily boolean, p_day integer, p_seconds integer, p_version text)
returns table (rank_all_time integer, rank_daily integer, total_players integer)
language plpgsql security definer set search_path = public as $$
declare best_all integer; best_day integer;
begin
  insert into linkshot_runs (player, name, score, multiplier, articles, target, reached, daily, day, seconds, version)
  values (p_player, left(coalesce(nullif(trim(p_name), ''), 'Anonymous'), 20), p_score, greatest(p_multiplier, 1),
          coalesce(p_articles, 1), left(p_target, 300), coalesce(p_reached, false), coalesce(p_daily, false),
          case when p_daily then p_day end, p_seconds, left(p_version, 40));

  select max(score) into best_all from linkshot_runs where player = p_player;
  rank_all_time := 1 + (select count(*) from (select player from linkshot_runs group by player having max(score) > best_all) t);
  total_players := (select count(distinct player) from linkshot_runs);
  if p_daily then
    select max(score) into best_day from linkshot_runs where player = p_player and daily and day = p_day;
    rank_daily := 1 + (select count(*) from (select player from linkshot_runs where daily and day = p_day
                                              group by player having max(score) > best_day) t);
  end if;
  return next;
end $$;

-- The top n players: each player's best score and latest name, for one daily challenge or all time.
create or replace function public.linkshot_top(p_scope text, p_day integer, p_n integer)
returns table (name text, score integer)
language sql stable security definer set search_path = public as $$
  select (array_agg(r.name order by r.created_at desc))[1] as name, max(r.score) as score
  from linkshot_runs r
  where p_scope <> 'daily' or (r.daily and r.day = p_day)
  group by r.player
  order by max(r.score) desc
  limit least(greatest(coalesce(p_n, 5), 1), 50);
$$;

revoke all on function public.linkshot_submit(text, text, integer, integer, integer, text, boolean, boolean, integer, integer, text) from public;
revoke all on function public.linkshot_top(text, integer, integer) from public;
grant execute on function public.linkshot_submit(text, text, integer, integer, integer, text, boolean, boolean, integer, integer, text) to anon;
grant execute on function public.linkshot_top(text, integer, integer) to anon;
