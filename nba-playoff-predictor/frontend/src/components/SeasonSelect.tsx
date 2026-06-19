import { useAsync } from "../hooks/useAsync";
import { api } from "../api/client";

/**
 * Season dropdown. Fetches the selectable seasons itself and reports changes.
 * `value === undefined` means "current season"; the picker shows it selected.
 */
export function SeasonSelect({
  value,
  onChange,
}: {
  value: string | undefined;
  onChange: (season: string) => void;
}) {
  const { data } = useAsync(() => api.seasons(), []);
  const seasons = data?.seasons ?? [];
  const current = data?.current;

  return (
    <select
      className="field"
      style={{ width: "auto", cursor: "pointer" }}
      value={value ?? current ?? ""}
      onChange={(e) => onChange(e.target.value)}
      aria-label="Season"
    >
      {seasons.map((s) => (
        <option key={s} value={s}>
          {s.replace("-", "–")}
          {s === current ? " (current)" : ""}
        </option>
      ))}
    </select>
  );
}
