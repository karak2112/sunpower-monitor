import { useMemo } from "react";

type Point = { time: string; value: number };

function formatKw(n: number): string {
  return `${n.toFixed(2)} kW`;
}

export function Overview({
  pv,
  load,
  net,
}: {
  pv: number | null;
  load: number | null;
  net: number | null;
}) {
  const gridMode = net == null ? "unknown" : net < 0 ? "export" : "import";
  const gridAbs = net == null ? null : Math.abs(net);

  return (
    <section className="section">
      <h2>Live power</h2>
      <div className="flow">
        <article className="stat solar">
          <div className="label">Solar</div>
          <div className="value">{pv == null ? "—" : formatKw(pv)}</div>
          <div className="meta">Measured production</div>
        </article>
        <article className="stat load">
          <div className="label">Home</div>
          <div className="value">{load == null ? "—" : formatKw(load)}</div>
          <div className="meta">Site load</div>
        </article>
        <article className={`stat grid ${gridMode}`}>
          <div className="label">Grid</div>
          <div className="value">{gridAbs == null ? "—" : formatKw(gridAbs)}</div>
          <div className="meta">
            {gridMode === "export" ? "Exporting" : gridMode === "import" ? "Importing" : "Net flow"}
          </div>
        </article>
      </div>
    </section>
  );
}

export function DayChart({ points }: { points: Point[] }) {
  const { path, area, maxY, labels } = useMemo(() => {
    if (points.length === 0) {
      return { path: "", area: "", maxY: 1, labels: [] as string[] };
    }
    const values = points.map((p) => p.value);
    const maxY = Math.max(...values, 0.1);
    const w = 640;
    const h = 220;
    const pad = 16;
    const coords = points.map((p, i) => {
      const x = pad + (i / Math.max(points.length - 1, 1)) * (w - pad * 2);
      const y = h - pad - (p.value / maxY) * (h - pad * 2);
      return [x, y] as const;
    });
    const path = coords.map((c, i) => `${i === 0 ? "M" : "L"}${c[0].toFixed(1)},${c[1].toFixed(1)}`).join(" ");
    const area = `${path} L${coords.at(-1)![0].toFixed(1)},${h - pad} L${coords[0][0].toFixed(1)},${h - pad} Z`;
    const labels = [
      new Date(points[0].time).toLocaleTimeString([], { hour: "numeric" }),
      new Date(points[Math.floor(points.length / 2)].time).toLocaleTimeString([], { hour: "numeric" }),
      new Date(points.at(-1)!.time).toLocaleTimeString([], { hour: "numeric" }),
    ];
    return { path, area, maxY, labels };
  }, [points]);

  return (
    <section className="section">
      <h2>Day chart</h2>
      <div className="panel chart-wrap">
        {points.length < 2 ? (
          <p className="muted">Not enough history yet. The collector adds points every poll interval.</p>
        ) : (
          <svg viewBox="0 0 640 240" role="img" aria-label="Solar production over time">
            <defs>
              <linearGradient id="fillGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.45" />
                <stop offset="100%" stopColor="var(--accent)" stopOpacity="0.02" />
              </linearGradient>
            </defs>
            <path d={area} fill="url(#fillGrad)" />
            <path d={path} fill="none" stroke="var(--accent)" strokeWidth="2.5" strokeLinejoin="round" />
            <text x="16" y="18" fill="var(--muted)" fontSize="12">
              max {maxY.toFixed(2)} kW
            </text>
            <text x="16" y="232" fill="var(--muted)" fontSize="12">
              {labels[0]}
            </text>
            <text x="300" y="232" fill="var(--muted)" fontSize="12" textAnchor="middle">
              {labels[1]}
            </text>
            <text x="624" y="232" fill="var(--muted)" fontSize="12" textAnchor="end">
              {labels[2]}
            </text>
          </svg>
        )}
      </div>
    </section>
  );
}
