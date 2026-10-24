"use client";

import { useState } from "react";

const SECTION_COLORS = { experience: "#38bdf8", education: "#a78bfa", skills: "#f97316", project: "#fbbf24", other: "#666" };

/** Text-mode preview (pasted / DOCX flows): plain text, optional per-line section map. */
export default function ResumeXray({ text, sectionLines }) {
  const [mode, setMode] = useState("preview");

  return (
    <div>
      <div className="mb-4 flex items-center justify-between gap-3">
        <div className="flex rounded-full border border-[rgba(255,255,255,0.1)] bg-[#151519] p-0.5 text-[12px] font-medium">
          {[["preview", "Preview"], ["sections", "Section map"]].map(([v, label]) => (
            <button key={v} onClick={() => setMode(v)}
              className={`rounded-full px-3.5 py-1.5 transition-colors ${
                mode === v ? "bg-[#1c1c22] text-white" : "text-[#888] hover:text-white"}`}>
              {label}
            </button>
          ))}
        </div>
        <span className="text-[11px] text-[#777]">sections labelled by the BiLSTM</span>
      </div>

      {mode === "sections" ? (
        <div className="max-h-[34rem] space-y-1 overflow-y-auto rounded-[15px] border border-[rgba(255,255,255,0.08)] bg-[#101014] p-4">
          {(sectionLines || []).map((row, i) => (
            <div key={i} className="flex items-start gap-3 rounded-r-md border-l-2 py-1 pl-3 pr-2"
              style={{ borderColor: SECTION_COLORS[row.section] || "#666" }}>
              <span className="mt-[3px] w-[70px] shrink-0 text-[9.5px] font-semibold uppercase tracking-widest"
                style={{ color: SECTION_COLORS[row.section] || "#666" }}>{row.section}</span>
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
