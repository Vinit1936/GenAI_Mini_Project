"use client";

import { useEffect, useRef, useState } from "react";

/** The uploaded PDF rendered page by page — a clean, plain preview. */
export default function PdfXray({ file }) {
  const [pages, setPages] = useState([]); // {width, height, png}
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState("");
  const wrapRef = useRef(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const pdfjs = await import("pdfjs-dist");
        pdfjs.GlobalWorkerOptions.workerSrc = "/pdf.worker.min.mjs";
        const buf = await file.arrayBuffer();
        const doc = await pdfjs.getDocument({ data: buf }).promise;
        // let layout settle before measuring the container (grid columns apply late)
        const measure = () => Math.min(620, (wrapRef.current?.clientWidth || 0) - 2);
        let target = measure();
        if (target < 100) {
          await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
          target = measure();
        }
        if (target < 100) target = 480; // sensible default if measurement still fails
        const out = [];
        for (let p = 1; p <= doc.numPages && !cancelled; p++) {
          const page = await doc.getPage(p);
          const base = page.getViewport({ scale: 1 });
          const vp = page.getViewport({ scale: target / base.width });
          const canvas = document.createElement("canvas");
          canvas.width = Math.ceil(vp.width);
          canvas.height = Math.ceil(vp.height);
          await page.render({ canvasContext: canvas.getContext("2d"), viewport: vp }).promise;
          out.push({ width: canvas.width, height: canvas.height, png: canvas.toDataURL("image/png") });
        }
        if (cancelled) return;
        setPages(out);
        setStatus("ready");
      } catch (e) {
        if (!cancelled) { setError(e.message || String(e)); setStatus("error"); }
      }
    })();
    return () => { cancelled = true; };
  }, [file]);

  if (status === "loading")
    return (
      <div className="rounded-[15px] border border-[rgba(255,255,255,0.08)] bg-[#101014] p-8 text-center">
        <div className="skeleton mx-auto h-[420px] w-full max-w-[420px]" />
        <p className="mt-4 text-[13px] text-[#888]">rendering your PDF…</p>
      </div>
    );
  if (status === "error")
    return (
      <div className="rounded-[15px] border border-red-400/20 bg-red-400/10 p-6 text-[13px] text-red-300">
        Couldn't render the PDF preview ({error}). The analysis itself is unaffected.
      </div>
    );

  return (
    <div>
      <p className="mb-4 text-[11px] font-medium uppercase tracking-[0.14em] text-[#888]">
        Uploaded PDF · {pages.length} page{pages.length > 1 ? "s" : ""}
      </p>
      <div ref={wrapRef} className="max-h-[34rem] space-y-4 overflow-y-auto rounded-[15px] border border-[rgba(255,255,255,0.08)] bg-[#101014] p-4">
        {pages.map((pg, i) => (
          <div key={i} className="mx-auto w-full" style={{ maxWidth: pg.width }}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={pg.png} alt={`resume page ${i + 1}`} className="block w-full rounded-[6px]" draggable={false} />
          </div>
        ))}
      </div>
    </div>
  );
}
