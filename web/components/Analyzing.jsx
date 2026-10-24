"use client";

import { useEffect, useState } from "react";

const STEPS = [
  "Reading resume text",
  "Detecting entities (DistilBERT NER)",
  "Classifying sections (BiLSTM)",
  "Predicting role",
  "Embedding & scoring match",
];

/** Scanning animation shown while the real analysis API call runs. */
export default function Analyzing({ done, error }) {
  const [active, setActive] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setActive((a) => (a < STEPS.length - 1 ? a + 1 : a));
    }, 850);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="mx-auto flex max-w-lg flex-col items-center py-24">
      {/* stylised resume being scanned */}
      <div className="relative w-64 overflow-hidden rounded-[14px] border border-[rgba(255,255,255,0.1)] bg-[#151519] p-5">
        <div className="scan-beam" />
        <div className="space-y-2.5 opacity-90">
          <div className="h-3 w-1/2 rounded bg-white/25" />
          <div className="h-2 w-1/3 rounded bg-white/10" />
          <div className="mt-4 space-y-2">
            <div className="h-2 w-full rounded bg-white/10" />
            <div className="h-2 w-11/12 rounded bg-white/10" />
            <div className="h-2 w-full rounded bg-white/10" />
            <div className="h-2 w-4/6 rounded bg-white/10" />
            <div className="h-2 w-full rounded bg-white/10" />
            <div className="h-2 w-2/3 rounded bg-white/10" />
          </div>
          <div className="mt-4 flex gap-1.5">
            <div className="h-4 w-12 rounded bg-[#f97316]/40" />
            <div className="h-4 w-14 rounded bg-[#38bdf8]/40" />
            <div className="h-4 w-10 rounded bg-[#a78bfa]/40" />
          </div>
        </div>
      </div>

      {/* step checklist */}
      <div className="mt-10 w-full max-w-xs space-y-3">
        {STEPS.map((s, i) => {
          const state = error ? "error" : i < active ? "done" : i === active ? (done && i === STEPS.length - 1 ? "done" : "running") : "todo";
          return (
            <div key={s} className="flex items-center gap-3 text-[14px]">
              <span
                className={`grid h-5 w-5 shrink-0 place-items-center rounded-full border text-[10px] ${
                  state === "done"
                    ? "border-transparent bg-[#0099ff] text-black"
                    : state === "running"
                    ? "status-live border-[#0099ff] text-[#0099ff]"
                    : "border-white/15 text-[#666]"
                }`}
              >
                {state === "done" ? "✓" : i + 1}
              </span>
              <span className={state === "todo" ? "text-[#666]" : "text-white"}>{s}</span>
            </div>
          );
        })}
      </div>
      {error && <p className="mt-6 text-center text-[13px] text-red-300">{error}</p>}
    </div>
  );
}
