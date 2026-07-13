export interface Player {
  element_id?: number | null;
  name: string;
  team: string;
  position: string;
  price: number;
  total_points: number;
  ppg: number;
  form: number;
  start_likelihood: number;
  value: number;
  captain_score: number;
  transfer_score: number;
  selected_by_percent?: number;
  defensive_contribution?: number;
  defensive_contribution_per_90?: number;
  safety_tier?: "Safe" | "Risky" | "";
  web_name?: string;
  team_code?: number;
  reasoning?: string;
}

export interface CaptainPick {
  element_id?: number | null;
  name: string;
  team: string;
  position: string;
  price?: number;
  ppg?: number;
  form?: number;
  start_likelihood: number;
  captain_score?: number;
  predicted_pts?: number | null;
  adjusted_pts?: number | null;
  team_code?: number;
  web_name?: string;
  reasoning?: string;
}

export interface TransferTarget {
  element_id?: number | null;
  name: string;
  team: string;
  position: string;
  price: number;
  form?: number;
  predicted_pts?: number | null;
  adjusted_pts?: number | null;
  start_likelihood: number;
  value?: number;
  transfer_score: number;
  selected_by_percent?: number;
  rotation_risk?: boolean;
  defensive_contribution?: number;
  defensive_contribution_per_90?: number;
  safety_tier?: "Safe" | "Risky" | "";
  team_code?: number;
}

export interface Fixture {
  id: number;
  team_h: number;
  team_a: number;
  team_h_name?: string;
  team_a_name?: string;
  team_h_short?: string;
  team_a_short?: string;
  team_h_score?: number | null;
  team_a_score?: number | null;
  event: number | null;
  kickoff_time?: string | null;
  started?: boolean;
  finished?: boolean;
  minutes?: number | null;
  team_h_difficulty: number;
  team_a_difficulty: number;
  source?: string;
  season?: string;
  difficulty_source?: string;
}

export interface FixtureTick {
  team: string;
  team_short: string;
  range?: number;
  source?: string;
  season?: string;
  difficulty_source?: string;
  fixtures: {
    gw: number;
    opponent: string;
    home: boolean;
    difficulty: number;
  }[];
}

export interface PlayerHistoryPoint {
  element_id?: number | null;
  gw: number;
  price: number;
  total_points: number;
  minutes: number;
  selected_by_percent: number;
}

export interface TeamData {
  team_name: string;
  overall_rank: number | null;
  total_points: number | null;
  bank_value: number | null;
  current_gw_points: number | null;
  squad_value: number | null;
  free_transfers_available: number | null;
}

export interface SquadPlayer {
  element_id?: number | null;
  name: string;
  position: string;
  team: string;
  team_code?: number;
  web_name?: string;
  price?: number | null;
  is_captain: boolean;
  is_vice_captain: boolean;
  predicted_pts: number | null;
  start_likelihood: number | null;
  form: number | null;
}

export interface SeasonState {
  season_state: SeasonStateCode;
  fpl_api_season: string;
  fixture_source: string;
  fixture_season: string;
  difficulty_source: string;
  current_gw: number | null;
  next_gw: number | null;
  last_completed_gw: number | null;
  next_season_start: string | null;
  data_freshness: {
    fpl_api: string;
    fixtures: string;
  };
}

export type SeasonStateCode =
  | "in_season"
  | "season_ended_preseason"
  | "season_ended_no_next_data";

export interface PlannerFixtureProjection {
  opponent: string;
  opponent_name: string;
  home: boolean;
  opponent_strength: number;
  predicted_points: number;
  start_likelihood: number;
  projected_points: number;
}

export interface PlannerProjection {
  gameweek: number;
  projected_points: number;
  blank: boolean;
  double: boolean;
  fixtures: PlannerFixtureProjection[];
}

export interface PlannerPlayer {
  element_id: number;
  name: string;
  web_name?: string;
  team: string;
  team_code?: number;
  position: string;
  price: number;
  start_likelihood: number;
  projections: PlannerProjection[];
  pick_order?: number;
  is_starter?: boolean;
  is_captain?: boolean;
  is_vice_captain?: boolean;
}

export interface PlannerBaselinePoint {
  gameweek: number;
  projected_points: number;
  blank_count: number;
  double_count: number;
}

export interface PlannerResponse {
  team_id: number;
  season_state: SeasonStateCode;
  fpl_api_season?: string;
  fixture_season?: string;
  next_season_start?: string | null;
  message?: string;
  start_gameweek: number;
  horizon: number;
  squad_gameweek: number;
  model: string;
  assumption: string;
  bank_value: number | null;
  free_transfers_available: number;
  max_extra_free_transfers: number;
  baseline: PlannerBaselinePoint[];
  squad: PlannerPlayer[];
  player_pool: PlannerPlayer[];
}

export interface BacktestResult {
  strategy: string;
  total_captain_points: number;
  avg_per_gameweek: number;
}

export interface AccuracyResult {
  model: string;
  raw_MAE: number;
  raw_RMSE: number;
  raw_beats_naive_MAE: string;
  raw_beats_naive_RMSE: string;
  adjusted_MAE: number;
  adjusted_RMSE: number;
  adjusted_beats_naive_MAE: string;
  adjusted_beats_naive_RMSE: string;
}

export interface Top10Metric {
  model: string;
  precision_at_10: number;
  recall_at_10: number;
}
