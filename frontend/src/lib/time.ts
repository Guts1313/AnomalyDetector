// Backend serializes timestamps via `datetime.utcnow().isoformat()`, which
// produces a naive ISO string with no `Z` suffix. `new Date(naiveString)`
// then interprets it as LOCAL time, not UTC, so Amsterdam users saw values
// shifted by their UTC offset. Force-tag as UTC, then render in Amsterdam.

const TZ = "Europe/Amsterdam";

function parseAsUtc(raw: string): Date {
  // Already has explicit zone (Z or +hh:mm) — trust it.
  if (/Z|[+-]\d{2}:?\d{2}$/.test(raw)) return new Date(raw);
  return new Date(`${raw}Z`);
}

const dateTimeFmt = new Intl.DateTimeFormat("sv-SE", {
  timeZone: TZ,
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  hour12: false,
});

const timeFmt = new Intl.DateTimeFormat("sv-SE", {
  timeZone: TZ,
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  hour12: false,
});

export function formatAmsterdam(raw: string): string {
  return dateTimeFmt.format(parseAsUtc(raw));
}

export function nowTimeAmsterdam(): string {
  return timeFmt.format(new Date());
}
