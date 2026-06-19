import { useMemo, useState } from "react";
import { api } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { Icon } from "../components/Icon";
import { SeasonSelect } from "../components/SeasonSelect";
import { LineChart, type Series } from "../components/LineChart";
import { EmptyState, ErrorState, Spinner } from "../components/common";
import type { CareerRow, GameLogRow } from "../api/types";

type SeasonType = "Regular Season" | "Playoffs";
type PerMode = "PerGame" | "Totals";

interface StatOption {
  key: keyof GameLogRow;
  label: string;
}
const STAT_OPTIONS: StatOption[] = [
  { key: "points", label: "PTS" },
  { key: "rebounds", label: "REB" },
  { key: "assists", label: "AST" },
  { key: "steals", label: "STL" },
  { key: "blocks", label: "BLK" },
  { key: "minutes", label: "MIN" },
  { key: "plus_minus", label: "+/-" },
];

const rolling = (vals: (number | null)[], window = 5): (number | null)[] =>
  vals.map((_, i) => {
    const slice = vals.slice(Math.max(0, i - window + 1), i + 1).filter((v): v is number => v != null);
    return slice.length ? slice.reduce((a, b) => a + b, 0) / slice.length : null;
  });

export function PlayerDetail({
  playerId,
  initialName,
  onBack,
}: {
  playerId: number;
  initialName: string;
  onBack: () => void;
}) {
  const [season, setSeason] = useState<string | undefined>(undefined);
  const [seasonType, setSeasonType] = useState<SeasonType>("Regular Season");
  const [perMode, setPerMode] = useState<PerMode>("PerGame");
  const [stat, setStat] = useState<keyof GameLogRow>("points");

  const { data, loading, error, reload } = useAsync(
    () => api.playerDetail(playerId, season, seasonType, perMode),
    [playerId, season, seasonType, perMode],
  );

  const chartSeries = useMemo<Series[]>(() => {
    if (!data) return [];
    const chrono = [...data.game_log].reverse(); // API returns newest-first
    const values = chrono.map((g) => (g[stat] as number | null) ?? null);
    return [
      { values, color: "var(--accent)", label: "Game" },
      { values: rolling(values), color: "var(--ink-3)", label: "5-game avg", dashed: true },
    ];
  }, [data, stat]);

  const statLabel = STAT_OPTIONS.find((s) => s.key === stat)?.label ?? "";

  return (
    <div className="page">
      <button
        className="btn-ghost"
        style={{ marginBottom: 18, display: "inline-flex", alignItems: "center", gap: 8 }}
        onClick={onBack}
      >
        <Icon name="chevron-left" size={16} strokeWidth={2.2} /> Back to leaderboard
      </button>

      <div className="page-head">
        <div>
          <div className="eyebrow">PLAYER PROFILE</div>
          <h1 className="h1">{data?.name ?? initialName}</h1>
        </div>
        <SeasonSelect value={season} onChange={setSeason} />
      </div>

      {error && <ErrorState message={error} onRetry={reload} />}
      {loading && <Spinner label="Loading player…" />}
      {!loading && !error && data && !data.available && (
        <EmptyState>{data.message ?? "No data available for this player."}</EmptyState>
      )}

      {!loading && !error && data && data.available && (
        <>
          {/* ---- Career tables ---- */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", margin: "0 0 12px", flexWrap: "wrap", gap: 10 }}>
            <div className="display" style={{ fontWeight: 800, fontSize: 18 }}>
              Career
            </div>
            <div className="seg-group">
              {(["PerGame", "Totals"] as PerMode[]).map((m) => (
                <button key={m} className={`seg${perMode === m ? " active" : ""}`} onClick={() => setPerMode(m)}>
                  {m === "PerGame" ? "Per Game" : "Totals"}
                </button>
              ))}
            </div>
          </div>
          {data.career_season.length === 0 ? (
            <EmptyState>No career data available.</EmptyState>
          ) : (
            <CareerTable rows={data.career_season} total={data.career_total} />
          )}

          {/* ---- Game-log chart ---- */}
          <div className="card" style={{ padding: 20, margin: "24px 0 18px" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, flexWrap: "wrap", marginBottom: 14 }}>
              <div className="display" style={{ fontWeight: 800, fontSize: 15 }}>
                {statLabel} per game — {data.season.replace("-", "–")}
              </div>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                <div className="seg-group">
                  {(["Regular Season", "Playoffs"] as SeasonType[]).map((t) => (
                    <button key={t} className={`seg${seasonType === t ? " active" : ""}`} onClick={() => setSeasonType(t)}>
                      {t === "Regular Season" ? "Regular" : "Playoffs"}
                    </button>
                  ))}
                </div>
                <select className="field" style={{ width: "auto" }} value={stat} onChange={(e) => setStat(e.target.value as keyof GameLogRow)}>
                  {STAT_OPTIONS.map((o) => (
                    <option key={o.key} value={o.key}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            {data.game_log.length === 0 ? (
              <EmptyState>No games for this player in {data.season} ({seasonType}).</EmptyState>
            ) : (
              <>
                <LineChart series={chartSeries} yLabel={statLabel} />
                <div style={{ display: "flex", gap: 16, marginTop: 8, fontSize: 11.5, fontWeight: 600, color: "var(--ink-3)" }}>
                  <Legend color="var(--accent)" label="Per game" />
                  <Legend color="var(--ink-3)" label="5-game average" dashed />
                </div>
              </>
            )}
          </div>

          {/* ---- Game log table ---- */}
          {data.game_log.length > 0 && <GameLogTable rows={data.game_log} />}
        </>
      )}
    </div>
  );
}

function Legend({ color, label, dashed }: { color: string; label: string; dashed?: boolean }) {
  return (
    <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <span style={{ width: 16, height: 0, borderTop: `2px ${dashed ? "dashed" : "solid"} ${color}` }} />
      {label}
    </span>
  );
}

const num = (v: number | null, d = 1) => (v == null ? "—" : v.toFixed(d));

function GameLogTable({ rows }: { rows: GameLogRow[] }) {
  return (
    <div className="table-wrap">
      <table className="stat-table" style={{ minWidth: 720 }}>
        <thead>
          <tr>
            <th className="left">DATE</th>
            <th className="left">MATCHUP</th>
            <th>W/L</th>
            <th>MIN</th>
            <th>PTS</th>
            <th>REB</th>
            <th>AST</th>
            <th>STL</th>
            <th>BLK</th>
            <th>+/-</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((g, i) => (
            <tr key={i}>
              <td className="left" style={{ fontWeight: 600, color: "var(--ink-2)" }}>{g.date}</td>
              <td className="left" style={{ fontWeight: 600 }}>{g.matchup}</td>
              <td style={{ fontWeight: 700, color: g.result === "W" ? "var(--pos)" : "var(--neg)" }}>{g.result ?? "—"}</td>
              <td>{num(g.minutes, 0)}</td>
              <td style={{ fontWeight: 800, color: "var(--ink)" }}>{num(g.points, 0)}</td>
              <td>{num(g.rebounds, 0)}</td>
              <td>{num(g.assists, 0)}</td>
              <td>{num(g.steals, 0)}</td>
              <td>{num(g.blocks, 0)}</td>
              <td>{g.plus_minus == null ? "—" : `${g.plus_minus > 0 ? "+" : ""}${g.plus_minus.toFixed(0)}`}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CareerTable({ rows, total }: { rows: CareerRow[]; total: CareerRow | null }) {
  const cell = (v: number | null, pct = false) => (v == null ? "—" : pct ? `${(v * 100).toFixed(1)}%` : v.toFixed(1));
  return (
    <div className="table-wrap">
      <table className="stat-table" style={{ minWidth: 760 }}>
        <thead>
          <tr>
            <th className="left">SEASON</th>
            <th>TEAM</th>
            <th>GP</th>
            <th>MIN</th>
            <th>PTS</th>
            <th>REB</th>
            <th>AST</th>
            <th>STL</th>
            <th>BLK</th>
            <th>FG%</th>
            <th>3P%</th>
            <th>FT%</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <CareerTr key={i} r={r} cell={cell} />
          ))}
          {total && (
            <tr style={{ borderTop: "2px solid var(--line-2)", fontWeight: 800 }}>
              <td className="left" style={{ fontWeight: 800 }}>Career</td>
              <td style={{ color: "var(--ink-3)" }}>—</td>
              <td>{cell(total.games_played)}</td>
              <td>{cell(total.minutes)}</td>
              <td style={{ color: "var(--ink)" }}>{cell(total.points)}</td>
              <td>{cell(total.rebounds)}</td>
              <td>{cell(total.assists)}</td>
              <td>{cell(total.steals)}</td>
              <td>{cell(total.blocks)}</td>
              <td>{cell(total.fg_pct, true)}</td>
              <td>{cell(total.fg3_pct, true)}</td>
              <td>{cell(total.ft_pct, true)}</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function CareerTr({ r, cell }: { r: CareerRow; cell: (v: number | null, pct?: boolean) => string }) {
  return (
    <tr>
      <td className="left" style={{ fontWeight: 700 }}>{r.season_id}</td>
      <td style={{ color: "var(--ink-2)", fontWeight: 600 }}>{r.team_abbr ?? "—"}</td>
      <td>{cell(r.games_played)}</td>
      <td>{cell(r.minutes)}</td>
      <td style={{ fontWeight: 800, color: "var(--ink)" }}>{cell(r.points)}</td>
      <td>{cell(r.rebounds)}</td>
      <td>{cell(r.assists)}</td>
      <td>{cell(r.steals)}</td>
      <td>{cell(r.blocks)}</td>
      <td>{cell(r.fg_pct, true)}</td>
      <td>{cell(r.fg3_pct, true)}</td>
      <td>{cell(r.ft_pct, true)}</td>
    </tr>
  );
}
