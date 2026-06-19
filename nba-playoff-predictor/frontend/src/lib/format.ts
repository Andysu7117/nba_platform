/** Small presentation helpers shared across pages. */

export const pct = (p: number | null | undefined): string =>
  p == null ? "—" : `${Math.round(p * 100)}%`;

export const pct1 = (p: number | null | undefined): string =>
  p == null ? "—" : `${(p * 100).toFixed(1)}%`;

/** ".677" style win-percentage (leading zero dropped, 3 decimals). */
export const pctRaw = (p: number): string => {
  const s = Math.round(p * 1000)
    .toString()
    .padStart(3, "0");
  return `.${s}`;
};

export const signed = (n: number): string => (n >= 0 ? `+${n}` : `−${Math.abs(n)}`);

export const fixed1 = (n: number): string => n.toFixed(1);

const WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const WEEKDAYS_SHORT = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];
const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

/** Parse a 'YYYY-MM-DD' string into a *local* date (no timezone surprises). */
export const parseISO = (iso: string): Date => {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d);
};

export const toISO = (d: Date): string => {
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${m}-${day}`;
};

export const addDays = (d: Date, n: number): Date => {
  const out = new Date(d);
  out.setDate(out.getDate() + n);
  return out;
};

export const longDate = (d: Date): string =>
  `${WEEKDAYS[d.getDay()]}, ${MONTHS[d.getMonth()]} ${d.getDate()}`;

export const weekdayShort = (d: Date): string => WEEKDAYS_SHORT[d.getDay()];

/** Sunday that starts the week containing `d`. */
export const startOfWeek = (d: Date): Date => addDays(d, -d.getDay());
