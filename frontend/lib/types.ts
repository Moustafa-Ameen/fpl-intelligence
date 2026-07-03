export interface Player {
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
  web_name?: string;
  team_code?: number;
  reasoning?: string;
}

export interface CaptainPick {
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
  reasoning?: string;
}

export interface TransferTarget {
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
}

export interface FixtureTick {
  team: string;
  team_short: string;
  fixtures: {
  gw: number;
    opponent: string;
    home: boolean;
    difficulty: number;
  }[];
}

export interface PlayerHistoryPoint {
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
