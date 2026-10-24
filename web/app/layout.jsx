import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import "./globals.css";

export const metadata = {
  title: "ResumeLens — See Exactly How Your Resume Scores",
  description:
    "ATS resume analysis powered by 4 self-trained ML models. DistilBERT role & NER, BiLSTM section classification, MiniLM similarity and Groq LLM advice.",
};

function Logo() {
  return (
    <a href="/" className="flex items-center gap-2.5 hover:opacity-90 transition">
      <span className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-tr from-[#0099ff]/30 to-[#38bdf8]/10 border border-[#0099ff]/30 text-[#38bdf8]">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="7" />
          <path d="m21 21-4.3-4.3" />
          <circle cx="11" cy="11" r="2.5" fill="currentColor" fillOpacity="0.4" />
        </svg>
      </span>
      <span className="text-[17px] font-semibold tracking-[-0.015em] text-white">ResumeLens</span>
    </a>
  );
}

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`${GeistSans.variable} ${GeistMono.variable}`}>
      <body className="flex min-h-screen flex-col bg-[#0b0b0e] text-white">
        {/* Floating transparent navigation bar */}
        <header className="fixed top-0 inset-x-0 z-50 bg-transparent">
          <div className="mx-auto flex h-20 max-w-[1340px] items-center justify-between px-6 md:px-14">
            <Logo />
            <nav className="hidden items-center gap-8 text-[14px] text-[#a1a1aa] md:flex">
              <a className="hover:text-white transition-colors" href="/#features">Features</a>
              <a className="hover:text-white transition-colors" href="/#how">How it works</a>
              <a className="hover:text-white transition-colors" href="/performance">Model card</a>
            </nav>
            <div className="flex items-center gap-3">
              <a
                className="rounded-full bg-white px-5 py-2 text-[14px] font-medium text-black transition-all hover:bg-white/90 active:scale-[0.98] shadow-sm"
                href="/analyse"
              >
                Upload resume
              </a>
            </div>
          </div>
        </header>

        <main className="flex-1">{children}</main>

        <footer className="border-t border-[rgba(255,255,255,0.06)] bg-[#0b0b0e]">
          <div className="mx-auto flex max-w-[1199px] flex-col gap-6 px-5 py-12 md:flex-row md:items-start md:justify-between">
            <div className="max-w-xs">
              <Logo />
              <p className="mt-4 text-[13px] leading-5 text-[#999]">
                Resume ↔ job-description match analysis powered by 4 self-trained ML models + MiniLM sentence embeddings + Groq LLM.
              </p>
            </div>
            <div className="flex gap-16 text-[13px]">
              <div className="space-y-2.5 text-[#999]">
                <p className="mb-3 text-white">Product</p>
                <a className="block hover:text-white transition-colors" href="/#features">Features</a>
                <a className="block hover:text-white transition-colors" href="/#how">How it works</a>
                <a className="block hover:text-white transition-colors" href="/analyse">Analyse a resume</a>
              </div>
              <div className="space-y-2.5 text-[#999]">
                <p className="mb-3 text-white">Project</p>
                <a className="block hover:text-white transition-colors" href="/performance">Model card</a>
                <a className="block hover:text-white transition-colors" href="https://console.groq.com" target="_blank" rel="noreferrer">Powered by Groq LLM</a>
              </div>
            </div>
          </div>
          <div className="border-t border-[rgba(255,255,255,0.04)] py-5 text-center text-[12px] text-[#666]">
            ResumeLens · GenAI Mini Project · 4 Self-Trained ML Models
          </div>
        </footer>
      </body>
    </html>
  );
}
