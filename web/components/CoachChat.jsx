"use client";

import { useEffect, useRef, useState } from "react";
import { chatWithCoach } from "../lib/api";

const STARTERS = [
  "Why is my skill score low?",
  "How do I add the missing skills quickly?",
  "Rewrite my summary for this job.",
  "What should I fix first?",
];

function CoachMessage({ msg }) {
  if (msg.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-[16px] rounded-br-[4px] bg-white/[0.10] px-3.5 py-2 text-[13px] leading-[1.5] text-[#eee]">
          {msg.content}
        </div>
      </div>
    );
  }
  const m = msg.content; // {available, summary, points, actions, reason}
  return (
    <div className="max-w-[95%] space-y-2.5">
      {!m.available ? (
        <div className="rounded-[14px] border border-[rgba(255,255,255,0.08)] bg-[#151519] px-3.5 py-2.5 text-[12.5px] leading-5 text-[#999]">
          Coach unavailable ({m.reason || "offline"}) — the analysis cards above don't need the LLM.
        </div>
      ) : (
        <div className="rounded-[14px] rounded-bl-[4px] border border-[rgba(255,255,255,0.08)] bg-[#151519] px-3.5 py-3">
          {m.summary && <p className="text-[13px] leading-[1.55] text-[#e8e8ec]">{m.summary}</p>}
          {m.points?.length > 0 && (
            <ul className="mt-2 space-y-1.5">
              {m.points.map((p, i) => (
                <li key={i} className="flex items-start gap-2 text-[12.5px] leading-[1.5] text-[#b9e5d8]">
                  <span className="mt-[7px] h-1 w-1 shrink-0 rounded-full bg-[#2dd4bf]" />{p}
                </li>
              ))}
            </ul>
          )}
          {m.actions?.length > 0 && (
            <div className="mt-2.5 flex flex-wrap gap-1.5 border-t border-[rgba(255,255,255,0.07)] pt-2.5">
              {m.actions.map((a, i) => (
                <span key={i} className="chip border-[#38bdf8]/30 bg-[#38bdf8]/10 text-[#7dd3fc]">→ {a}</span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/** Floating "ask the coach" drawer on the results screen. Grounded in the user's
    analysis + full resume text; answers arrive structured (summary + points + actions). */
export default function CoachChat({ analysis, jdText, resumeText }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]); // {role:'user'|'assistant', content}
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, busy, open]);

  const send = async (text) => {
    const q = (text ?? input).trim();
    if (!q || busy) return;
    setInput("");
    setBusy(true);
    setMessages((m) => [...m, { role: "user", content: q }]);
    try {
      const history = messages.map((m) =>
        m.role === "assistant"
          ? { role: "assistant", content: m.content.summary || "" }
          : { role: "user", content: m.content }
      );
      const reply = await chatWithCoach(q, analysis, jdText, history, resumeText);
      setMessages((m) => [...m, { role: "assistant", content: reply }]);
    } catch (e) {
      setMessages((m) => [...m, { role: "assistant", content: { available: false, reason: e.message } }]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      {/* floating launcher */}
      <button
        onClick={() => setOpen((o) => !o)}
        className="fixed bottom-6 right-6 z-50 flex min-h-[48px] items-center gap-2 rounded-full bg-white px-5 text-[14px] font-medium text-black shadow-[0_8px_30px_rgba(0,0,0,0.5)] transition-transform hover:brightness-95 active:scale-[0.97]">
        {open ? "✕ close" : "💬 Ask the coach"}
      </button>

      {/* drawer */}
      <div
        className={`fixed bottom-20 right-6 z-50 flex max-h-[70vh] w-[min(400px,calc(100vw-3rem))] flex-col overflow-hidden rounded-[20px] border border-[rgba(255,255,255,0.10)] bg-[#0e0e12] shadow-[0_20px_60px_rgba(0,0,0,0.6)] transition-all duration-200 ${
          open ? "pointer-events-auto translate-y-0 opacity-100" : "pointer-events-none translate-y-4 opacity-0"
        }`}>
        <div className="border-b border-[rgba(255,255,255,0.07)] px-4 py-3">
          <p className="text-[13px] font-semibold tracking-[-0.01em]">Resume coach</p>
          <p className="text-[11px] text-[#888]">answers grounded in your analysis · Groq LLM</p>
        </div>

        <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto p-4">
          {messages.length === 0 && (
            <div className="space-y-3">
              <p className="text-[12.5px] leading-5 text-[#999]">
                Ask anything about your results — scores, missing skills, rewrites, strategy.
              </p>
              <div className="flex flex-wrap gap-1.5">
                {STARTERS.map((s) => (
                  <button key={s} onClick={() => send(s)}
                    className="chip border-[rgba(255,255,255,0.12)] bg-white/[0.04] text-[#bbb] hover:bg-white/[0.08]">
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((m, i) => <CoachMessage key={i} msg={m} />)}
          {busy && (
            <div className="flex items-center gap-2 text-[12px] text-[#888]">
              <span className="status-live h-2 w-2 rounded-full bg-[#0099ff]" /> coach is thinking…
            </div>
          )}
        </div>

        <div className="flex items-center gap-2 border-t border-[rgba(255,255,255,0.07)] p-3">
          <input
            className="input !py-2 text-[13px]"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
            placeholder="Ask a follow-up…"
            disabled={busy}
          />
          <button onClick={() => send()} disabled={busy || !input.trim()}
            className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-white text-black transition-transform hover:brightness-95 active:scale-95 disabled:opacity-40">
            ➤
          </button>
        </div>
      </div>
    </>
  );
}
