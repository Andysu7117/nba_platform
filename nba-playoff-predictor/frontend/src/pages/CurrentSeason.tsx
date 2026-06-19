import { useMemo, useState } from "react";
import { api } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { TeamChip } from "../components/TeamChip";
import { Icon } from "../components/Icon";
import { BoxScoreModal } from "../components/BoxScoreModal";
import { EmptyState, ErrorState, Spinner, StatusBadge } from "../components/common";
import { addDays, longDate, parseISO, startOfWeek, toISO, weekdayShort } from "../lib/format";
import type { GameSummary } from "../api/types";

type Layout = "cards" | "list" | "time";
const LAYOUTS: { id: Layout; label: string }[] = [
  { id: "cards", label: "Cards" },
  { id: "list", label: "List" },
  { id: "time", label: "Timeline" },
];

export function CurrentSeason({ latestDate }: { latestDate: string | null }) {
  const fallbackToday = latestDate ?? toISO(new Date());
  const [date, setDate] = useState(fallbackToday);
  const [layout, setLayout] = useState<Layout>("cards");
  const [openGame, setOpenGame] = useState<GameSummary | null>(null);

  const selected = parseISO(date);
  const weekStart = startOfWeek(selected);
  const weekEnd = addDays(weekStart, 6);

  const schedule = useAsync(() => api.schedule(date), [date]);
  const calendar = useAsync(() => api.calendar(toISO(weekStart), toISO(weekEnd)), [toISO(weekStart)]);

  const countByDate = useMemo(() => {
    const map = new Map<string, number>();
    calendar.data?.days.forEach((d) => map.set(d.date, d.count));
    return map;
  }, [calendar.data]);

  const games = schedule.data?.games ?? [];

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <div className="eyebrow">GAMES</div>
          <h1 className="h1">{longDate(selected)}</h1>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ display: "flex", alignItems: "center", background: "var(--surface)", border: "1px solid var(--line)", borderRadius: 12, padding: 4, boxShadow: "var(--card)" }}>
            <button className="icon-btn" onClick={() => setDate(toISO(addDays(selected, -1)))}>
              <Icon name="chevron-left" size={18} strokeWidth={2} />
            </button>
            <button
              className="icon-btn"
              style={{ width: "auto", padding: "0 14px", color: "var(--ink)", fontWeight: 700, fontSize: 13 }}
              onClick={() => setDate(fallbackToday)}
            >
              Today
            </button>
            <button className="icon-btn" onClick={() => setDate(toISO(addDays(selected, 1)))}>
              <Icon name="chevron-right" size={18} strokeWidth={2} />
            </button>
          </div>
          <div className="seg-group">
            {LAYOUTS.map((l) => (
              <button key={l.id} className={`seg${layout === l.id ? " active" : ""}`} onClick={() => setLayout(l.id)}>
                {l.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(7,1fr)", gap: 8, marginBottom: 26 }}>
        {Array.from({ length: 7 }, (_, i) => addDays(weekStart, i)).map((d) => {
          const iso = toISO(d);
          const active = iso === date;
          return (
            <button
              key={iso}
              onClick={() => setDate(iso)}
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 3,
                padding: "12px 6px",
                borderRadius: 14,
                cursor: "pointer",
                border: `1.5px solid ${active ? "var(--accent)" : "var(--line)"}`,
                background: active ? "var(--accent-soft)" : "var(--surface)",
                color: active ? "var(--accent)" : "var(--ink)",
                transition: "border-color .15s",
              }}
            >
              <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: 0.5, opacity: 0.7 }}>{weekdayShort(d)}</span>
              <span className="display" style={{ fontWeight: 700, fontSize: 21, lineHeight: 1.1 }}>
                {d.getDate()}
              </span>
              <span style={{ fontSize: 10.5, fontWeight: 700, color: active ? "var(--accent)" : "var(--ink-3)" }}>
                {countByDate.get(iso) ?? 0} games
              </span>
            </button>
          );
        })}
      </div>

      {schedule.error && <ErrorState message={schedule.error} onRetry={schedule.reload} />}
      {!schedule.error && schedule.loading && <Spinner label="Loading games…" />}
      {!schedule.error && !schedule.loading && games.length === 0 && (
        <EmptyState>No NBA games found for {longDate(selected)}.</EmptyState>
      )}

      {!schedule.error && !schedule.loading && games.length > 0 && (
        <>
          {layout === "cards" && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(330px,1fr))", gap: 16 }}>
              {games.map((g) => (
                <GameCard key={g.game_id} game={g} onOpen={() => setOpenGame(g)} />
              ))}
            </div>
          )}
          {layout === "list" && (
            <div className="table-wrap">
              {games.map((g) => (
                <GameRow key={g.game_id} game={g} onOpen={() => setOpenGame(g)} />
              ))}
            </div>
          )}
          {layout === "time" && (
            <div>
              {games.map((g) => (
                <TimelineItem key={g.game_id} game={g} onOpen={() => setOpenGame(g)} />
              ))}
            </div>
          )}
        </>
      )}

      {openGame && <BoxScoreModal game={openGame} onClose={() => setOpenGame(null)} />}
    </div>
  );
}

