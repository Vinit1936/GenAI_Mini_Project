"use client";

import { useEffect, useRef, useState } from "react";
import { analyze, extractResume } from "../../lib/api";
import { loadResume, loadPdf, saveResume, savePdf, clearResume } from "../../lib/flow";
import { PRESET_ROLES } from "../../lib/presets";
import Analyzing from "../../components/Analyzing";
import ResumeXray from "../../components/ResumeXray";
import PdfXray from "../../components/PdfXray";
import ResultsPanel from "../../components/ResultsPanel";
import CoachChat from "../../components/CoachChat";

const MIN_SPIN_MS = 4200; // let the scanning animation breathe even if the API is fast

export default function AnalyseFlow() {
  const [step, setStep] = useState("resume"); // resume | jd | analyzing | results
  const [resume, setResume] = useState("");
  const [resumeName, setResumeName] = useState("");
  const [jdChoice, setJdChoice] = useState(null);   // preset id or "custom"
  const [customJd, setCustomJd] = useState("");
  const [result, setResult] = useState(null);
  const [pdfFile, setPdfFile] = useState(null);   // original File, when a PDF was uploaded
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const fileRef = useRef(null);

  const jdText = jdChoice === "custom" ? customJd : (PRESET_ROLES.find((r) => r.id === jdChoice)?.jd || "");

  useEffect(() => {
    const saved = loadResume();
    if (saved.text) {
      setResume(saved.text);
      setResumeName(saved.name);
      setPdfFile(loadPdf());
      setStep("jd");
    }
  }, []);

  const takeFile = async (file) => {
    if (!file) return;
    setBusy(true); setError("");
    try {
      const out = await extractResume(file);
      setResume(out.text);
      setResumeName(file.name);
      saveResume(out.text, file.name);
      const isPdf = await savePdf(file);
      setPdfFile(isPdf ? file : null);
      setStep("jd");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  /** Demo path: use the bundled sample PDF exactly like a real upload. */
  const useSamplePdf = async () => {
    setBusy(true); setError("");
    try {
      const res = await fetch("/sample-resume.pdf");
      const blob = await res.blob();
      await takeFile(new File([blob], "sample-resume.pdf", { type: "application/pdf" }));
    } catch (e) {
      setError("couldn't load the sample PDF: " + e.message);
    } finally {
      setBusy(false);
    }
  };

  const runAnalysis = async () => {
    if (jdText.trim().length < 20) return;
    setStep("analyzing");
    setError("");
    const t0 = Date.now();
    try {
      const target = jdChoice === "custom" ? null : PRESET_ROLES.find((r) => r.id === jdChoice)?.title;
      const r = await analyze(resume, jdText, true, target);
      const wait = Math.max(0, MIN_SPIN_MS - (Date.now() - t0));
      setTimeout(() => { setResult(r); setStep("results"); }, wait);
    } catch (e) {
      setError(e.message + " — is the analysis engine running on port 8000?");
      setStep("jd");
    }
  };

  const restart = () => {
    clearResume();
    setResume(""); setResumeName(""); setJdChoice(null); setCustomJd("");
    setResult(null); setPdfFile(null); setStep("resume");
  };

  /* ---------------- STEP 1 · resume ---------------- */
  if (step === "resume") {
    return (
      <div className="mx-auto max-w-xl px-5 py-24">
        <h1 className="display-lg">Add your resume.</h1>
        <p className="subhead mt-3">Upload a file, or paste the text — whatever's faster.</p>
        <label
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => { e.preventDefault(); takeFile(e.dataTransfer.files?.[0]); }}
          className="mt-10 flex cursor-pointer flex-col items-center justify-center gap-3 rounded-[30px] border border-dashed border-[rgba(255,255,255,0.16)] bg-[#101014] py-16 transition-colors hover:border-[#0099ff]/50"
        >
          <span className="text-[15px] text-[#aaa]">{busy ? "Extracting text…" : "Drop your resume here, or"}</span>
          <span className="pill-primary">{busy ? "…" : "⬆  Choose a file"}</span>
          <span className="text-[12px] text-[#666]">PDF · DOCX · TXT</span>
          <input ref={fileRef} type="file" accept=".pdf,.docx,.txt" className="hidden"
            onChange={(e) => { takeFile(e.target.files?.[0]); e.target.value = ""; }} />
        </label>
        {error && <p className="mt-4 rounded-[12px] border border-red-400/20 bg-red-400/10 px-4 py-2.5 text-[13px] text-red-300">{error}</p>}
        <div className="mt-6 flex items-center gap-3 text-[13px] text-[#888]">
          <span>no resume handy?</span>
          <button className="pill-ghost !text-[#7cc7ff]" onClick={useSamplePdf} disabled={busy}>
            ✨ try the sample PDF
          </button>
        </div>

        <div className="mt-8">
          <p className="mb-2 text-[12px] uppercase tracking-widest text-[#777]">or paste text</p>
          <textarea className="input-area" rows={8} value={resume}
            onChange={(e) => setResume(e.target.value)}
            placeholder="Paste your full resume text…" />
          <button className="pill-primary mt-4 w-full sm:w-auto"
            disabled={resume.trim().length < 50}
            onClick={() => { saveResume(resume, "pasted"); setStep("jd"); }}>
            Continue →
          </button>
        </div>
      </div>
    );
  }

  /* ---------------- STEP 2 · job description ---------------- */
  if (step === "jd") {
    return (
      <div className="mx-auto max-w-3xl px-5 py-20">
        <div className="flex items-center gap-2 text-[12px] text-[#777]">
          <span className="rounded-full bg-white/[0.06] px-2.5 py-1">✓ resume{resumeName ? ` · ${resumeName}` : ""}</span>
          <span>→</span>
          <span className="rounded-full border border-[#0099ff]/40 px-2.5 py-1 text-[#7cc7ff]">target job</span>
        </div>
        <h1 className="display-lg mt-6">Which job are you aiming at?</h1>
        <p className="subhead mt-3">Pick a preset role — or paste the real job description for sharper scoring.</p>

        <div className="mt-10 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {PRESET_ROLES.map((r) => {
            const selected = jdChoice === r.id;
            return (
              <button key={r.id} onClick={() => setJdChoice(r.id)}
                className={`rounded-[20px] border p-5 text-left transition-all ${
                  selected
                    ? "border-[#0099ff] bg-[#0099ff]/[0.08] shadow-[0_0_0_1px_rgba(0,153,255,0.35)]"
                    : "border-[rgba(255,255,255,0.08)] bg-[#151519] hover:border-white/[0.16]"
                }`}>
                <span className="text-xl">{r.emoji}</span>
                <p className="mt-2 text-[15px] font-semibold tracking-[-0.01em]">{r.title}</p>
                <p className="mt-1 line-clamp-2 text-[12px] leading-4 text-[#888]">preset job description included</p>
              </button>
            );
          })}
        </div>

        <div className={`mt-6 rounded-[20px] border p-5 transition-colors ${
          jdChoice === "custom" ? "border-[#0099ff] bg-[#0099ff]/[0.06]" : "border-[rgba(255,255,255,0.08)] bg-[#151519]"
        }`}>
          <button className="flex w-full items-center justify-between text-left"
            onClick={() => setJdChoice(jdChoice === "custom" ? null : "custom")}>
            <span>
              <span className="text-[15px] font-semibold tracking-[-0.01em]">📋 Have the actual job description?</span>
              <span className="mt-1 block text-[12px] text-[#888]">Paste it for the most accurate score</span>
            </span>
            <span className={`grid h-6 w-6 place-items-center rounded-full border text-[11px] ${
              jdChoice === "custom" ? "border-transparent bg-[#0099ff] text-black" : "border-white/20 text-[#888]"
            }`}>{jdChoice === "custom" ? "✓" : "+"}</span>
          </button>
          {jdChoice === "custom" && (
            <textarea className="input-area mt-4" rows={7} value={customJd}
              onChange={(e) => setCustomJd(e.target.value)}
              placeholder="Paste the job description from any job board…" />
          )}
        </div>

        {error && <p className="mt-6 rounded-[12px] border border-red-400/20 bg-red-400/10 px-4 py-2.5 text-[13px] text-red-300">{error}</p>}

        <div className="mt-8 flex items-center gap-3">
          <button className="pill-primary !px-8" disabled={jdText.trim().length < 20 || busy} onClick={runAnalysis}>
            Analyse my resume →
          </button>
          <button className="pill-ghost" onClick={restart}>use a different resume</button>
        </div>
      </div>
    );
  }

  /* ---------------- STEP 3 · analyzing ---------------- */
  if (step === "analyzing") {
    return (
      <div className="mx-auto max-w-3xl px-5">
        <Analyzing done={false} error={error} />
      </div>
    );
  }

  /* ---------------- STEP 4 · results ---------------- */
  return (
    <div className="mx-auto max-w-[1440px] px-5 pt-24 pb-12">
      <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="display-md">Your analysis</h1>
          <p className="mt-1.5 text-[13px] text-[#888]">
            {resumeName ? resumeName : "pasted resume"} ·{" "}
            {jdChoice === "custom" ? "custom job description" : PRESET_ROLES.find((r) => r.id === jdChoice)?.title}
          </p>
        </div>
        <button className="pill-secondary" onClick={restart}>＋ New analysis</button>
      </div>

      <div className="grid gap-6 lg:grid-cols-[2fr_3fr]">
        <div className="lg:sticky lg:top-20 lg:self-start">
          <p className="mb-4 text-[11px] font-medium uppercase tracking-[0.14em] text-[#888]">Resume X-ray</p>
          {pdfFile ? (
            <PdfXray file={pdfFile} entities={result.entities} />
          ) : (
            <ResumeXray text={resume} entities={result.entities} sectionLines={result.section_lines} />
          )}
        </div>
        <ResultsPanel result={result} />
      </div>

      <CoachChat analysis={result} jdText={jdText} resumeText={resume} />
    </div>
  );
}
