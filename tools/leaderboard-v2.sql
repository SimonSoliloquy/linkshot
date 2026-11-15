-- Linkshot leaderboard, update 2: remember the article each run ended on, and show it with every score.
-- Run once in the Supabase SQL Editor. Safe to run again.

-- 1. Remove the stray test score saved during testing.
delete from public.linkshot_runs where name = 'Linkshot test';

-- 2. A column for the article the run ended on.
alter table public.linkshot_runs add column if not exists ended_on text;

-- 3. Saving a run now also takes the article it ended on (optional, so older copies of the game keep working).
drop function if exists public.linkshot_submit(text, text, integer, integer, integer, text, boolean, boolean, integer, integer, text);
drop function if exists public.linkshot_submit(text, text, integer, integer, integer, text, boolean, boolean, integer, integer, text, text);
create function public.linkshot_submit(
  p_player text, p_name text, p_score integer, p_multiplier integer, p_articles integer,
  p_target text, p_reached boolean, p_daily boolean, p_day integer, p_seconds integer, p_version text,
  p_ended_on text default null)
returns table (rank_all_time integer, rank_daily integer, total_players integer)
language plpgsql security definer set search_path = public as $$
declare best_all integer; best_day integer;
begin
  insert into linkshot_runs (player, name, score, multiplier, articles, target, reached, daily, day, seconds, version, ended_on)
  values (p_player, left(coalesce(nullif(trim(p_name), ''), 'Anonymous'), 20), p_score, greatest(p_multiplier, 1),
          coalesce(p_articles, 1), left(p_target, 300), coalesce(p_reached, false), coalesce(p_daily, false),
          case when p_daily then p_day end, p_seconds, left(p_version, 40), left(p_ended_on, 300));

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

-- 4. The top lists now also return the article that each player's best run ended on.
drop function if exists public.linkshot_top(text, integer, integer);
create function public.linkshot_top(p_scope text, p_day integer, p_n integer)
returns table (name text, score integer, ended_on text)
language sql stable security definer set search_path = public as $$
  select b.name, b.score, b.ended_on from (
    select distinct on (r.player) r.name, r.score, r.ended_on
    from linkshot_runs r
    where p_scope <> 'daily' or (r.daily and r.day = p_day)
    order by r.player, r.score desc, r.created_at desc
  ) b
  order by b.score desc
  limit least(greatest(coalesce(p_n, 5), 1), 50);
$$;

revoke all on function public.linkshot_submit(text, text, integer, integer, integer, text, boolean, boolean, integer, integer, text, text) from public;
revoke all on function public.linkshot_top(text, integer, integer) from public;
grant execute on function public.linkshot_submit(text, text, integer, integer, integer, text, boolean, boolean, integer, integer, text, text) to anon;
grant execute on function public.linkshot_top(text, integer, integer) to anon;