/* ---- helpers ---- */
function probPcts(g: GameSummary): { away: number; home: number } | null {
  if (g.home_win_prob == null || g.away_win_prob == null) return null;
  const home = Math.round(g.home_win_prob * 100);
  return { home, away: 100 - home };
}

function inkFor(g: GameSummary, side: "home" | "away"): string {
  if (g.winner == null) return "var(--ink)";
  return g.winner === side ? "var(--ink)" : "var(--ink-3)";
}

/* ---- Cards ---- */
function GameCard({ game, onOpen }: { game: GameSummary; onOpen: () => void }) {
  const probs = probPcts(game);
  return (
    <div
      className="card"
      style={{ padding: 18, cursor: "pointer", transition: "transform .18s, box-shadow .18s" }}
      onClick={onOpen}
      onMouseEnter={(e) => (e.currentTarget.style.transform = "translateY(-2px)")}
      onMouseLeave={(e) => (e.currentTarget.style.transform = "none")}
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
        <StatusBadge status={game.status} label="FINAL" />
        <span style={{ fontSize: 12, fontWeight: 600, color: "var(--ink-3)" }}>Box score ›</span>
      </div>
      <ScoreLine team={game.away} score={game.away_score} ink={inkFor(game, "away")} />
      <div style={{ height: 11 }} />
      <ScoreLine team={game.home} score={game.home_score} ink={inkFor(game, "home")} />
      {probs && (
        <div style={{ marginTop: 14, paddingTop: 13, borderTop: "1px solid var(--line)" }}>
          <div style={{ display: "flex", height: 6, borderRadius: 4, overflow: "hidden", marginBottom: 9 }}>
            <div style={{ width: `${probs.away}%`, background: game.away.color }} />
            <div style={{ width: `${probs.home}%`, background: game.home.color }} />
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11.5, fontWeight: 600, color: "var(--ink-3)" }}>
            <span>Pre-game model</span>
            <span>
              {game.away.abbr} {probs.away}% · {game.home.abbr} {probs.home}%
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

function ScoreLine({ team, score, ink }: { team: GameSummary["home"]; score: number | null; ink: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
      <TeamChip abbr={team.abbr} color={team.color} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 700, fontSize: 15, color: ink, letterSpacing: -0.2 }}>
          {team.city} {team.name}
        </div>
        <div style={{ fontSize: 12, color: "var(--ink-3)", fontWeight: 500 }}>{team.record ?? ""}</div>
      </div>
      <div className="display tnum" style={{ fontWeight: 800, fontSize: 26, color: ink }}>
        {score ?? "—"}
      </div>
    </div>
  );
}

