import { useState } from "react";
import { Sidebar } from "./components/Sidebar";
import { ErrorState } from "./components/common";
import { useAsync } from "./hooks/useAsync";
import { api } from "./api/client";
import { CurrentSeason } from "./pages/CurrentSeason";
import { GamePredictor } from "./pages/GamePredictor";
import { PlayoffSimulator } from "./pages/PlayoffSimulator";
import { PlayerStats } from "./pages/PlayerStats";
import { TeamStats } from "./pages/TeamStats";

export type PageId = "season" | "pred" | "playoff" | "players" | "teams";

export default function App() {
  const [page, setPage] = useState<PageId>("season");
  const meta = useAsync(() => api.meta(), []);

  return (
    <div className="app-shell">
      <Sidebar page={page} onNavigate={setPage} season={meta.data?.current_season ?? null} />
      <main className="main">
        {meta.error && (
          <div className="page">
            <ErrorState
              message={`Could not reach the API: ${meta.error}. Is the backend running on :8000?`}
              onRetry={meta.reload}
            />
          </div>
        )}
        {!meta.error && page === "season" && <CurrentSeason />}
        {!meta.error && page === "pred" && <GamePredictor />}
        {!meta.error && page === "playoff" && <PlayoffSimulator />}
        {!meta.error && page === "players" && <PlayerStats />}
        {!meta.error && page === "teams" && <TeamStats />}
      </main>
    </div>
  );
}
