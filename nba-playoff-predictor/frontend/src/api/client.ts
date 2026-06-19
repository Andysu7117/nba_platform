/** Thin typed wrapper around the FastAPI backend. */
import type {
  AppMeta,
  BoxScoreResponse,
  CalendarResponse,
  ModelStatus,
  PlayerDetailResponse,
  PlayerSearchResult,
  PlayersResponse,
  PredictResponse,
  ScheduleResponse,
  SeasonsResponse,
  SeedsResponse,
  SimulateResponse,
  StandingsResponse,
  TeamRef,
} from "./types";

const BASE = "/api";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      /* response had no JSON body */
    }
    throw new ApiError(res.status, detail);
  }
  return (await res.json()) as T;
}

const seasonQuery = (season?: string) => (season ? `&season=${season}` : "");

export const api = {
  meta: () => request<AppMeta>("/meta"),
  seasons: () => request<SeasonsResponse>("/seasons"),
  modelStatus: () => request<ModelStatus>("/meta/model"),
  teams: () => request<TeamRef[]>("/teams"),

  standings: (conference: string, season?: string) =>
    request<StandingsResponse>(`/standings?conference=${conference}${seasonQuery(season)}`),

  schedule: (date: string, refresh = false) =>
    request<ScheduleResponse>(`/schedule?date=${date}${refresh ? "&refresh=true" : ""}`),
  calendar: (start: string, end: string) =>
    request<CalendarResponse>(`/schedule/calendar?start=${start}&end=${end}`),
  boxScore: (gameId: string) => request<BoxScoreResponse>(`/games/${gameId}/boxscore`),

  predict: (homeAbbr: string, awayAbbr: string) =>
    request<PredictResponse>("/predict", {
      method: "POST",
      body: JSON.stringify({ home_abbr: homeAbbr, away_abbr: awayAbbr }),
    }),

  seeds: (season?: string) => request<SeedsResponse>(`/playoffs/seeds${season ? `?season=${season}` : ""}`),
  simulate: (nSimulations: number, season?: string) =>
    request<SimulateResponse>("/playoffs/simulate", {
      method: "POST",
      body: JSON.stringify({ n_simulations: nSimulations, season }),
    }),

  players: (season?: string) =>
    request<PlayersResponse>(`/players${season ? `?season=${season}` : ""}`),
  playerSearch: (q: string) =>
    request<PlayerSearchResult[]>(`/players/search?q=${encodeURIComponent(q)}`),
  playerDetail: (playerId: number, season?: string, seasonType = "Regular Season", perMode = "PerGame") =>
    request<PlayerDetailResponse>(
      `/players/${playerId}?season_type=${encodeURIComponent(seasonType)}&per_mode=${perMode}` +
        (season ? `&season=${season}` : ""),
    ),
};
