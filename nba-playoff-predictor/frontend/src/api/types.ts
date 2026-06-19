/** Mirrors the Pydantic response models exposed by the FastAPI backend. */

export interface TeamRef {
  team_id: number;
  abbr: string;
  city: string;
  name: string;
  conference: string;
  color: string;
  record: string | null;
}

export interface AppMeta {
  current_season: string;
  latest_date: string | null;
  has_model: boolean;
  has_data: boolean;
}

export interface SeasonsResponse {
  current: string;
  seasons: string[];
}

export interface ModelStatus {
  trained: boolean;
  accuracy: number | null;
  log_loss: number | null;
  brier_score: number | null;
  n_train: number | null;
  n_test: number | null;
  train_end_date: string | null;
  test_start_date: string | null;
}

export interface StandingRow {
  rank: number;
  team: TeamRef;
  wins: number;
  losses: number;
  win_pct: number;
  games_back: number;
  streak: string;
  last_10: string;
  off_rating: number;
  def_rating: number;
  net_rating: number;
  games_played: number;
}

export interface StandingsResponse {
  conference: string;
  season: string;
  rows: StandingRow[];
}

export type GameStatus = "scheduled" | "live" | "final";

export interface GameSummary {
  game_id: string;
  date: string;
  status: GameStatus;
  status_text: string | null;
  home: TeamRef;
  away: TeamRef;
  home_score: number | null;
  away_score: number | null;
  home_win_prob: number | null;
  away_win_prob: number | null;
  winner: "home" | "away" | null;
}

export interface ScheduleResponse {
  date: string;
  games: GameSummary[];
}

export interface DayCount {
  date: string;
  count: number;
}

export interface CalendarResponse {
  days: DayCount[];
}

export interface BoxScorePlayer {
  name: string;
  position: string | null;
  minutes: string | null;
  points: number | null;
  rebounds: number | null;
  assists: number | null;
  plus_minus: string | null;
}

export interface BoxScoreTeam {
  team: TeamRef;
  score: number | null;
  players: BoxScorePlayer[];
}

export interface BoxScoreResponse {
  game_id: string;
  status: string;
  available: boolean;
  message: string | null;
  home: BoxScoreTeam | null;
  away: BoxScoreTeam | null;
}

export interface PredictFactor {
  label: string;
  away_value: number;
  home_value: number;
  higher_is_better: boolean;
}

export interface PredictResponse {
  home: TeamRef;
  away: TeamRef;
  home_win_prob: number;
  away_win_prob: number;
  predicted_winner: "home" | "away";
  projected_home_score: number;
  projected_away_score: number;
  factors: PredictFactor[];
}

export interface SeedsResponse {
  east: TeamRef[];
  west: TeamRef[];
}

export interface SeriesResult {
  higher: TeamRef;
  lower: TeamRef;
  higher_won: boolean;
  higher_wins: number;
  lower_wins: number;
}

export interface BracketColumn {
  label: string;
  series: SeriesResult[];
}

export interface ChampionshipOdd {
  team: TeamRef;
  titles: number;
  probability: number;
}

export interface SimulateResponse {
  n_simulations: number;
  champion: TeamRef;
  runner_up: TeamRef;
  final_higher_wins: number;
  final_lower_wins: number;
  columns: BracketColumn[];
  odds: ChampionshipOdd[];
}

export interface PlayerRow {
  rank: number;
  player_id: number;
  name: string;
  team_abbr: string;
  team_color: string;
  position: string | null;
  games_played: number;
  minutes: number;
  points: number;
  rebounds: number;
  assists: number;
  steals: number;
  blocks: number;
  fg_pct: number;
  fg3_pct: number;
  ft_pct: number;
}

export interface LeaderCard {
  category: string;
  unit: string;
  name: string;
  team_abbr: string;
  team_color: string;
  team_name: string;
  value: number;
}

export interface PlayersResponse {
  season: string;
  available: boolean;
  message: string | null;
  leaders: LeaderCard[];
  rows: PlayerRow[];
}

export interface PlayerSearchResult {
  player_id: number;
  full_name: string;
  is_active: boolean | null;
}

export interface GameLogRow {
  date: string;
  matchup: string;
  result: string | null;
  minutes: number | null;
  points: number | null;
  rebounds: number | null;
  assists: number | null;
  steals: number | null;
  blocks: number | null;
  turnovers: number | null;
  fg_pct: number | null;
  fg3_pct: number | null;
  ft_pct: number | null;
  plus_minus: number | null;
}

export interface CareerRow {
  season_id: string;
  team_abbr: string | null;
  games_played: number | null;
  minutes: number | null;
  points: number | null;
  rebounds: number | null;
  assists: number | null;
  steals: number | null;
  blocks: number | null;
  turnovers: number | null;
  fg_pct: number | null;
  fg3_pct: number | null;
  ft_pct: number | null;
}

export interface PlayerDetailResponse {
  player_id: number;
  name: string;
  season: string;
  season_type: string;
  per_mode: string;
  available: boolean;
  message: string | null;
  game_log: GameLogRow[];
  career_season: CareerRow[];
  career_total: CareerRow | null;
}
