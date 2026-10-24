"use client";

import { useEffect, useState } from "react";
import { fetchPerformance, plotUrl } from "../../lib/api";
import StatusDot from "../../components/StatusDot";

function Metric({ value, label, accent = "text-zinc-100" }) {
  return (
    <div className="text-center">
      <p className={`text-2xl font-semibold ${accent}`}>{value}</p>
      <p className="mt-0.5 text-[11px] text-zinc-500">{label}</p>
    </div>
  );
}

function Card({ title, sub, children }) {
  return (
    <div className="card animate-fade-up p-6">
      <p className="label">{title}</p>
      {sub && <p className="mt-1 text-[11px] text-zinc-600">{sub}</p>}
      <div className="mt-4">{children}</div>
    </div>
  );
}

export default function Performance() {
  const [perf, setPerf] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchPerformance().then(setPerf).catch((e) => setError(e.message));
  }, []);

  if (error)
    return (
      <div className="rounded-xl border border-red-400/25 bg-red-400/10 p-4 text-sm text-red-300">
        {error} — start the ML engine first: <code>uvicorn app.main:app --port 8000</code>
      </div>
    );
  if (!perf) return <p className="text-sm text-zinc-600">loading model metrics…</p>;

  const { role_classifier: role, resume_ner: ner, section_classifier: sec } = perf;

  return (
    <div className="mx-auto max-w-[1199px] px-5 pt-28 pb-16 space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Model Performance</h1>
          <p className="mt-1 text-sm text-zinc-500">
            Every number below comes from training runs I did myself — nothing pretrained-as-a-service.
          </p>
        </div>
        <StatusDot />
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card title="Role classifier" sub={`DistilBERT fine-tune vs TF-IDF+LogReg · ${role.n_train}/${role.n_test} split · ${role.n_classes} classes`}>
          <div className="space-y-3">
            {[
              ["TF-IDF + LogReg", role.baseline.accuracy, role.baseline.macro_f1, false],
              ["DistilBERT (fine-tuned)", role.distilbert.accuracy, role.distilbert.macro_f1, true],
            ].map(([name, acc, f1, star]) => (
              <div key={name}>
                <div className="mb-1 flex justify-between text-xs">
                  <span className={star ? "font-medium text-emerald-300" : "text-zinc-400"}>{name}</span>
                  <span className="text-zinc-500">{(acc * 100).toFixed(1)}% acc · {(f1 * 100).toFixed(1)}% F1</span>
                </div>
                <div className="flex h-1.5 gap-1 overflow-hidden rounded-full bg-white/[0.06]">
                  <div className={star ? "h-full bg-emerald-400" : "h-full bg-zinc-600"} style={{ width: `${acc * 100}%` }} />
                </div>
              </div>
            ))}
            <p className="pt-1 text-[11px] text-zinc-600">macro-F1 = unweighted per-class average, punishes ignored minority classes</p>
          </div>
        </Card>

        <Card title="Resume NER" sub={`DistilBERT token classification · seqeval entity-level · ${ner.n_train_resumes}/${ner.n_test_resumes} resumes`}>
          <div className="grid grid-cols-3 divide-x divide-white/[0.06]">
            <Metric value={`${(ner.precision * 100).toFixed(1)}%`} label="precision" />
            <Metric value={`${(ner.recall * 100).toFixed(1)}%`} label="recall" />
            <Metric value={`${(ner.f1 * 100).toFixed(1)}%`} label="entity F1" accent="text-emerald-300" />
          </div>
        </Card>

        <Card title="Section classifier" sub={`2-layer BiLSTM + trained word embeddings · class-weighted loss · ${sec.n_train.toLocaleString()}/${sec.n_test.toLocaleString()} lines`}>
          <div className="grid grid-cols-2 divide-x divide-white/[0.06]">
            <Metric value={`${(sec.accuracy * 100).toFixed(1)}%`} label="accuracy" />
            <Metric value={`${(sec.macro_f1 * 100).toFixed(1)}%`} label="macro-F1" accent="text-emerald-300" />
          </div>
          <p className="mt-3 text-center text-[11px] text-zinc-600">vocabulary: {sec.vocab_size.toLocaleString()} words</p>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {[
          ["role_classifier", "cm_distilbert.png", "Role classifier — confusion matrix (DistilBERT)"],
          ["section_classifier", "cm_bilstm.png", "Section classifier — confusion matrix (BiLSTM)"],
          ["role_classifier", "class_distribution.png", "Role dataset — 24 balanced classes"],
          ["resume_ner", "entity_distribution.png", "NER dataset — entity type imbalance"],
        ].map(([model, file, caption]) => (
          <figure key={file} className="card overflow-hidden p-3">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img className="w-full rounded-lg border border-white/[0.06] bg-white" src={plotUrl(model, file)} alt={caption} />
            <figcaption className="px-1 pt-2 text-[11px] text-zinc-500">{caption}</figcaption>
          </figure>
        ))}
      </div>

      <Card title="NER per-type report · seqeval">
        <pre className="overflow-x-auto rounded-lg border border-white/[0.06] bg-black/30 p-4 font-mono text-[11.5px] leading-5 text-zinc-400">
          {ner.per_type_report}
        </pre>
      </Card>

      <Card title="Honest limitations — say these in the viva">
        <ul className="space-y-2 text-sm leading-6 text-zinc-400">
          {[
            "NER trained on only 220 annotated resumes → entity F1 0.46. Name 0.90 / Location 0.72 are strong; Skills 0.11 is weak, so the app additionally harvests skill phrases from lines the BiLSTM labels as skills-section.",
            "The role dataset has 24 fixed categories with no “Data Science” class — data-science resumes map to neighbours like Information-Technology.",
            "project lines are ~2% of the section dataset; class weights (project ≈ 10.7×) compensate, its recall stays weakest.",
            "Match score = 40% MiniLM semantic + 30% skills + 15% sections + 15% role, computed on text with names, emails, phones and gendered words stripped.",
          ].map((t, i) => (
            <li key={i} className="flex gap-2.5">
              <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-zinc-600" />{t}
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
