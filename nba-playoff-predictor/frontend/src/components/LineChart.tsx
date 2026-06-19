/** Minimal dependency-free SVG line chart (one or more series). */
export interface Series {
  values: (number | null)[];
  color: string;
  label: string;
  dashed?: boolean;
}

export function LineChart({ series, height = 230, yLabel }: { series: Series[]; height?: number; yLabel?: string }) {
  const W = 820;
  const H = height;
  const pad = { l: 40, r: 14, t: 16, b: 26 };

  const all = series.flatMap((s) => s.values).filter((v): v is number => v != null);
  const max = all.length ? Math.max(...all) : 1;
  const min = Math.min(0, all.length ? Math.min(...all) : 0);
  const span = max - min || 1;
  const n = Math.max(1, ...series.map((s) => s.values.length));

  const x = (i: number) => pad.l + (i / Math.max(n - 1, 1)) * (W - pad.l - pad.r);
  const y = (v: number) => pad.t + (1 - (v - min) / span) * (H - pad.t - pad.b);

  const toPath = (values: (number | null)[]) => {
    let d = "";
    let started = false;
    values.forEach((v, i) => {
      if (v == null) {
        started = false;
        return;
      }
      d += `${started ? "L" : "M"}${x(i).toFixed(1)} ${y(v).toFixed(1)} `;
      started = true;
    });
    return d.trim();
  };

  const ticks = 4;
  const gridVals = Array.from({ length: ticks + 1 }, (_, i) => min + (span * i) / ticks);

  return (
    <div style={{ width: "100%", overflow: "hidden" }}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" preserveAspectRatio="none" style={{ display: "block" }}>
        {gridVals.map((v, i) => (
          <g key={i}>
            <line x1={pad.l} x2={W - pad.r} y1={y(v)} y2={y(v)} stroke="var(--line)" strokeWidth={1} />
            <text x={pad.l - 6} y={y(v) + 3} textAnchor="end" fontSize={10} fill="var(--ink-3)" fontFamily="Hanken Grotesk">
              {Math.round(v)}
            </text>
          </g>
        ))}
        {series.map((s, i) => (
          <path
            key={i}
            d={toPath(s.values)}
            fill="none"
            stroke={s.color}
            strokeWidth={s.dashed ? 1.6 : 2.4}
            strokeDasharray={s.dashed ? "5 4" : undefined}
            strokeLinejoin="round"
            strokeLinecap="round"
          />
        ))}
        {yLabel && (
          <text x={pad.l} y={11} fontSize={10} fontWeight={700} fill="var(--ink-3)" fontFamily="Hanken Grotesk">
            {yLabel}
          </text>
        )}
      </svg>
    </div>
  );
}
