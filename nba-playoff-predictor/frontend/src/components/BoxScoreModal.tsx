import { api } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { TeamChip } from "../components/TeamChip";
import { Icon } from "./Icon";
import { Spinner } from "./common";
import type { BoxScoreTeam, GameSummary } from "../api/types";

export function BoxScoreModal({ game, onClose }: { game: GameSummary; onClose: () => void }) {
  const { data, loading, error } = useAsync(() => api.boxScore(game.game_id), [game.game_id]);

  const awayWon = game.winner === "away";

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div style={{ padding: "22px 24px", borderBottom: "1px solid var(--line)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <span className="badge badge--final">FINAL</span>
          <button className="icon-btn" style={{ width: 32, height: 32, background: "var(--surface-2)" }} onClick={onClose}>
            <Icon name="close" size={16} strokeWidth={2.2} />
          </button>
        </div>

        <div style={{ padding: "22px 24px" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: 20 }}>
            <TeamHeader
              abbr={game.away.abbr}
              color={game.away.color}
              city={game.away.city}
              name={game.away.name}
              record={game.away.record}
              score={game.away_score}
              dim={!awayWon && game.winner != null}
            />
            <TeamHeader
              abbr={game.home.abbr}
              color={game.home.color}
              city={game.home.city}
              name={game.home.name}
              record={game.home.record}
              score={game.home_score}
              dim={awayWon}
            />
          </div>

          {loading && <Spinner label="Loading box score…" />}
          {error && <div className="empty-state">{error}</div>}
          {!loading && !error && data && !data.available && (
            <div className="empty-state">{data.message ?? "Box score unavailable."}</div>
          )}
          {!loading && !error && data && data.available && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 18 }}>
              {data.away && <PerformerTable team={data.away} />}
              {data.home && <PerformerTable team={data.home} />}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function TeamHeader({
  abbr,
  color,
  city,
  name,
  record,
  score,
  dim,
}: {
  abbr: string;
  color: string;
  city: string;
  name: string;
  record: string | null;
  score: number | null;
  dim: boolean;
}) {
  const inkColor = dim ? "var(--ink-3)" : "var(--ink)";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 13 }}>
      <TeamChip abbr={abbr} color={color} />
      <div>
        <div style={{ fontWeight: 700, fontSize: 16, color: inkColor }}>
          {city} {name}
        </div>
        <div style={{ fontSize: 12, color: "var(--ink-3)" }}>{record ?? ""}</div>
      </div>
      <div className="display tnum" style={{ marginLeft: "auto", fontWeight: 800, fontSize: 32, color: inkColor }}>
        {score ?? "—"}
      </div>
    </div>
  );
}

function PerformerTable({ team }: { team: BoxScoreTeam }) {
  const th = { textAlign: "right", padding: "5px 8px", fontSize: 10, fontWeight: 700, color: "var(--ink-3)" } as const;
  const td = { textAlign: "right", padding: "7px 8px", fontSize: 12.5, fontWeight: 600, color: "var(--ink-2)" } as const;
  return (
    <div>
      <div style={{ fontWeight: 700, fontSize: 13, color: team.team.color, marginBottom: 8 }}>
        {team.team.name} — Top Performers
      </div>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th style={{ ...th, textAlign: "left" }}>PLAYER</th>
            <th style={th}>MIN</th>
            <th style={th}>PTS</th>
            <th style={th}>REB</th>
            <th style={th}>AST</th>
            <th style={th}>+/-</th>
          </tr>
        </thead>
        <tbody>
          {team.players.map((p, i) => (
            <tr key={i} style={{ borderTop: "1px solid var(--line)" }}>
              <td style={{ padding: "7px 8px", fontWeight: 600, fontSize: 13 }}>{p.name}</td>
              <td style={td}>{p.minutes ?? "—"}</td>
              <td style={{ ...td, fontWeight: 800, color: "var(--ink)" }}>{p.points ?? "—"}</td>
              <td style={td}>{p.rebounds ?? "—"}</td>
              <td style={td}>{p.assists ?? "—"}</td>
              <td style={td}>{p.plus_minus ?? "—"}</td>
            </tr>
          ))}
          {team.players.length === 0 && (
            <tr>
              <td colSpan={6} style={{ padding: "10px 8px", color: "var(--ink-3)", fontSize: 12 }}>
                No player data.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
