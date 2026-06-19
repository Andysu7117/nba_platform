import { Icon } from "./Icon";
import { useTheme } from "../context/ThemeContext";
import type { PageId } from "../App";
import { longDate, parseISO } from "../lib/format";

interface NavItem {
  id: PageId;
  label: string;
  icon: Parameters<typeof Icon>[0]["name"];
}

const NAV: NavItem[] = [
  { id: "season", label: "Current Season", icon: "calendar" },
  { id: "pred", label: "Game Predictor", icon: "target" },
  { id: "playoff", label: "Playoff Simulator", icon: "trophy" },
  { id: "players", label: "Player Stats", icon: "user" },
  { id: "teams", label: "Team Stats", icon: "bars" },
];

export function Sidebar({
  page,
  onNavigate,
  season,
  latestDate,
}: {
  page: PageId;
  onNavigate: (p: PageId) => void;
  season: string | null;
  latestDate: string | null;
}) {
  const { theme, toggle } = useTheme();

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">
          <Icon name="basketball" size={20} stroke="#fff" strokeWidth={2} />
        </div>
        <div>
          <div className="brand-name">Hardwood</div>
          <div className="brand-sub">{season ? `${season.replace("-", "–")} SEASON` : "NBA PLATFORM"}</div>
        </div>
      </div>

      <nav className="nav">
        {NAV.map((item) => (
          <button
            key={item.id}
            className={`nav-btn${page === item.id ? " active" : ""}`}
            onClick={() => onNavigate(item.id)}
          >
            <Icon name={item.icon} />
            {item.label}
          </button>
        ))}
      </nav>

      <div className="sidebar-foot">
        <div className="live-box">
          <div className="live-label">LATEST RESULTS</div>
          <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
            <span className="dot" style={{ background: "var(--accent)" }} />
            <span style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-2)" }}>
              {latestDate ? longDate(parseISO(latestDate)) : "No games cached"}
            </span>
          </div>
        </div>
        <button className="theme-toggle" onClick={toggle}>
          <span style={{ display: "flex", alignItems: "center", gap: 9 }}>
            <Icon name="moon" size={17} />
            {theme === "light" ? "Dark mode" : "Light mode"}
          </span>
        </button>
      </div>
    </aside>
  );
}
