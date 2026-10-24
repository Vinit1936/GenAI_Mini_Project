/** Build a markdown report from an /analyze result + download/copy helpers (client-side). */

export function buildReport(result, jdExcerpt = "") {
  const b = result.breakdown;
  const lines = [
    `# ResumeLens Analysis Report`,
    ``,
    `**Overall match score: ${result.overall_score}/100**`,
    `**Predicted role:** ${result.predicted_role.role} (${(result.predicted_role.confidence * 100).toFixed(1)}% confidence)`,
    `**Generated:** ${new Date().toLocaleString()}`,
    ``,
    `## Score breakdown`,
    ``,
    `| Component | Score | Weight |`,
    `|---|---|---|`,
    ...Object.entries(b).map(
      ([k, v]) => `| ${k.replace(/_/g, " ")} | ${v.score} | ${Math.round(v.weight * 100)}% |`
    ),
    ``,
    `## Skills`,
    ``,
    `- Matched: ${b.skill_overlap.matched.join(", ") || "none"}`,
    ...(b.skill_overlap.semantic_matches?.length
      ? [`- Semantic matches: ${b.skill_overlap.semantic_matches.map((m) => `${m.jd_skill} ≈ ${m.resume_skill} (${Math.round(m.similarity * 100)}%)`).join(", ")}`]
      : []),
    `- Missing: ${b.skill_overlap.missing.join(", ") || "none"}`,
    ``,
    `## Sections`,
    ``,
    `- Present: ${b.section_completeness.present.join(", ") || "none"}`,
    `- Missing: ${b.section_completeness.missing.join(", ") || "none"}`,
    ``,
  ];
  if (result.diagnosis?.problems?.length) {
    lines.push(`## What to fix`, ``);
    for (const p of result.diagnosis.problems) {
      lines.push(`- **[${p.severity}] ${p.title}** — ${p.detail}`, `  → fix: ${p.fix}`);
    }
    lines.push(``);
  }
  if (result.diagnosis?.working?.length) {
    lines.push(`## What's working`, ``, ...result.diagnosis.working.map((w) => `- ${w}`), ``);
  }
  if (result.rewrites?.available && result.rewrites.rewrites?.length) {
    lines.push(`## Bullet rewrites (LLM)`, ``);
    if (result.rewrites.summary) lines.push(`> ${result.rewrites.summary}`, ``);
    for (const r of result.rewrites.rewrites) {
      lines.push(`- ~~${r.before}~~`, `  → **${r.after}**`);
    }
    lines.push(``);
  }
  lines.push(
    `## Privacy`,
    ``,
    `${result.privacy.names_stripped} name(s) detected and stripped before scoring. ` +
      `Names, emails, phone numbers and gendered words never influence the score.`,
    ``
  );
  return lines.join("\n");
}

export function downloadReport(md) {
  const blob = new Blob([md], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `resumelens-report-${new Date().toISOString().slice(0, 10)}.md`;
  a.click();
  URL.revokeObjectURL(url);
}
