/** Small shared UI primitives: spinner, empty state, status badge, prob bar. */
import type { GameStatus } from "../api/types";

export function Spinner({ label }: { label?: string }) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "90px 0",
        gap: 18,
      }}
    >
      <div className="spinner" />
      {label && <div style={{ fontWeight: 700, color: "var(--ink-2)", fontSize: 15 }}>{label}</div>}
    </div>
  );
}

export function EmptyState({ children }: { children: React.ReactNode }) {
  return <div className="empty-state">{children}</div>;
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="empty-state" style={{ borderColor: "var(--neg)", color: "var(--neg)" }}>
      <div>{message}</div>
      {onRetry && (
        <button className="btn-ghost" style={{ marginTop: 14 }} onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}

export function StatusBadge({ status, label }: { status: GameStatus; label: string }) {
  const cls =
    status === "final" ? "badge badge--final" : status === "live" ? "badge badge--live" : "badge badge--sched";
  return <span className={cls}>{label}</span>;
}

/** Two-segment win-probability / share bar. */
export function SplitBar({
  awayPct,
  homePct,
  awayColor,
  homeColor,
  height = 6,
}: {
  awayPct: number;
  homePct: number;
  awayColor: string;
  homeColor: string;
  height?: number;
}) {
  return (
    <div style={{ display: "flex", height, borderRadius: 4, overflow: "hidden" }}>
      <div style={{ width: `${awayPct}%`, background: awayColor }} />
      <div style={{ width: `${homePct}%`, background: homeColor }} />
    </div>
  );
}
