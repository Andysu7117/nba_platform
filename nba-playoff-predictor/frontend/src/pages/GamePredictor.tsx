import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { TeamChip } from "../components/TeamChip";
import { ErrorState, Spinner } from "../components/common";
import type { PredictFactor, PredictResponse, TeamRef } from "../api/types";

export function GamePredictor() {
  const teams = useAsync(() => api.teams(), []);
  const [awayAbbr, setAwayAbbr] = useState("LAL");
  const [homeAbbr, setHomeAbbr] = useState("BOS");
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reset a stale result whenever the matchup changes.
  useEffect(() => setResult(null), [awayAbbr, homeAbbr]);

  const teamList = teams.data ?? [];
  const away = teamList.find((t) => t.abbr === awayAbbr);
  const home = teamList.find((t) => t.abbr === homeAbbr);
  const sameTeam = awayAbbr === homeAbbr;

  const run = async () => {
    setRunning(true);
    setError(null);
    try {
      setResult(await api.predict(homeAbbr, awayAbbr));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Prediction failed");
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="page page--narrow">
      <div style={{ marginBottom: 26 }}>
        <div className="eyebrow">MATCHUP ANALYZER</div>
        <h1 className="h1">Game Predictor</h1>
        <p className="subtitle">
          Pick any two teams to project a winner, final score, and the edge that decides it.
        </p>
      </div>

      {teams.loading && <Spinner label="Loading teams…" />}
      {teams.error && <ErrorState message={teams.error} onRetry={teams.reload} />}

      {!teams.loading && !teams.error && (
        <>
          <div className="panel">
            <div style={{ display: "grid", gridTemplateColumns: "1fr auto 1fr", gap: 18, alignItems: "center" }}>
              <TeamPicker label="Away" team={away} value={awayAbbr} options={teamList} onChange={setAwayAbbr} />
              <div className="display" style={{ fontWeight: 800, fontSize: 22, color: "var(--ink-3)" }}>
                @
              </div>
              <TeamPicker label="Home" team={home} value={homeAbbr} options={teamList} onChange={setHomeAbbr} />
            </div>
            <button className="btn" style={{ marginTop: 22, width: "100%" }} disabled={sameTeam || running} onClick={run}>
              {running ? "Projecting…" : sameTeam ? "Pick two different teams" : "Predict Outcome"}
            </button>
          </div>

          {error && (
            <div style={{ marginTop: 18 }}>
              <ErrorState message={error} />
            </div>
          )}
          {result && away && home && <ResultPanel result={result} />}
        </>
      )}
    </div>
  );
}

function TeamPicker({
  label,
  team,
  value,
  options,
  onChange,
}: {
  label: string;
  team: TeamRef | undefined;
  value: string;
  options: TeamRef[];
  onChange: (abbr: string) => void;
}) {
  return (
    <div style={{ textAlign: "center" }}>
      <div style={{ margin: "0 auto 12px", width: 84 }}>
        {team && <TeamChip abbr={team.abbr} color={team.color} size="big" />}
      </div>
      <div style={{ fontWeight: 700, fontSize: 17, letterSpacing: -0.2 }}>{team?.city}</div>
      <div className="display" style={{ fontWeight: 700, fontSize: 20, letterSpacing: -0.3 }}>
        {team?.name}
      </div>
      <div style={{ fontSize: 12.5, color: "var(--ink-3)", fontWeight: 600, margin: "4px 0 12px" }}>
        {label} · {team?.record ?? "—"}
      </div>
      <select className="field" value={value} onChange={(e) => onChange(e.target.value)}>
        {options.map((t) => (
          <option key={t.abbr} value={t.abbr}>
            {t.city} {t.name}
          </option>
        ))}
      </select>
    </div>
  );
}

function ResultPanel({ result }: { result: PredictResponse }) {
  const homeWins = result.predicted_winner === "home";
  const winner = homeWins ? result.home : result.away;
  const conf = Math.round(Math.max(result.home_win_prob, result.away_win_prob) * 100);
  const awayPct = Math.round(result.away_win_prob * 100);
  const homePct = 100 - awayPct;

  return (
    <div className="panel" style={{ marginTop: 18, animation: "pop .3s" }}>
      <div style={{ textAlign: "center", marginBottom: 20 }}>
        <div style={{ fontSize: 12.5, fontWeight: 700, color: "var(--ink-3)", letterSpacing: 0.5 }}>
          PROJECTED WINNER
        </div>
        <div className="display" style={{ fontWeight: 800, fontSize: 28, letterSpacing: -0.5, color: "var(--accent)", marginTop: 4 }}>
          {winner.city} {winner.name}
        </div>
        <div style={{ fontSize: 13.5, color: "var(--ink-2)", fontWeight: 600, marginTop: 4 }}>
          Win probability {conf}% · projected by net rating, form &amp; home court
        </div>
      </div>

      <div
        className="display"
        style={{ display: "flex", height: 42, borderRadius: 12, overflow: "hidden", marginBottom: 8, fontWeight: 800, color: "#fff" }}
      >
        <div style={{ width: `${awayPct}%`, background: result.away.color, display: "flex", alignItems: "center", padding: "0 14px", fontSize: 16 }}>
          {awayPct}%
        </div>
        <div style={{ width: `${homePct}%`, background: result.home.color, display: "flex", alignItems: "center", justifyContent: "flex-end", padding: "0 14px", fontSize: 16 }}>
          {homePct}%
        </div>
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12.5, fontWeight: 700, color: "var(--ink-2)", marginBottom: 22 }}>
        <span>{result.away.abbr} win</span>
        <span>{result.home.abbr} win</span>
      </div>

      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 18, padding: 16, background: "var(--surface-2)", borderRadius: 14, marginBottom: 20 }}>
        <div style={{ fontSize: 11.5, fontWeight: 700, color: "var(--ink-3)", letterSpacing: 0.4 }}>PROJECTED FINAL</div>
        <div className="display tnum" style={{ fontWeight: 800, fontSize: 30 }}>
          {result.projected_away_score} – {result.projected_home_score}
        </div>
      </div>

      <div style={{ fontSize: 11.5, fontWeight: 700, color: "var(--ink-3)", letterSpacing: 0.4, marginBottom: 12 }}>
        KEY FACTORS
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {result.factors.map((f) => (
          <FactorRow key={f.label} factor={f} awayColor={result.away.color} homeColor={result.home.color} />
        ))}
      </div>
    </div>
  );
}

