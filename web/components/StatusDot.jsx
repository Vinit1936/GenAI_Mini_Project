"use client";

import { useEffect, useState } from "react";
import { ML_API } from "../lib/api";

/** Pulsing dot indicating whether the ML engine is reachable. */
export default function StatusDot() {
  const [up, setUp] = useState(null);

  useEffect(() => {
    let alive = true;
    const check = () =>
      fetch(`${ML_API}/health`)
        .then((r) => alive && setUp(r.ok))
        .catch(() => alive && setUp(false));
    check();
    const id = setInterval(check, 15000);
    return () => { alive = false; clearInterval(id); };
  }, []);

  return (
    <span className="inline-flex items-center gap-2 text-[12px] text-[#888]" title={up ? "analysis engine online" : "analysis engine offline — run uvicorn on port 8000"}>
      <span
        className={`h-2 w-2 rounded-full ${up === null ? "bg-[#555]" : up ? "status-live bg-[#0099ff]" : "bg-red-500"}`}
      />
      {up === null ? "connecting…" : up ? "engine online" : "engine offline"}
    </span>
  );
}
