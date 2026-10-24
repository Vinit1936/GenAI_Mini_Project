"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { extractResume } from "../lib/api";
import { saveResume, savePdf } from "../lib/flow";
import GradientASCII from "../components/GradientASCII";

const STATS = [
  ["4", "self-trained models"],
  ["24", "roles recognised"],
  ["11", "entity types detected"],
  ["0", "names used in scoring"],
];

const FEATURES = [
  {
    title: "ATS Match Score",
    body: "One 0–100 number, broken open: 40% semantic fit, 30% skill coverage, 15% section completeness, 15% role alignment — every weight visible.",
    icon: "◎",
  },
  {
    title: "Skill gap analysis",
    body: "See exactly which skills the job description asks for that your resume is missing — and which ones already hit.",
    icon: "✦",
  },
  {
    title: "Section completeness",
    body: "A BiLSTM reads your resume line by line and checks that experience, education, projects and skills sections all exist.",
    icon: "☰",
  },
  {
    title: "Privacy-first scoring",
    body: "Names, emails, phone numbers and gendered words are detected and stripped before any score is computed. Credentials never tip the scales.",
    icon: "⛨",
  },
];

export default function Landing() {
  const router = useRouter();
  const fileRef = useRef(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const takeFile = async (file) => {
    if (!file) return;
    setBusy(true); setError("");
    try {
      const out = await extractResume(file);
      await savePdf(file);
      saveResume(out.text, file.name);
      router.push("/analyse");
    } catch (e) {
      setError(e.message);
      setBusy(false);
    }
  };

  return (
    <div className="relative w-full bg-[#0b0b0e]">
      {/* ================= HERO — GRADIENT ASCII HORIZON ================= */}
      <section
        id="hero"
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          takeFile(e.dataTransfer.files?.[0]);
        }}
        className="relative flex h-screen min-h-[680px] w-full flex-col justify-end overflow-hidden"
      >
        {/* Full-bleed GradientASCII Canvas */}
        <div className="absolute inset-0 z-0">
          <GradientASCII
            colors={["#060d2e", "#0e227a", "#1e40e6", "#00a2ff", "#70e0ff"]}
            shape="horizon"
            characters=" =+xX0S8#@"
            cellSize={18}
            density={0.88}
            glyphOpacity={0.95}
            glow={0.35}
            speed={0.7}
            gradientOpacity={0.04}
            mouseInteraction={true}
            clickEffect="wave"
            fontFamily='"Geist Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace'
          />
        </div>

        {/* Soft natural floor gradient for seamless transition to content below */}
        <div className="pointer-events-none absolute inset-x-0 bottom-0 z-[1] h-40 bg-gradient-to-t from-[#0b0b0e] via-[#0b0b0e]/75 to-transparent" />

        {/* Bottom-left Content with ResumeLens Copy & Action Buttons */}
        <div className="relative z-10 max-w-3xl px-6 pb-16 md:px-14 md:pb-24 text-left">
          <h1 className="text-4xl font-medium tracking-[-0.035em] leading-[1.08] text-white drop-shadow-[0_4px_24px_rgba(0,0,0,0.9)] sm:text-6xl md:text-[68px]">
            Know exactly how
            <br />
            your resume scores.
          </h1>

          <p className="mt-6 max-w-xl text-[16px] font-light leading-[1.5] text-[#b4b4bd] drop-shadow-[0_2px_12px_rgba(0,0,0,0.9)] tracking-[-0.01em] sm:text-[18px]">
            Upload your resume, pick a target role, and get an ATS-grade match score with an X-ray of every entity our models find — skills, companies, degrees and more.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-3">
            <button
              onClick={() => fileRef.current?.click()}
              disabled={busy}
              className="inline-flex items-center justify-center gap-1.5 rounded-full bg-white px-7 py-3 text-[14.5px] font-medium text-black transition-all hover:bg-white/90 active:scale-[0.98] shadow-lg shadow-black/30"
            >
              {busy ? "Extracting text…" : "Upload your resume >"}
            </button>

            <a
              href="/analyse"
              className="inline-flex items-center justify-center gap-2 rounded-full border border-white/20 bg-[#151519]/80 px-7 py-3 text-[14.5px] font-normal text-white transition-all hover:bg-[#1e1e24] hover:border-white/30 backdrop-blur-sm"
            >
              or paste text instead
            </a>

            <input
              ref={fileRef}
              type="file"
              accept=".pdf,.docx,.txt"
              className="hidden"
              onChange={(e) => {
                takeFile(e.target.files?.[0]);
                e.target.value = "";
              }}
            />
          </div>

          {error && (
            <p className="mt-4 max-w-md rounded-[12px] border border-red-400/20 bg-red-400/10 px-4 py-2.5 text-[13px] text-red-300">
              {error} — try another file, or paste text in the analysis flow.
            </p>
          )}
        </div>
      </section>

      {/* ================= STATS STRIP ================= */}
      <section className="relative z-10 mx-auto max-w-[1199px] px-5 pt-8">
        <div className="grid grid-cols-2 gap-px overflow-hidden rounded-[20px] border border-[rgba(255,255,255,0.07)] bg-[rgba(255,255,255,0.07)] md:grid-cols-4">
          {STATS.map(([n, label]) => (
            <div key={label} className="bg-[#0b0b0e] px-6 py-7 text-center">
              <p className="text-[34px] font-semibold tracking-[-0.03em]">{n}</p>
              <p className="mt-1 text-[12px] text-[#999]">{label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ================= FEATURES & COMPONENTS ================= */}
      <section id="features" className="relative z-10 mx-auto max-w-[1199px] px-5 py-24">
        <h2 className="display-lg max-w-2xl">Everything the score is made of.</h2>
        <p className="subhead mt-4 max-w-xl">No black box. Every number traces back to a model you can inspect on the model card.</p>

        <div className="mt-12 grid gap-5 md:grid-cols-3">
          {/* Spotlight: X-ray */}
          <div className="spotlight spotlight-magenta md:row-span-2">
            <p className="text-[13px] font-medium uppercase tracking-wider opacity-80">Signature feature</p>
            <h3 className="display-md mt-3">Resume X-ray</h3>
            <p className="mt-3 text-[15px] leading-relaxed opacity-90">
              Your resume comes back annotated like a recruiter marked it up — hand-drawn
              circles around companies, highlights over skills, degrees and names — with a
              per-line section map drawn by a bidirectional LSTM.
            </p>
            <div className="mt-8 flex items-center gap-2 opacity-90">
              <span className="chip border-white/30 bg-white/15">NER · DistilBERT</span>
              <span className="chip border-white/30 bg-white/15">sections · BiLSTM</span>
            </div>
            <div className="mt-8 select-none font-mono text-[12px] leading-6 opacity-75">
              <p><span className="rounded bg-white/25 px-1">Maria Rodriguez</span> — Data Scientist</p>
              <p>worked at <span className="rounded-full border border-white/60 px-2">FinTech Labs</span> building</p>
              <p><span className="rounded bg-white/25 px-1">PyTorch</span> <span className="rounded bg-white/25 px-1">Docker</span> <span className="rounded bg-white/25 px-1">AWS</span> models…</p>
            </div>
          </div>

          {FEATURES.map((f) => (
            <div key={f.title} className="card p-7 transition-colors hover:border-white/[0.14]">
              <span className="grid h-10 w-10 place-items-center rounded-full bg-[#1c1c22] text-[15px]">{f.icon}</span>
              <h3 className="mt-5 text-[17px] font-semibold tracking-[-0.015em]">{f.title}</h3>
              <p className="mt-2 text-[14px] leading-[1.55] text-[#999]">{f.body}</p>
            </div>
          ))}

          {/* Spotlight: AI suggestions */}
          <div className="spotlight spotlight-orange">
            <p className="text-[13px] font-medium uppercase tracking-wider opacity-80">Groq LLM</p>
            <h3 className="display-md mt-3">Fix-it suggestions</h3>
            <p className="mt-3 text-[15px] leading-relaxed opacity-90">
              A language model reads the analysis — matched skills, gaps, missing sections —
              and returns concrete rewrites you can make tonight.
            </p>
          </div>
        </div>
      </section>

      {/* ================= HOW IT WORKS ================= */}
      <section id="how" className="relative z-10 mx-auto max-w-[1199px] px-5 py-24">
        <h2 className="display-lg">Three steps. One score.</h2>
        <div className="mt-12 grid gap-5 md:grid-cols-3">
          {[
            ["01", "Upload your resume", "PDF, DOCX or plain text. We extract the text on your behalf — scanned-image PDFs get a friendly nudge to paste instead."],
            ["02", "Pick the target job", "Choose one of six preset role descriptions or paste your own from any job board."],
            ["03", "Read the X-ray", "Match score, skill gaps, section checks and hand-drawn annotations — in about ten seconds."],
          ].map(([n, title, body]) => (
            <div key={n} className="card p-7">
              <p className="text-[13px] font-medium text-[#0099ff]">{n}</p>
              <h3 className="mt-3 text-[17px] font-semibold tracking-[-0.015em]">{title}</h3>
              <p className="mt-2 text-[14px] leading-[1.55] text-[#999]">{body}</p>
            </div>
          ))}
        </div>

        {/* Final CTA band */}
        <div className="spotlight spotlight-violet mt-16 flex flex-col items-center gap-6 py-14 text-center md:flex-row md:justify-between md:text-left">
          <div>
            <h3 className="display-md">Ready to see your score?</h3>
            <p className="mt-2 text-[15px] opacity-85">It takes one file and ten seconds.</p>
          </div>
          <a className="pill-primary !px-8" href="/analyse">Analyse my resume →</a>
        </div>
      </section>
    </div>
  );
}
