export const ML_API = process.env.NEXT_PUBLIC_ML_API || "http://localhost:8000";

export async function analyze(resume_text, job_description, want_suggestions = true, target_role = null) {
  const res = await fetch(`${ML_API}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resume_text, job_description, want_suggestions, target_role }),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Analysis failed (${res.status}): ${detail.slice(0, 200)}`);
  }
  return res.json();
}

export async function extractResume(file) {
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch(`${ML_API}/extract`, { method: "POST", body: fd });
  if (!res.ok) {
    const detail = await res.text();
    let msg = `Extraction failed (${res.status})`;
    try { msg = JSON.parse(detail).detail || msg; } catch {}
    throw new Error(msg);
  }
  return res.json();
}

export async function chatWithCoach(question, analysis, jdText = "", history = [], resumeText = "") {
  const res = await fetch(`${ML_API}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, analysis, jd_text: jdText, history, resume_text: resumeText }),
  });
  if (!res.ok) throw new Error(`Coach chat failed (${res.status})`);
  return res.json();
}

export async function fetchPerformance() {
  const res = await fetch(`${ML_API}/models/performance`);
  if (!res.ok) throw new Error(`ML service unreachable (${res.status})`);
  return res.json();
}

export function plotUrl(model, name) {
  return `${ML_API}/models/plots/${model}/${name}`;
}
