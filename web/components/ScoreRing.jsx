"use client";

import { useEffect, useRef, useState } from "react";

/** Animated score ring with count-up number. Pure SVG, no chart libs. */
export default function ScoreRing({ score, size = 200 }) {
  const [shown, setShown] = useState(0);
  const raf = useRef(null);

  useEffect(() => {
    const start = performance.now();
    const dur = 900;
    const tick = (t) => {
      const p = Math.min(1, (t - start) / dur);
      const eased = 1 - Math.pow(1 - p, 3);
      setShown(score * eased);
      if (p < 1) raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf.current);
  }, [score]);

  const r = 78;
  const c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, shown)) / 100;
  const tone =
    score >= 70
      ? { from: "#34d399", to: "#2dd4bf", label: "strong match", cls: "text-emerald-300" }
      : score >= 45
      ? { from: "#fbbf24", to: "#fb923c", label: "partial match", cls: "text-amber-300" }
      : { from: "#f87171", to: "#ef4444", label: "weak match", cls: "text-red-300" };

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} viewBox="0 0 200 200">
        <defs>
          <linearGradient id="ringGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor={tone.from} />
            <stop offset="100%" stopColor={tone.to} />
          </linearGradient>
        </defs>
        <circle cx="100" cy="100" r={r} fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="14" />
        <circle
          cx="100" cy="100" r={r} fill="none" stroke="url(#ringGrad)" strokeWidth="14"
          strokeLinecap="round" strokeDasharray={`${c * pct} ${c}`} transform="rotate(-90 100 100)"
          style={{ filter: `drop-shadow(0 0 10px ${tone.from}40)` }}
        />
        <text x="100" y="94" textAnchor="middle" fontSize="52" fontWeight="700" fill="#f4f4f5">
          {Math.round(shown)}
        </text>
        <text x="100" y="118" textAnchor="middle" fontSize="13" fill="#71717a">/ 100</text>
      </svg>
      <p className={`-mt-2 text-sm font-medium ${tone.cls}`}>{tone.label}</p>
    </div>
  );
}
