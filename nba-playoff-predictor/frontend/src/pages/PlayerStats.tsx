import { useMemo, useState } from "react";
import { api } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { TeamChip } from "../components/TeamChip";
import { Icon } from "../components/Icon";
import { SeasonSelect } from "../components/SeasonSelect";
import { EmptyState, ErrorState, Spinner } from "../components/common";
import { PlayerDetail } from "./PlayerDetail";
import type { LeaderCard, PlayerRow } from "../api/types";

type SortKey =
  | "games_played" | "minutes" | "points" | "rebounds" | "assists"
  | "steals" | "blocks" | "fg_pct" | "fg3_pct" | "ft_pct";

interface Column {
  key: SortKey;
  label: string;
  int?: boolean;
}

const COLUMNS: Column[] = [
  { key: "games_played", label: "GP", int: true },
  { key: "minutes", label: "MIN" },
  { key: "points", label: "PPG" },
  { key: "rebounds", label: "REB" },
  { key: "assists", label: "AST" },
  { key: "steals", label: "STL" },
  { key: "blocks", label: "BLK" },
  { key: "fg_pct", label: "FG%" },
  { key: "fg3_pct", label: "3P%" },
  { key: "ft_pct", label: "FT%" },
];

export function PlayerStats() {
  const [season, setSeason] = useState<string | undefined>(undefined);
  const [selected, setSelected] = useState<{ id: number; name: string } | null>(null);
  const { data, loading, error, reload } = useAsync(() => api.players(season), [season]);
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("points");
  const [sortDir, setSortDir] = useState<-1 | 1>(-1);

  if (selected) {
    return <PlayerDetail playerId={selected.id} initialName={selected.name} onBack={() => setSelected(null)} />;
  }

  const rows = useMemo(() => {
    if (!data) return [];
    const q = search.toLowerCase().trim();
    const filtered = q
      ? data.rows.filter((r) => r.name.toLowerCase().includes(q) || r.team_abbr.toLowerCase().includes(q))
      : data.rows;
    return [...filtered].sort((a, b) => (a[sortKey] - b[sortKey]) * sortDir);
  }, [data, search, sortKey, sortDir]);

  const onSort = (key: SortKey) => {
    if (key === sortKey) setSortDir((d) => (d === -1 ? 1 : -1));
    else {
      setSortKey(key);
      setSortDir(-1);
    }
  };

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <div className="eyebrow">LEAGUE LEADERS</div>
          <h1 className="h1">Player Stats</h1>
        </div>
        <SeasonSelect value={season} onChange={setSeason} />
      </div>

      {error && <ErrorState message={error} onRetry={reload} />}
      {!error && loading && <Spinner label="Loading players…" />}
      {!error && !loading && data && !data.available && (
        <EmptyState>{data.message ?? "Player leaderboard is unavailable."}</EmptyState>
      )}

      {!error && !loading && data && data.available && (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 14, marginBottom: 20 }}>
            {data.leaders.map((l) => (
              <LeaderCardView key={l.category} leader={l} />
            ))}
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 14 }}>
            <div style={{ position: "relative", flex: 1, maxWidth: 300 }}>
              <Icon
                name="search"
                size={16}
                stroke="var(--ink-3)"
                strokeWidth={2}
                style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)" }}
              />
              <input
                className="input"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search players or teams…"
              />
            </div>
            <span style={{ fontSize: 12.5, color: "var(--ink-3)", fontWeight: 600 }}>{rows.length} players</span>
          </div>

          <div className="table-wrap">
            <table className="stat-table" style={{ minWidth: 820 }}>
              <thead>
                <tr>
                  <th className="left" style={{ position: "sticky", left: 0, background: "var(--surface-2)" }}>
                    PLAYER
                  </th>
                  {COLUMNS.map((c) => (
                    <th
                      key={c.key}
                      className={`sortable${sortKey === c.key ? " active" : ""}`}
                      onClick={() => onSort(c.key)}
                    >
                      {c.label}
                      {sortKey === c.key ? (sortDir < 0 ? " ↓" : " ↑") : ""}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <PlayerTableRow
                    key={r.player_id || `${r.name}-${r.team_abbr}`}
                    row={r}
                    rank={i + 1}
                    sortKey={sortKey}
                    onSelect={() => setSelected({ id: r.player_id, name: r.name })}
                  />
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

function LeaderCardView({ leader }: { leader: LeaderCard }) {
  return (
    <div className="card" style={{ padding: 18, display: "flex", alignItems: "center", gap: 14 }}>
      <TeamChip abbr={leader.team_abbr} color={leader.team_color} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: "var(--ink-3)", letterSpacing: 0.4 }}>
          {leader.category}
        </div>
        <div style={{ fontWeight: 700, fontSize: 15, letterSpacing: -0.2 }}>{leader.name}</div>
        <div style={{ fontSize: 12, color: "var(--ink-3)", fontWeight: 500 }}>{leader.team_name}</div>
      </div>
      <div style={{ textAlign: "right" }}>
        <div className="display tnum" style={{ fontWeight: 800, fontSize: 26, color: "var(--accent)" }}>
          {leader.value.toFixed(1)}
        </div>
        <div style={{ fontSize: 10.5, fontWeight: 700, color: "var(--ink-3)" }}>{leader.unit}</div>
      </div>
    </div>
  );
}

function PlayerTableRow({
  row,
  rank,
  sortKey,
  onSelect,
}: {
  row: PlayerRow;
  rank: number;
  sortKey: SortKey;
  onSelect: () => void;
}) {
  return (
    <tr style={{ cursor: "pointer" }} onClick={onSelect}>
      <td className="left" style={{ position: "sticky", left: 0, background: "inherit" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 11 }}>
          <span style={{ width: 22, fontWeight: 800, fontSize: 12, color: "var(--ink-3)" }}>{rank}</span>
          <TeamChip abbr={row.team_abbr} color={row.team_color} size="sm" />
          <div>
            <div style={{ fontWeight: 700, fontSize: 13.5, color: "var(--accent)" }}>{row.name}</div>
            <div style={{ fontSize: 11, color: "var(--ink-3)", fontWeight: 500 }}>{row.team_abbr}</div>
          </div>
        </div>
      </td>
      {COLUMNS.map((c) => {
        const value = row[c.key];
        const active = sortKey === c.key;
        return (
          <td
            key={c.key}
            style={{ color: active ? "var(--ink)" : "var(--ink-2)", fontWeight: active ? 800 : 600 }}
          >
            {c.int ? value : value.toFixed(1)}
          </td>
        );
      })}
    </tr>
  );
}
