import { CalendarDays } from "lucide-react";
import type { SeasonState, SeasonStateCode } from "@/lib/types";

export function isSeasonEndedState(state?: SeasonStateCode | null): boolean {
  return state === "season_ended_preseason" || state === "season_ended_no_next_data";
}

export function SeasonTransitionNotice({
  seasonState,
  message,
}: {
  seasonState: SeasonState;
  message?: string;
}) {
  if (!isSeasonEndedState(seasonState.season_state)) return null;

  const nextSeason = seasonState.fixture_season !== "unknown"
    ? seasonState.fixture_season
    : "the next season";
  const startDate = seasonState.next_season_start
    ? new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "long", year: "numeric" }).format(
        new Date(seasonState.next_season_start),
      )
    : null;

  return (
    <div className="flex items-start gap-3 rounded-lg border border-fpl-amber/30 bg-fpl-amber/10 p-4 text-sm text-secondary">
      <CalendarDays className="mt-0.5 h-5 w-5 shrink-0 text-fpl-amber" />
      <div>
        <div className="font-semibold text-primary">Season transition</div>
        <p className="mt-1 leading-6">
          {message ?? (
            `The ${seasonState.fpl_api_season} season has ended. Projections for ${nextSeason} will be available once the new season begins and enough gameweeks have been played to establish rolling form data.`
          )}
        </p>
        {startDate && !message ? (
          <p className="mt-1 text-xs text-fpl-amber">Season starts {startDate}.</p>
        ) : null}
      </div>
    </div>
  );
}
