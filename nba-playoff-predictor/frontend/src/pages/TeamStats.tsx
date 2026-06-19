import { useState } from "react";
import { api } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { TeamChip } from "../components/TeamChip";
import { EmptyState, ErrorState, Spinner } from "../components/common";
import { pctRaw, signed } from "../lib/format";
import type { StandingRow } from "../api/types";

type Conf = "East" | "West" | "League";
const CONFS: Conf[] = ["East", "West", "League"];

const NUM_COLS = ["W", "L", "PCT", "GB", "STRK", "L10", "ORTG", "DRTG", "NET"];

export function TeamStats() {
  const [conf, setConf] = useState<Conf>("East");
  const { data, loading, error, reload } = useAsync(() => api.standings(conf), [conf]);

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <div className="eyebrow">STANDINGS</div>
          <h1 className="h1">Team Stats</h1>
        </div>
        <div className="seg-group">
          {CONFS.map((c) => (
            <button key={c} className={`seg${conf === c ? " active" : ""}`} onClick={() => setConf(c)}>
              {c}
            </button>
          ))}
        </div>
      </div>

      <div style={{ display: "flex", gap: 18, flexWrap: "wrap", marginBottom: 18 }}>
        <Legend color="var(--accent)" label="Playoff berth" />
        <Legend color="var(--gold)" label="Play-in" />
      </div>

      {error && <ErrorState message={error} onRetry={reload} />}
      {!error && loading && <Spinner label="Loading standings…" />}
      {!error && !loading && data && data.rows.length === 0 && (
        <EmptyState>No standings available — no games cached for {data.season}.</EmptyState>
      )}
      {!error && !loading && data && data.rows.length > 0 && (
        <div className="table-wrap">
          <table className="stat-table" style={{ minWidth: 720 }}>
            <thead>
              <tr>
                <th className="left">TEAM</th>
                {NUM_COLS.map((c) => (
                  <th key={c}>{c}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.rows.map((row) => (
                <StandingsRow key={row.team.team_id} row={row} showSeedAccent={conf !== "League"} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 7, fontSize: 12, fontWeight: 600, color: "var(--ink-2)" }}>
      <span style={{ width: 14, height: 3, borderRadius: 2, background: color }} />
      {label}
    </div>
  );
}

function StandingsRow({ row, showSeedAccent }: { row: StandingRow; showSeedAccent: boolean }) {
  const accent =
    showSeedAccent && row.rank <= 6
      ? "var(--accent)"
      : showSeedAccent && row.rank <= 8
        ? "var(--gold)"
        : "transparent";
  const numStyle = { fontSize: 13.5, fontWeight: 700, color: "var(--ink)" } as const;
  const muteStyle = { fontSize: 13, fontWeight: 600, color: "var(--ink-3)" } as const;

  return (
    <tr style={{ boxShadow: `inset 3px 0 0 ${accent}` }}>
      <td className="left">
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ width: 22, fontWeight: 800, fontSize: 13, color: "var(--ink-3)" }}>{row.rank}</span>
          <TeamChip abbr={row.team.abbr} color={row.team.color} size="sm" />
          <div style={{ whiteSpace: "nowrap" }}>
            <div style={{ fontWeight: 700, fontSize: 14 }}>
              {row.team.city} {row.team.name}
            </div>
            <div style={{ fontSize: 11, color: "var(--ink-3)", fontWeight: 500 }}>{row.team.conference}</div>
          </div>
        </div>
      </td>
      <td style={numStyle}>{row.wins}</td>
      <td style={numStyle}>{row.losses}</td>
      <td style={numStyle}>{pctRaw(row.win_pct)}</td>
      <td style={muteStyle}>{row.games_back === 0 ? "—" : row.games_back.toFixed(1)}</td>
      <td style={{ fontSize: 13, fontWeight: 700, color: row.streak[0] === "W" ? "var(--pos)" : "var(--neg)" }}>
        {row.streak}
      </td>
      <td style={muteStyle}>{row.last_10}</td>
      <td style={numStyle}>{row.off_rating.toFixed(1)}</td>
      <td style={numStyle}>{row.def_rating.toFixed(1)}</td>
      <td style={{ fontSize: 13.5, fontWeight: 800, color: row.net_rating >= 0 ? "var(--pos)" : "var(--neg)" }}>
        {signed(Number(row.net_rating.toFixed(1)))}
      </td>
    </tr>
  );
}