function FactorRow({ factor, awayColor, homeColor }: { factor: PredictFactor; awayColor: string; homeColor: string }) {
  const max = Math.max(factor.away_value, factor.home_value) || 1;
  const awayBetter = factor.higher_is_better ? factor.away_value > factor.home_value : factor.away_value < factor.home_value;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
      <div
        className="tnum"
        style={{ width: 54, textAlign: "right", fontWeight: 800, fontSize: 14, color: awayBetter ? "var(--ink)" : "var(--ink-3)" }}
      >
        {factor.away_value.toFixed(1)}
      </div>
      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 5 }}>
        <div style={{ textAlign: "center", fontSize: 12, fontWeight: 600, color: "var(--ink-2)" }}>{factor.label}</div>
        <div style={{ display: "flex", gap: 4, height: 6 }}>
          <div style={{ flex: 1, display: "flex", justifyContent: "flex-end" }}>
            <div style={{ width: `${(factor.away_value / max) * 100}%`, background: awayColor, borderRadius: 3 }} />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ width: `${(factor.home_value / max) * 100}%`, background: homeColor, borderRadius: 3 }} />
          </div>
        </div>
      </div>
      <div
        className="tnum"
        style={{ width: 54, fontWeight: 800, fontSize: 14, color: !awayBetter ? "var(--ink)" : "var(--ink-3)" }}
      >
        {factor.home_value.toFixed(1)}
      </div>
    </div>
  );
}
