import { useState } from "react";
import { api } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { TeamChip } from "../components/TeamChip";
import { Icon } from "../components/Icon";
import { ErrorState, Spinner } from "../components/common";
import type { BracketColumn, ChampionshipOdd, SeriesResult, SimulateResponse, TeamRef } from "../api/types";

const N_SIMS = 2000;

export function PlayoffSimulator() {
  const seeds = useAsync(() => api.seeds(), []);
  const [sim, setSim] = useState<SimulateResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    setBusy(true);
    setError(null);
    try {
      setSim(await api.simulate(N_SIMS));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Simulation failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <div className="eyebrow">BRACKET PROJECTION</div>
          <h1 className="h1">Playoff Simulator</h1>
        </div>
        {!busy && (
          <button className={sim ? "btn-ghost" : "btn"} style={sim ? undefined : { padding: "12px 22px" }} onClick={run}>
            {sim ? "Re-simulate" : "Simulate Playoffs"}
          </button>
        )}
      </div>

      {error && <ErrorState message={error} onRetry={run} />}
      {busy && <Spinner label={`Running ${N_SIMS.toLocaleString()} simulations…`} />}

      {!busy && !error && !sim && seeds.loading && <Spinner label="Loading seeds…" />}
      {!busy && !error && !sim && seeds.error && <ErrorState message={seeds.error} onRetry={seeds.reload} />}
      {!busy && !error && !sim && seeds.data && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 }}>
          <SeedCard title="Eastern Conference" accent="var(--accent)" teams={seeds.data.east} />
          <SeedCard title="Western Conference" accent="var(--gold)" teams={seeds.data.west} />
        </div>
      )}

      {!busy && !error && sim && <SimResult sim={sim} />}
    </div>
  );
}

function SeedCard({ title, accent, teams }: { title: string; accent: string; teams: TeamRef[] }) {
  return (
    <div className="card" style={{ padding: 20 }}>
      <div className="display" style={{ fontWeight: 800, fontSize: 16, marginBottom: 14, display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ width: 9, height: 9, borderRadius: 2, background: accent }} />
        {title}
      </div>
      {teams.map((t, i) => (
        <div key={t.team_id} style={{ display: "flex", alignItems: "center", gap: 12, padding: "8px 0", borderBottom: "1px solid var(--line)" }}>
          <span style={{ width: 20, fontWeight: 800, color: "var(--ink-3)", fontSize: 13 }}>{i + 1}</span>
          <TeamChip abbr={t.abbr} color={t.color} size="sm" />
          <span style={{ fontWeight: 700, fontSize: 14, flex: 1 }}>
            {t.city} {t.name}
          </span>
          <span style={{ fontSize: 13, color: "var(--ink-3)", fontWeight: 600 }}>{t.record ?? "—"}</span>
        </div>
      ))}
    </div>
  );
}

function SimResult({ sim }: { sim: SimulateResponse }) {
  const maxProb = sim.odds.length ? sim.odds[0].probability : 1;
  return (
    <div style={{ animation: "pop .3s" }}>
      <div
        style={{
          background: "linear-gradient(135deg,var(--accent),var(--accent-2))",
          borderRadius: 20,
          padding: 26,
          marginBottom: 20,
          display: "flex",
          alignItems: "center",
          gap: 22,
          boxShadow: "var(--shadow)",
        }}
      >
        <Icon name="trophy" size={50} stroke="#fff" strokeWidth={1.6} />
        <div>
          <div style={{ fontSize: 12.5, fontWeight: 700, color: "rgba(255,255,255,.8)", letterSpacing: 0.5 }}>
            PROJECTED CHAMPION
          </div>
          <div className="display" style={{ fontWeight: 800, fontSize: 32, color: "#fff", letterSpacing: -0.5 }}>
            {sim.champion.city} {sim.champion.name}
          </div>
          <div style={{ fontSize: 13.5, color: "rgba(255,255,255,.85)", fontWeight: 600, marginTop: 2 }}>
            defeats {sim.runner_up.name} {sim.final_higher_wins >= sim.final_lower_wins ? sim.final_higher_wins : sim.final_lower_wins}
            –{sim.final_higher_wins >= sim.final_lower_wins ? sim.final_lower_wins : sim.final_higher_wins} in the Finals
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.6fr 1fr", gap: 18 }}>
        <div className="card" style={{ padding: 20, overflowX: "auto" }}>
          <div className="display" style={{ fontWeight: 800, fontSize: 15, marginBottom: 16 }}>
            Bracket Run
          </div>
          <div style={{ display: "flex", gap: 14, minWidth: 600 }}>
            {sim.columns.map((col, i) => (
              <BracketColumnView key={i} column={col} />
            ))}
          </div>
        </div>

        <div className="card" style={{ padding: 20 }}>
          <div className="display" style={{ fontWeight: 800, fontSize: 15, marginBottom: 4 }}>
            Championship Odds
          </div>
          <div style={{ fontSize: 11.5, color: "var(--ink-3)", fontWeight: 600, marginBottom: 16 }}>
            From {sim.n_simulations.toLocaleString()} simulations
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 11 }}>
            {sim.odds.slice(0, 8).map((o) => (
              <OddsRow key={o.team.team_id} odd={o} maxProb={maxProb} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function BracketColumnView({ column }: { column: BracketColumn }) {
  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 10 }}>
      <div style={{ fontSize: 10.5, fontWeight: 700, color: "var(--ink-3)", letterSpacing: 0.4, textAlign: "center" }}>
        {column.label}
      </div>
      <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "space-around", gap: 10 }}>
        {column.series.map((s, i) => (
          <SeriesBox key={i} series={s} />
        ))}
      </div>
    </div>
  );
}

function SeriesBox({ series }: { series: SeriesResult }) {
  const row = (team: TeamRef, wins: number, won: boolean) => (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 7,
        padding: "6px 9px",
        background: won ? "var(--accent-soft)" : "transparent",
        opacity: won ? 1 : 0.55,
      }}
    >
      <TeamChip abbr={team.abbr} color={team.color} size="xs" />
      <span style={{ flex: 1, fontWeight: 700, fontSize: 12 }}>{team.abbr}</span>
      <span style={{ fontSize: 11, fontWeight: 700, color: "var(--ink-3)" }}>{wins}</span>
    </div>
  );
  return (
    <div style={{ border: "1px solid var(--line)", borderRadius: 10, overflow: "hidden", background: "var(--surface-2)" }}>
      {row(series.higher, series.higher_wins, series.higher_won)}
      <div style={{ borderTop: "1px solid var(--line)" }}>{row(series.lower, series.lower_wins, !series.higher_won)}</div>
    </div>
  );
}

function OddsRow({ odd, maxProb }: { odd: ChampionshipOdd; maxProb: number }) {
  const pctLabel = `${Math.round(odd.probability * 100)}%`;
  const barWidth = maxProb > 0 ? `${(odd.probability / maxProb) * 100}%` : "0%";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 11 }}>
      <TeamChip abbr={odd.team.abbr} color={odd.team.color} size="sm" />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
          <span style={{ fontWeight: 700, fontSize: 13 }}>{odd.team.name}</span>
          <span className="tnum" style={{ fontWeight: 800, fontSize: 13, color: "var(--accent)" }}>
            {pctLabel}
          </span>
        </div>
        <div style={{ height: 6, background: "var(--surface-3)", borderRadius: 3, overflow: "hidden" }}>
          <div style={{ width: barWidth, height: "100%", background: odd.team.color, borderRadius: 3 }} />
        </div>
      </div>
    </div>
  );
}
