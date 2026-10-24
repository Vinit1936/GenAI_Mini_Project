"use client";

import { useState } from "react";

const SECTION_COLORS = {
  experience: "#38bdf8",
  education: "#a78bfa",
  skills: "#f97316",
  project: "#fbbf24",
  other: "#666",
};

/** Text-mode preview: plain text, section map (BiLSTM), sentence relevance heatmap (MiniLM), or Google XYZ Impact inspector. */
export default function ResumeXray({ text, sectionLines, semanticHeatmap, impactAnalysis, defaultMode = "preview" }) {
  const [mode, setMode] = useState(defaultMode);
  const [tierFilter, setTierFilter] = useState("all");
  const [impactFilter, setImpactFilter] = useState("all");

  const heatmap = semanticHeatmap || [];
  const counts = {
    all: heatmap.length,
    high: heatmap.filter((h) => h.tier === "high").length,
    moderate: heatmap.filter((h) => h.tier === "moderate").length,
    low: heatmap.filter((h) => h.tier === "low").length,
  };

  const filteredHeatmap = tierFilter === "all" ? heatmap : heatmap.filter((h) => h.tier === tierFilter);

  const impact = impactAnalysis || {
    score: 0,
    total_bullets: 0,
    xyz_count: 0,
    quantified_count: 0,
    weak_verb_count: 0,
    bullets: [],
  };

  const filteredBullets = impact.bullets.filter((b) => {
    if (impactFilter === "all") return true;
    if (impactFilter === "xyz") return b.is_xyz;
    if (impactFilter === "missing_metric") return !b.has_metric;
    if (impactFilter === "weak_verb") return b.is_weak;
    return true;
  });

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex rounded-full border border-[rgba(255,255,255,0.1)] bg-[#151519] p-0.5 text-[12px] font-medium">
          {[
            ["preview", "Preview"],
            ["sections", "Section map"],
            ["heatmap", "Relevance Heatmap"],
            ["impact", "XYZ Formula & Impact"],
          ].map(([v, label]) => (
            <button
              key={v}
              onClick={() => setMode(v)}
              className={`rounded-full px-3 py-1.5 transition-colors cursor-pointer ${
                mode === v ? "bg-[#1c1c22] text-white shadow-sm" : "text-[#888] hover:text-white"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
        <span className="text-[11px] text-[#777]">
          {mode === "sections"
            ? "sections labelled by BiLSTM"
            : mode === "heatmap"
            ? "sentence attribution via MiniLM"
            : mode === "impact"
            ? "Google XYZ & quantifiable metrics"
            : "plain text extracted"}
        </span>
      </div>

      {mode === "impact" ? (
        <div className="space-y-3">
          {/* Top Impact Overview Card */}
          <div className="grid grid-cols-4 gap-2 rounded-xl border border-white/[0.08] bg-[#101014] p-3 text-center">
            <div className="border-r border-white/[0.06]">
              <p className="text-[10px] uppercase tracking-wider text-[#777]">Impact Score</p>
              <p className="mt-0.5 text-lg font-bold text-emerald-400">{impact.score}%</p>
            </div>
            <div className="border-r border-white/[0.06]">
              <p className="text-[10px] uppercase tracking-wider text-[#777]">Google XYZ</p>
              <p className="mt-0.5 text-lg font-bold text-[#f4f4f5]">
                {impact.xyz_count}
                <span className="text-xs font-normal text-[#777]">/{impact.total_bullets}</span>
              </p>
            </div>
            <div className="border-r border-white/[0.06]">
              <p className="text-[10px] uppercase tracking-wider text-[#777]">Quantified</p>
              <p className="mt-0.5 text-lg font-bold text-[#f4f4f5]">
                {impact.quantified_count}
                <span className="text-xs font-normal text-[#777]">/{impact.total_bullets}</span>
              </p>
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-wider text-[#777]">Weak Verbs</p>
              <p
                className={`mt-0.5 text-lg font-bold ${
                  impact.weak_verb_count > 0 ? "text-amber-400" : "text-emerald-400"
                }`}
              >
                {impact.weak_verb_count}
              </p>
            </div>
          </div>

          {/* Filter Pills */}
          <div className="flex flex-wrap items-center gap-2 text-[11px]">
            <span className="text-[#777]">Filter:</span>
            <button
              onClick={() => setImpactFilter("all")}
              className={`rounded-full px-2.5 py-1 transition-colors cursor-pointer ${
                impactFilter === "all"
                  ? "bg-white/20 text-white font-medium"
                  : "bg-white/[0.04] text-[#888] hover:text-white"
              }`}
            >
              All ({impact.total_bullets})
            </button>
            <button
              onClick={() => setImpactFilter("xyz")}
              className={`rounded-full px-2.5 py-1 transition-colors cursor-pointer ${
                impactFilter === "xyz"
                  ? "bg-emerald-500/30 text-emerald-300 font-medium border border-emerald-500/40"
                  : "bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20"
              }`}
            >
              ✨ Google XYZ Full ({impact.xyz_count})
            </button>
            <button
              onClick={() => setImpactFilter("missing_metric")}
              className={`rounded-full px-2.5 py-1 transition-colors cursor-pointer ${
                impactFilter === "missing_metric"
                  ? "bg-rose-500/30 text-rose-300 font-medium border border-rose-500/40"
                  : "bg-rose-500/10 text-rose-400 hover:bg-rose-500/20"
              }`}
            >
              ⚠️ Missing Metrics ({impact.total_bullets - impact.quantified_count})
            </button>
            {impact.weak_verb_count > 0 && (
              <button
                onClick={() => setImpactFilter("weak_verb")}
                className={`rounded-full px-2.5 py-1 transition-colors cursor-pointer ${
                  impactFilter === "weak_verb"
                    ? "bg-amber-500/30 text-amber-300 font-medium border border-amber-500/40"
                    : "bg-amber-500/10 text-amber-400 hover:bg-amber-500/20"
                }`}
              >
                ⚠️ Weak Verb ({impact.weak_verb_count})
              </button>
            )}
          </div>

          {/* Bullet List */}
          <div className="max-h-[34rem] space-y-3 overflow-y-auto rounded-[15px] border border-[rgba(255,255,255,0.08)] bg-[#101014] p-4">
            {filteredBullets.length === 0 ? (
              <p className="py-8 text-center text-[13px] text-[#777]">No bullets in this category.</p>
            ) : (
              filteredBullets.map((b, i) => (
                <div
                  key={i}
                  className={`rounded-xl border p-3.5 transition-all ${
                    b.is_xyz
                      ? "border-emerald-500/30 bg-emerald-950/10"
                      : b.is_weak
                      ? "border-amber-500/30 bg-amber-950/10"
                      : "border-rose-500/25 bg-rose-950/10"
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
                      {b.action_verb && (
                        <span className="rounded bg-sky-500/15 border border-sky-500/30 px-2 py-0.5 font-mono text-sky-300">
                          ⚡ Action: {b.action_verb}
                        </span>
                      )}
                      {b.metrics && b.metrics.length > 0 ? (
                        b.metrics.map((m, idx) => (
                          <span
                            key={idx}
                            className="rounded bg-amber-500/15 border border-amber-500/30 px-2 py-0.5 font-mono text-amber-300"
                          >
                            📊 {m}
                          </span>
                        ))
                      ) : (
                        <span className="rounded bg-rose-500/15 border border-rose-500/30 px-2 py-0.5 font-mono text-rose-300">
                          ✕ No Metric
                        </span>
                      )}
                    </div>

                    {b.is_xyz ? (
                      <span className="rounded-full bg-emerald-500/20 border border-emerald-500/40 px-2.5 py-0.5 text-[10.5px] font-semibold text-emerald-300">
                        ✨ Google XYZ Compliant
                      </span>
                    ) : b.is_weak ? (
                      <span className="rounded-full bg-amber-500/20 border border-amber-500/40 px-2.5 py-0.5 text-[10.5px] font-semibold text-amber-300">
                        ⚠️ Passive Opener
                      </span>
                    ) : (
                      <span className="rounded-full bg-rose-500/20 border border-rose-500/40 px-2.5 py-0.5 text-[10.5px] font-semibold text-rose-300">
                        ⚠️ Missing Metric
                      </span>
                    )}
                  </div>

                  <p className="mt-2.5 font-mono text-[12px] leading-relaxed text-[#e4e4e7]">{b.clean}</p>

                  <div
                    className={`mt-2.5 rounded-lg px-3 py-2 text-[11.5px] leading-relaxed ${
                      b.is_xyz
                        ? "bg-emerald-950/30 border border-emerald-500/20 text-emerald-200"
                        : b.is_weak
                        ? "bg-amber-950/30 border border-amber-500/20 text-amber-200"
                        : "bg-rose-950/30 border border-rose-500/20 text-rose-200"
                    }`}
                  >
                    <span className="font-semibold">{b.is_xyz ? "✓ Formula Met: " : "💡 Coaching Tip: "}</span>
                    {b.tip}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      ) : mode === "heatmap" ? (
        <div className="space-y-3">
          {/* Filter Pills */}
          <div className="flex flex-wrap items-center gap-2 text-[11px]">
            <span className="text-[#777]">Filter:</span>
            <button
              onClick={() => setTierFilter("all")}
              className={`rounded-full px-2.5 py-1 transition-colors cursor-pointer ${
                tierFilter === "all" ? "bg-white/20 text-white font-medium" : "bg-white/[0.04] text-[#888] hover:text-white"
              }`}
            >
              All ({counts.all})
            </button>
            <button
              onClick={() => setTierFilter("high")}
              className={`rounded-full px-2.5 py-1 transition-colors cursor-pointer ${
                tierFilter === "high"
                  ? "bg-emerald-500/30 text-emerald-300 font-medium border border-emerald-500/40"
                  : "bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20"
              }`}
            >
              🟢 High Fit ({counts.high})
            </button>
            <button
              onClick={() => setTierFilter("moderate")}
              className={`rounded-full px-2.5 py-1 transition-colors cursor-pointer ${
                tierFilter === "moderate"
                  ? "bg-amber-500/30 text-amber-300 font-medium border border-amber-500/40"
                  : "bg-amber-500/10 text-amber-400 hover:bg-amber-500/20"
              }`}
            >
              🟡 Moderate ({counts.moderate})
            </button>
            <button
              onClick={() => setTierFilter("low")}
              className={`rounded-full px-2.5 py-1 transition-colors cursor-pointer ${
                tierFilter === "low"
                  ? "bg-zinc-700/60 text-zinc-200 font-medium border border-zinc-600"
                  : "bg-zinc-800/40 text-zinc-400 hover:bg-zinc-800"
              }`}
            >
              ⚪ Low Relevance ({counts.low})
            </button>
          </div>

          {/* Heatmap List */}
          <div className="max-h-[34rem] space-y-2 overflow-y-auto rounded-[15px] border border-[rgba(255,255,255,0.08)] bg-[#101014] p-4">
            {filteredHeatmap.length === 0 ? (
              <p className="py-8 text-center text-[13px] text-[#777]">No lines in this category.</p>
            ) : (
              filteredHeatmap.map((row, i) => {
                const isHigh = row.tier === "high";
                const isMod = row.tier === "moderate";
                const isLow = row.tier === "low";

                return (
                  <div
                    key={i}
                    className={`rounded-r-md border-l-2 p-2.5 transition-all ${
                      isHigh
                        ? "border-emerald-400 bg-emerald-500/[0.06]"
                        : isMod
                        ? "border-amber-400/70 bg-amber-500/[0.04]"
                        : isLow
                        ? "border-zinc-700 bg-white/[0.02]"
                        : "border-transparent"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <span className="text-[12.5px] leading-relaxed text-[#dfdfe6]">{row.line}</span>
                      {row.tier !== "neutral" && (
                        <span
                          className={`shrink-0 rounded-full px-2 py-0.5 text-[10.5px] font-medium ${
                            isHigh
                              ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                              : isMod
                              ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                              : "bg-zinc-800 text-zinc-400 border border-zinc-700"
                          }`}
                        >
                          {row.score}% fit
                        </span>
                      )}
                    </div>
                    {row.matched_requirement && (
                      <p className="mt-1 text-[11px] text-[#8a8a94]">
                        <span className="text-[#a1a1aa] font-medium">↳ matches requirement:</span> “{row.matched_requirement}”
                      </p>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      ) : mode === "sections" ? (
        <div className="max-h-[34rem] space-y-1 overflow-y-auto rounded-[15px] border border-[rgba(255,255,255,0.08)] bg-[#101014] p-4">
          {(sectionLines || []).map((row, i) => (
            <div
              key={i}
              className="flex items-start gap-3 rounded-r-md border-l-2 py-1 pl-3 pr-2"
              style={{ borderColor: SECTION_COLORS[row.section] || "#666" }}
            >
              <span
                className="mt-[3px] w-[70px] shrink-0 text-[9.5px] font-semibold uppercase tracking-widest"
                style={{ color: SECTION_COLORS[row.section] || "#666" }}
              >
                {row.section}
              </span>
              <span className="text-[12px] leading-5 text-[#cfcfd6]">{row.line}</span>
            </div>
          ))}
        </div>
      ) : (
        <pre className="max-h-[34rem] overflow-y-auto whitespace-pre-wrap rounded-[15px] border border-[rgba(255,255,255,0.08)] bg-[#101014] p-6 font-mono text-[12.5px] leading-[1.9] text-[#cfcfd6]">
          {text}
        </pre>
      )}
    </div>
  );
}
