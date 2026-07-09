import { OverviewClient } from "@/components/OverviewClient";
import {
  getAccuracy,
  getCaptains,
  getCaptaincyPredictions,
  getDifferentials,
  getFixtureTicker,
  getPlayers,
  getPredictionTransfers,
  getSeasonState,
} from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function OverviewPage() {
  const [players, captains, predictions, transfers, fixtures, gems, accuracy, seasonState] = await Promise.all([
    getPlayers({ limit: 1000 }),
    getCaptains(),
    getCaptaincyPredictions(),
    getPredictionTransfers(),
    getFixtureTicker(),
    getDifferentials(),
    getAccuracy(),
    getSeasonState(),
  ]);

  return (
    <OverviewClient
      players={players}
      captains={captains}
      predictions={predictions}
      transfers={transfers}
      fixtures={fixtures}
      gems={gems}
      accuracy={accuracy}
      seasonState={seasonState}
    />
  );
}
