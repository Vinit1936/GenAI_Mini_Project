"use client";

/** Radar of the four weighted components — gradient fill, value dots, % rings. */
export default function RadarChart({ breakdown }) {
  const axes = [
    ["Semantic", breakdown.semantic_similarity.score],
    ["Skills", breakdown.skill_overlap.score],
    ["Sections", breakdown.section_completeness.score],
    ["Role fit", breakdown.role_alignment.score],
  ];
  const cx = 140, cy = 128, R = 92;
  const pt = (i, frac) => {
    const ang = (Math.PI * 2 * i) / axes.length - Math.PI / 2;
    return [cx + Math.cos(ang) * R * frac, cy + Math.sin(ang) * R * frac];
  };
  const ring = (f) => axes.map((_, i) => pt(i, f).join(",")).join(" ");
  const dataPoly = axes.map(([_, v], i) => pt(i, Math.max(0.03, v / 100)).join(",")).join(" ");

  return (
    <svg width="300" height="268" viewBox="0 0 300 268" className="max-w-full">
      <defs>
        <linearGradient id="radarFill" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="rgba(52,211,153,0.35)" />
          <stop offset="100%" stopColor="rgba(45,212,191,0.12)" />
        </linearGradient>
      </defs>
      {[0.25, 0.5, 0.75, 1].map((f) => (
        <polygon key={f} points={ring(f)} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="1" />
      ))}
      <text x={cx - R - 6} y={cy + 3} textAnchor="end" fontSize="9" fill="#52525b">25</text>
      <text x={cx - R - 6} y={cy - R + 6} textAnchor="end" fontSize="9" fill="#52525b">100</text>
      {axes.map(([label], i) => {
        const [x, y] = pt(i, 1);
        return <line key={label} x1={cx} y1={cy} x2={x} y2={y} stroke="rgba(255,255,255,0.08)" />;
      })}
      <polygon points={dataPoly} fill="url(#radarFill)" stroke="#34d399" strokeWidth="2"
               style={{ transformOrigin: `${cx}px ${cy}px`, transition: "all 0.4s ease-out" }} />
      {axes.map(([label, v], i) => {
        const [dx, dy] = pt(i, Math.max(0.03, v / 100));
        const [lx, ly] = pt(i, 1.24);
        return (
          <g key={label}>
            <circle cx={dx} cy={dy} r="3.5" fill="#34d399" stroke="#0a0e13" strokeWidth="1.5"
                    style={{ transition: "cx 0.4s ease-out, cy 0.4s ease-out" }} />
            <text x={lx} y={ly - 4} textAnchor="middle" fontSize="11" fill="#a1a1aa">{label}</text>
            <text x={lx} y={ly + 9} textAnchor="middle" fontSize="11" fontWeight="600" fill="#e4e4e7">
              {Math.round(v)}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
