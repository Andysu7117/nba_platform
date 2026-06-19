/** The coloured, rounded team-abbreviation square used throughout the UI. */
type ChipSize = "xs" | "sm" | "md" | "big";

const CLASS: Record<ChipSize, string> = {
  xs: "chip chip--xs",
  sm: "chip chip--sm",
  md: "chip",
  big: "chip chip--big",
};

export function TeamChip({
  abbr,
  color,
  size = "md",
}: {
  abbr: string;
  color: string;
  size?: ChipSize;
}) {
  return (
    <div className={CLASS[size]} style={{ background: color }}>
      {abbr}
    </div>
  );
}