/* ---- List ---- */
function GameRow({ game, onOpen }: { game: GameSummary; onOpen: () => void }) {
  const compact = (team: GameSummary["home"], score: number | null, ink: string) => (
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <TeamChip abbr={team.abbr} color={team.color} size="sm" />
      <span style={{ fontWeight: 700, fontSize: 14, color: ink, flex: 1, minWidth: 0 }}>
        {team.city} {team.name}
      </span>
      <span style={{ fontSize: 12, color: "var(--ink-3)", width: 54, textAlign: "right" }}>{team.record ?? ""}</span>
      <span className="display tnum" style={{ fontWeight: 800, fontSize: 18, color: ink, width: 38, textAlign: "right" }}>
        {score ?? "—"}
      </span>
    </div>
  );
  return (
    <div
      onClick={onOpen}
      style={{ display: "flex", alignItems: "center", gap: 16, padding: "14px 18px", borderBottom: "1px solid var(--line)", cursor: "pointer" }}
      onMouseEnter={(e) => (e.currentTarget.style.background = "var(--surface-2)")}
      onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
    >
      <span className="badge badge--final" style={{ width: 64, justifyContent: "center", flex: "none" }}>
        FINAL
      </span>
      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 7, minWidth: 0 }}>
        {compact(game.away, game.away_score, inkFor(game, "away"))}
        {compact(game.home, game.home_score, inkFor(game, "home"))}
      </div>
      <div style={{ width: 120, flex: "none", textAlign: "right", borderLeft: "1px solid var(--line)", paddingLeft: 16 }}>
        <div style={{ fontSize: 12.5, fontWeight: 700, color: "var(--ink-2)" }}>Final</div>
        <div style={{ fontSize: 11.5, color: "var(--ink-3)", fontWeight: 500, marginTop: 2 }}>Box score ›</div>
      </div>
    </div>
  );
}

/* ---- Timeline ---- */
function TimelineItem({ game, onOpen }: { game: GameSummary; onOpen: () => void }) {
  const line = (team: GameSummary["home"], score: number | null, ink: string) => (
    <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
      <TeamChip abbr={team.abbr} color={team.color} />
      <div style={{ minWidth: 120 }}>
        <div style={{ fontWeight: 700, fontSize: 14.5, color: ink }}>{team.name}</div>
        <div style={{ fontSize: 11.5, color: "var(--ink-3)" }}>{team.record ?? ""}</div>
      </div>
      <div className="display tnum" style={{ fontWeight: 800, fontSize: 24, color: ink }}>
        {score ?? "—"}
      </div>
    </div>
  );
  return (
    <div style={{ display: "flex", gap: 20, alignItems: "stretch" }}>
      <div style={{ position: "relative", flex: "none", display: "flex", flexDirection: "column", alignItems: "center" }}>
        <span style={{ width: 13, height: 13, borderRadius: "50%", background: "var(--ink-3)", border: "3px solid var(--surface)", marginTop: 18 }} />
        <span style={{ flex: 1, width: 2, background: "var(--line)" }} />
      </div>
      <div
        onClick={onOpen}
        style={{ flex: 1, display: "flex", gap: 18, alignItems: "center", background: "var(--surface)", border: "1px solid var(--line)", borderRadius: 16, padding: "16px 18px", marginBottom: 18, boxShadow: "var(--card)", cursor: "pointer" }}
      >
        {line(game.away, game.away_score, inkFor(game, "away"))}
        <div className="display" style={{ fontWeight: 700, fontSize: 12, color: "var(--ink-3)", textAlign: "center" }}>
          @
        </div>
        {line(game.home, game.home_score, inkFor(game, "home"))}
        <div style={{ marginLeft: "auto", alignSelf: "center", textAlign: "right", paddingLeft: 18, borderLeft: "1px solid var(--line)" }}>
          <span className="badge badge--final">FINAL</span>
        </div>
      </div>
    </div>
  );
}
