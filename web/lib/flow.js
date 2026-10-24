/** Flow state between landing → wizard screens (sessionStorage).
    The uploaded PDF is kept as base64 (size-guarded) so the real-file preview
    survives the route change; plain text always survives regardless. */

const K = {
  resume: "rl.resume",
  resumeName: "rl.resumeName",
  pdf: "rl.pdf",
  pdfName: "rl.pdfName",
};

const MAX_PDF = 3.5 * 1024 * 1024; // keep sessionStorage comfortably under quota

export const saveResume = (text, name = "pasted") => {
  sessionStorage.setItem(K.resume, text);
  sessionStorage.setItem(K.resumeName, name);
};

export const loadResume = () => ({
  text: sessionStorage.getItem(K.resume) || "",
  name: sessionStorage.getItem(K.resumeName) || "",
});

async function fileToBase64(file) {
  const buf = await file.arrayBuffer();
  let binary = "";
  const bytes = new Uint8Array(buf);
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunk));
  }
  return btoa(binary);
}

/** Best-effort: stash the uploaded PDF so the results screen can render the
    original file. Returns true when stashed. Never throws. */
export async function savePdf(file) {
  try {
    if (!file || file.type !== "application/pdf" || file.size > MAX_PDF) return false;
    const b64 = await fileToBase64(file);
    sessionStorage.setItem(K.pdf, b64);
    sessionStorage.setItem(K.pdfName, file.name || "resume.pdf");
    return true;
  } catch {
    return false;
  }
}

export function loadPdf() {
  try {
    const b64 = sessionStorage.getItem(K.pdf);
    if (!b64) return null;
    const bin = atob(b64);
    const bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    return new File([bytes], sessionStorage.getItem(K.pdfName) || "resume.pdf", { type: "application/pdf" });
  } catch {
    return null;
  }
}

export const clearResume = () => {
  Object.values(K).forEach((k) => sessionStorage.removeItem(k));
};
