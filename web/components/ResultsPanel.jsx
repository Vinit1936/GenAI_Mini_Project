"use client";

import { useState } from "react";
import ScoreRing from "./ScoreRing";
import RadarChart from "./RadarChart";
import { buildReport, downloadReport } from "../lib/report";

const SEV = { high: "#fb7185", medium: "#fbbf24", low: "#38bdf8" };

function Block({ title, children, right }) {
  return (
    <div className="card p-6">
      <div className="mb-4 flex items-center justify-between">
        <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-[#888]">{title}</p>
        {right}
      </div>
      {children}
    </div>
  );
}

export default function ResultsPanel({ result }) {
  const b = result.breakdown;
  const [copied, setCopied] = useState(false);
  const [simulatedSkills, setSimulatedSkills] = useState([]);
  const [simulatedSections, setSimulatedSections] = useState([]);

  const matched = b.skill_overlap.matched || [];
  const missing = b.skill_overlap.missing || [];
  const totalSkills = Math.max(1, matched.length + missing.length);

  const activeSimSkills = simulatedSkills.filter((s) => missing.includes(s));
  const simMatchedCount = matched.length + activeSimSkills.length;
  const simCoverage = Math.round((simMatchedCount / totalSkills) * 100);
  const simSkillScore = Math.min(100, Math.round((simMatchedCount / totalSkills) * 100));

  const standardSections = ["experience", "education", "project", "skills"];
  const presentSections = b.section_completeness.present || [];
  const missingSections = standardSections.filter((s) => !presentSections.includes(s));
  const activeSimSections = simulatedSections.filter((s) => missingSections.includes(s));
  const totalPresentCount = presentSections.length + activeSimSections.length;
  const simSectionScore = Math.min(100, Math.round((totalPresentCount / 4) * 100));

  const simOverall = Math.min(
    100,
    Math.round(
      b.semantic_similarity.score * b.semantic_similarity.weight +
      simSkillScore * b.skill_overlap.weight +
      simSectionScore * b.section_completeness.weight +
      b.role_alignment.score * b.role_alignment.weight
    )
  );

  const delta = Math.max(0, Math.round((simOverall - result.overall_score) * 10) / 10);
  const ptsPerSkill = Math.round((100 / totalSkills) * b.skill_overlap.weight * 10) / 10;
  const ptsPerSection = Math.round(25 * b.section_completeness.weight * 10) / 10;

  const activeBreakdown = {
    ...b,
    skill_overlap: {
      ...b.skill_overlap,
      score: simSkillScore,
    },
    section_completeness: {
      ...b.section_completeness,
      score: simSectionScore,
    },
  };

  const diag = result.diagnosis || { working: [], problems: [] };
  const rw = result.rewrites || { available: false, rewrites: [] };

  return (
    <div className="space-y-5">
      {/* ---- ATS score ---- */}
      <div className="card-lg p-7">
        {delta > 0 && (
          <div className="mb-6 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-emerald-500/35 bg-emerald-950/40 px-4 py-2.5 shadow-[0_0_20px_rgba(16,185,129,0.12)]">
            <div className="flex flex-wrap items-center gap-2.5 text-xs text-emerald-200">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <div>
                <span className="font-semibold text-emerald-300">🔮 What-If Simulator Active: </span>
                <span className="text-emerald-200/90">
                  +{activeSimSkills.length} skill{activeSimSkills.length === 1 ? "" : "s"}
                  {activeSimSections.length > 0 ? ` & +${activeSimSections.length} section` : ""}
                </span>
              </div>
              <span className="rounded-md border border-emerald-500/35 bg-emerald-500/20 px-2 py-0.5 font-mono text-[11px] font-bold text-emerald-300">
                +{delta % 1 === 0 ? delta : delta.toFixed(1)} pts → {simOverall}/100
              </span>
            </div>
            <button
              onClick={() => {
                setSimulatedSkills([]);
                setSimulatedSections([]);
              }}
              className="rounded-md border border-white/10 bg-white/5 px-2.5 py-1 text-[11px] font-medium text-zinc-300 hover:bg-white/10 hover:text-white transition-colors cursor-pointer"
            >
              Reset Simulator
            </button>
          </div>
        )}

        <div className="flex flex-col items-center gap-4 lg:flex-row lg:gap-10">
          <div className="flex shrink-0 flex-col items-center">
            <p className="mb-2 text-[11px] font-medium uppercase tracking-[0.16em] text-[#888]">ATS Match Score</p>
            <ScoreRing score={simOverall} size={185} delta={delta} />
          </div>
          <div className="w-full space-y-3 self-stretch border-t border-[rgba(255,255,255,0.07)] pt-5 lg:border-l lg:border-t-0 lg:pl-10 lg:pt-0">
            {Object.entries(activeBreakdown).map(([k, v]) => {
              const origScore = b[k].score;
              const isSim = v.score !== origScore;
              return (
                <div key={k} className="space-y-1">
                  <div className="flex items-center gap-4 text-[13px]">
                    <span className="w-[150px] shrink-0 text-[#999]">{k.replace(/_/g, " ")}</span>
                    <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/[0.07]">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${isSim ? "bg-emerald-400" : "bg-white/60"}`}
                        style={{ width: `${v.score}%` }}
                      />
                    </div>
                    <span className="w-[92px] shrink-0 text-right text-[#bbb]">
                      {isSim ? (
                        <>
                          <span className="text-emerald-400 font-semibold">{v.score}</span>
                          <span className="text-[10px] text-emerald-400/80 ml-0.5">+{v.score - origScore}</span>
                        </>
                      ) : (
                        v.score
                      )}{" "}
                      × {v.weight}
                    </span>
                  </div>
                  {k === "semantic_similarity" && v.attribution && (
                    <div className="flex items-center gap-2 pl-[150px] text-[11px] text-[#888]">
                      <span className="text-emerald-400 font-medium">🟢 {v.attribution.high} high fit</span>·
                      <span className="text-amber-400">🟡 {v.attribution.moderate} moderate</span>·
                      <span className="text-zinc-500">⚪ {v.attribution.low} low</span>
                      <span className="text-[10px] text-[#666] ml-auto">see Heatmap on left</span>
                    </div>
                  )}
                </div>
              );
            })}
            <p className="pt-2 text-[11px] leading-4 text-[#777]">
              weights are fixed and visible — 40% semantic · 30% skills · 15% sections · 15% role
            </p>
          </div>
        </div>
      </div>

      {/* ---- diagnosis ---- */}
      <div className="card p-6">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-[#888]">Diagnosis</p>
            {result.impact_analysis && (
              <span className="rounded-full bg-cyan-500/15 border border-cyan-500/30 px-2 py-0.5 text-[10.5px] font-medium text-cyan-300">
                XYZ Impact: {result.impact_analysis.score}%
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 text-[11px] text-[#777]">
            <span className="text-[#5eead4]">{diag.working.length} working</span>·
            <span className="text-[#fda4af]">{diag.problems.length} to fix</span>
          </div>
        </div>

        {diag.working.length > 0 && (
          <ul className="space-y-2">
            {diag.working.map((w, i) => (
              <li key={i} className="flex items-start gap-2.5 text-[13px] leading-[1.5] text-[#c9e8df]">
                <span className="mt-0.5 grid h-4 w-4 shrink-0 place-items-center rounded-full bg-[#134e4a] text-[9px] text-[#5eead4]">✓</span>
                {w}
              </li>
            ))}
          </ul>
        )}

        {diag.problems.length > 0 && (
          <div className={diag.working.length ? "mt-5 space-y-3 border-t border-[rgba(255,255,255,0.07)] pt-5" : "space-y-3"}>
            {diag.problems.map((p, i) => (
              <div key={i} className="flex items-start gap-3">
                <span className="mt-0.5 h-2 w-2 shrink-0 rounded-full"
                  style={{ background: SEV[p.severity] || "#fbbf24" }} />
                <div className="min-w-0">
                  <p className="text-[13.5px] font-semibold tracking-[-0.01em] text-[#f1f1f4]">{p.title}</p>
                  <p className="mt-0.5 text-[12px] leading-[1.5] text-[#9a9aa3]">{p.detail}</p>
                  <p className="mt-1 text-[12px] leading-[1.5] text-[#8fd4c0]">
                    <span className="text-[#5eead4]">→ fix:</span> {p.fix}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
        {diag.working.length === 0 && diag.problems.length === 0 && (
          <p className="text-[13px] text-[#999]">Nothing flagged — clean bill of health.</p>
        )}
      </div>

      {/* ---- rewrites ---- */}
      <Block
        title="Bullet rewrites · Groq LLM"
        right={
          <div className="flex gap-1">
            <button className="pill-ghost"
              onClick={async () => {
                try { await navigator.clipboard.writeText(buildReport(result)); setCopied(true); setTimeout(() => setCopied(false), 1800); } catch {}
              }}>
              {copied ? "✓ copied" : "copy report"}
            </button>
            <button className="pill-ghost" onClick={() => downloadReport(buildReport(result))}>download .md</button>
          </div>
        }
      >
        {rw.available && rw.rewrites.length > 0 ? (
          <div className="space-y-4">
            {rw.summary && (
              <p className="rounded-[10px] bg-white/[0.04] px-3 py-2 text-[12.5px] italic text-[#bbb]">
                “{rw.summary}”
              </p>
            )}
            {rw.rewrites.map((r, i) => (
              <div key={i} className="space-y-1.5">
                <p className="rounded-[8px] bg-[#1a1a20] px-3 py-1.5 font-mono text-[12px] leading-5 text-[#8a8a94] line-through decoration-[#8a8a94]/50">
                  {r.before}
                </p>
                <p className="rounded-[8px] border-l-2 border-[#2dd4bf] bg-[#0f1f1c] px-3 py-1.5 font-mono text-[12px] leading-5 text-[#d7f5ec]">
                  {r.after}
                </p>
                {r.note && <p className="pl-1 text-[11px] text-[#777]">{r.note}</p>}
              </div>
            ))}
            <p className="text-[11px] text-[#666]">[X%]-style numbers are placeholders — replace with your real metrics.</p>
          </div>
        ) : (
          <p className="text-[13px] leading-6 text-[#777]">
            {rw.reason === "no weak lines worth rewriting"
              ? "No weak bullets found — nothing to rewrite. 🎉"
              : `Rewrites unavailable (${rw.reason || "disabled"}) — the diagnosis above is fully deterministic and works without the LLM.`}
          </p>
        )}
      </Block>

      {/* ---- skills + radar ---- */}
      <div className="grid gap-5 sm:grid-cols-2">
        <Block
          title="Skill coverage"
          right={
            <div className="flex items-center gap-2">
              {activeSimSkills.length > 0 && (
                <span className="rounded-full bg-emerald-500/15 border border-emerald-500/30 px-2 py-0.5 text-[10.5px] font-medium text-emerald-300">
                  +{activeSimSkills.length} simulated
                </span>
              )}
              {b.skill_overlap.semantic_matches?.length > 0 && (
                <span className="rounded-full bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 text-[10.5px] font-medium text-emerald-400">
                  {b.skill_overlap.semantic_matches.length} semantic
                </span>
              )}
              <span className={`text-[12px] ${activeSimSkills.length > 0 ? "text-emerald-400 font-semibold" : "text-[#999]"}`}>
                {simCoverage}%
              </span>
            </div>
          }
        >
          <div className="mb-4 h-2 overflow-hidden rounded-full bg-white/[0.07]">
            <div
              className={`h-full rounded-full transition-all duration-700 ${
                activeSimSkills.length > 0
                  ? "bg-gradient-to-r from-emerald-500 to-teal-400 shadow-[0_0_12px_rgba(52,211,153,0.3)]"
                  : "bg-gradient-to-r from-[#0099ff] to-[#38bdf8]"
              }`}
              style={{ width: `${simCoverage}%` }}
            />
          </div>
          <div className="flex flex-wrap gap-1.5">
            {matched.length === 0 && missing.length === 0 && (
              <span className="text-[13px] text-[#777]">no skills detected — the resume may be too short</span>
            )}
            {/* Exact matches */}
            {(b.skill_overlap.exact_matches || matched).map((s) => (
              <span key={s} className="chip border-[#38bdf8]/30 bg-[#38bdf8]/10 text-[#7dd3fc]" title="Exact keyword match">
                ✓ {s}
              </span>
            ))}
            {/* Semantic synonym matches */}
            {(b.skill_overlap.semantic_matches || []).map((m, idx) => (
              <span
                key={`sem-${idx}`}
                className="chip border-emerald-400/30 bg-emerald-500/10 text-emerald-300"
                title={`Semantic match (${Math.round(m.similarity * 100)}% similarity via MiniLM): JD asks for '${m.jd_skill}', your resume has '${m.resume_skill}'`}
              >
                ≈ {m.jd_skill} <span className="opacity-70 text-[10.5px]">({m.resume_skill})</span>
              </span>
            ))}
            {/* Missing skills (Interactive counterfactual simulation) */}
            {missing.map((s) => {
              const isSimulated = activeSimSkills.includes(s);
              return (
                <button
                  key={s}
                  type="button"
                  onClick={() => {
                    setSimulatedSkills((prev) =>
                      prev.includes(s) ? prev.filter((item) => item !== s) : [...prev, s]
                    );
                  }}
                  className={`chip transition-all duration-200 cursor-pointer ${
                    isSimulated
                      ? "border-emerald-400 bg-emerald-500/20 text-emerald-200 shadow-[0_0_10px_rgba(52,211,153,0.25)] ring-1 ring-emerald-400/50"
                      : "border-[#fb7185]/25 bg-[#fb7185]/10 text-[#fda4af] hover:border-emerald-500/50 hover:bg-emerald-500/10 hover:text-emerald-300"
                  }`}
                  title={
                    isSimulated
                      ? `Click to remove '${s}' from simulation`
                      : `Click to simulate adding '${s}' (+~${ptsPerSkill} pts to ATS score)`
                  }
                >
                  {isSimulated ? `✨ ${s} (+${ptsPerSkill} pts) ✕` : `+ ${s}`}
                </button>
              );
            })}
          </div>
          {missing.length > 0 && (
            <p className="mt-2.5 text-[10.5px] text-[#777] flex items-center gap-1.5">
              <span className="text-[#a1a1aa]">💡 Tip:</span> Click any missing skill above to simulate score impact.
            </p>
          )}
          {b.skill_overlap.semantic_matches?.length > 0 && (
            <p className="mt-2.5 text-[11px] leading-4 text-[#8a8a94] border-t border-white/[0.05] pt-2.5">
              <span className="text-emerald-400 font-medium">⚡ Semantic Match:</span> Synonyms &amp; acronyms are recognized via MiniLM embeddings without strict keyword penalties.
            </p>
          )}
        </Block>

        <Block title="Predicted role & score shape">
          <p className="text-[15px] font-semibold tracking-[-0.01em]">{result.predicted_role.role}
            <span className="ml-2 text-[11px] font-normal text-[#888]">{(result.predicted_role.confidence * 100).toFixed(0)}% conf</span></p>
          <div className="mt-1 flex justify-center">
            <RadarChart breakdown={activeBreakdown} />
          </div>
        </Block>
      </div>

      {/* ---- sections ---- */}
      <Block
        title="Section completeness"
        right={
          <div className="flex items-center gap-2">
            {activeSimSections.length > 0 && (
              <span className="rounded-full bg-emerald-500/15 border border-emerald-500/30 px-2 py-0.5 text-[10.5px] font-medium text-emerald-300">
                +{activeSimSections.length} simulated
              </span>
            )}
            <span className={`text-[12px] ${activeSimSections.length > 0 ? "text-emerald-400 font-semibold" : "text-[#999]"}`}>
              {simSectionScore}/100
            </span>
          </div>
        }
      >
        <div className="flex flex-wrap gap-2">
          {standardSections.map((s) => {
            const present = presentSections.includes(s);
            const isSimulated = activeSimSections.includes(s);
            if (present) {
              return (
                <span key={s} className="chip border-[#2dd4bf]/30 bg-[#2dd4bf]/10 text-[#5eead4]">
                  ✓ {s}
                </span>
              );
            }
            return (
              <button
                key={s}
                type="button"
                onClick={() => {
                  setSimulatedSections((prev) =>
                    prev.includes(s) ? prev.filter((item) => item !== s) : [...prev, s]
                  );
                }}
                className={`chip transition-all duration-200 cursor-pointer ${
                  isSimulated
                    ? "border-emerald-400 bg-emerald-500/20 text-emerald-200 shadow-[0_0_10px_rgba(52,211,153,0.25)] ring-1 ring-emerald-400/50"
                    : "border-[#fb7185]/25 bg-[#fb7185]/10 text-[#fda4af] line-through hover:no-underline hover:border-emerald-500/50 hover:bg-emerald-500/10 hover:text-emerald-300"
                }`}
                title={
                  isSimulated
                    ? `Click to remove '${s}' section from simulation`
                    : `Click to simulate adding '${s}' section (+~${ptsPerSection} pts to ATS score)`
                }
              >
                {isSimulated ? `✨ ${s} (+${ptsPerSection} pts) ✕` : `✕ ${s}`}
              </button>
            );
          })}
        </div>
        <p className="mt-4 text-[11px] leading-5 text-[#777]">
          line counts —{" "}
          {Object.entries(result.sections.line_counts).map(([k, v]) => (
            <span key={k} className="mr-2.5">{k} <span className="text-[#aaa]">{v}</span></span>
          ))}
        </p>
        <p className="mt-3 text-[11px] leading-4 text-[#777]">
          ⛨ privacy: {result.privacy.names_stripped} name(s) stripped before scoring
        </p>
      </Block>
    </div>
  );
}
