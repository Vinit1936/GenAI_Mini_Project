/** Map NER entities (character offsets in *extracted* text) onto pdf.js text-layer
    positions, so annotations can be drawn over the rendered PDF.

    Strategy: build a normalised "soup" of the page's text items (each character
    remembers which item + index it came from), then string-match each entity in
    document order with a moving cursor; fall back to global search and shortened
    prefixes when pypdf and pdf.js disagree on layout order. */

function normalize(s) {
  return String(s).toLowerCase().replace(/\s+/g, " ").trim();
}

/** Build the normalised page string. Returns {soup, map} where map[i] is
    {item, idx} for soup[i], or {item: -1} for inserted separators. */
export function buildSoup(items) {
  let soup = "";
  const map = [];
  items.forEach((item, idx) => {
    for (const ch of item.str) {
      const n = /\s/.test(ch) ? " " : ch.toLowerCase();
      if (n === " " && soup.endsWith(" ")) continue; // collapse runs of spaces
      map.push({ item: idx, idx: map.length ? map.length : 0, ch: n });
      soup += n;
    }
    if (soup && !soup.endsWith(" ")) {
      map.push({ item: -1, idx: -1, ch: " " });
      soup += " ";
    }
  });
  // second pass: give each mapped char its real index within its item
  const perItem = items.map(() => 0);
  for (const m of map) {
    if (m.item >= 0) {
      m.idx = perItem[m.item]++;
    }
  }
  return { soup, map };
}

function findFrom(soup, needle, from) {
  const n = normalize(needle);
  if (n.length < 3) return null;
  const i = soup.indexOf(n, from);
  if (i === -1) return null;
  return { start: i, end: i + n.length };
}

/** For one entity hit, compute per-line rectangles in viewport coordinates. */
function rectsForHit(hit, map, items, viewport) {
  const byItem = new Map();
  for (let i = hit.start; i < hit.end; i++) {
    const m = map[i];
    if (!m || m.item < 0) continue;
    if (!byItem.has(m.item)) byItem.set(m.item, { min: m.idx, max: m.idx });
    const r = byItem.get(m.item);
    r.min = Math.min(r.min, m.idx);
    r.max = Math.max(r.max, m.idx);
  }
  const rects = [];
  for (const [itemIdx, { min, max }] of byItem) {
    const it = items[itemIdx];
    const t = it.transform;
    const h = it.height || Math.abs(t[3]) || 10;
    const w = it.width || 0;
    const len = Math.max(1, it.str.length);
    const x0 = t[4] + (w * min) / len;
    const x1 = t[4] + (w * (max + 1)) / len;
    const yTop = t[5] + h * 0.25;
    const yBot = t[5] - h * 0.8;
    const [vx0, vy0] = viewport.convertToViewportPoint(x0, yTop);
    const [vx1, vy1] = viewport.convertToViewportPoint(x1, yBot);
    const x = Math.min(vx0, vx1), y = Math.min(vy0, vy1);
    const rw = Math.max(3, Math.abs(vx1 - vx0)), rh = Math.max(6, Math.abs(vy1 - vy0));
    rects.push({ x, y, w: rw, h: rh });
  }
  return rects;
}

/** Match ONE text (an issue anchor) against a page's items → viewport rects. */
export function matchAnchor(items, text, viewport) {
  const usable = items.filter((it) => it.str && it.str.trim());
  const { soup, map } = buildSoup(usable);
  let hit = findFrom(soup, text, 0);
  if (!hit) {
    const words = normalize(text).split(" ");
    for (const n of [4, 3, 2]) {
      const shorter = words.slice(0, n).join(" ");
      if (shorter.length >= 4) {
        hit = findFrom(soup, shorter, 0);
        if (hit) break;
      }
    }
  }
  if (!hit) return [];
  return rectsForHit(hit, map, usable, viewport);
}

/** Match all entities against one page's items.
    Returns [{type, confidence, rects}] in viewport pixels. */
export function matchEntities(items, entities, viewport) {
  const usable = items.filter((it) => it.str && it.str.trim());
  const { soup, map } = buildSoup(usable);
  const sorted = [...(entities || [])]
    .filter((e) => e.text && String(e.text).trim().length >= 3)
    .sort((a, b) => a.start - b.start);

  let cursor = 0;
  const out = [];
  for (const ent of sorted) {
    let hit =
      findFrom(soup, ent.text, cursor) ??
      findFrom(soup, ent.text, 0);
    if (!hit) {
      // layout-order disagreement: try progressively shorter prefixes
      const words = normalize(ent.text).split(" ");
      for (const n of [3, 2]) {
        const shorter = words.slice(0, n).join(" ");
        if (shorter.length >= 4) {
          hit = findFrom(soup, shorter, cursor) ?? findFrom(soup, shorter, 0);
          if (hit) break;
        }
      }
    }
    if (!hit) continue;
    cursor = hit.end;
    const rects = rectsForHit(hit, map, usable, viewport);
    if (rects.length) out.push({ type: ent.type, confidence: ent.confidence, rects });
  }
  return out;
}
