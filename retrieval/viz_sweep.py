#!/usr/bin/env python3
"""
Generate a self-contained HTML visualization of a topic-extractor sweep.

Usage:
    python3 retrieval/viz_sweep.py retrieval/runs/YYYYMMDD-HHMMSS.jsonl
    # writes retrieval/runs/YYYYMMDD-HHMMSS.html next to it

The HTML embeds both the sweep records and the source file contents so it is
fully offline-portable. Open in any browser.

Features
--------
- Filter by model and/or file; stats strip updates live.
- Click a span chip to highlight those lines in the source pane.
- Duplicate span-sets across topics flagged inline (dim-8 smell).
- Inline scoring widget per record (dims 5-8, 0-3), weighted quality live.
- Scores persist to localStorage keyed by run_id.
- Export button generates the manual-rubric markdown matching
  MANUAL_RUBRIC_TEMPLATE in extract_topics.py.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def load_records(jsonl_path: Path) -> list[dict]:
    return [json.loads(line) for line in jsonl_path.read_text().splitlines() if line.strip()]


def load_sources(records: list[dict]) -> dict[str, str]:
    sources: dict[str, str] = {}
    for r in records:
        rel = r["file"]
        if rel in sources:
            continue
        path = REPO_ROOT / rel
        sources[rel] = path.read_text(encoding="utf-8", errors="replace") \
            if path.exists() else f"[file not found: {rel}]"
    return sources


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Topic Extractor Sweep __TAG__</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
         margin: 0; display: flex; height: 100vh; color: #222; }
  .main { flex: 1 1 55%; overflow-y: auto; }
  .sidebar { flex: 1 1 45%; border-left: 1px solid #ddd; overflow-y: auto;
             padding: 12px 16px; background: #fafafa; font-size: 0.88em; }
  .controls { position: sticky; top: 0; background: #fff; padding: 10px 16px;
              border-bottom: 1px solid #ddd; display: flex; flex-wrap: wrap;
              gap: 12px; align-items: center; z-index: 10; }
  .controls label { font-size: 0.9em; }
  .controls select { padding: 4px 6px; font-size: 0.9em; }
  .stats { display: flex; gap: 14px; font-size: 0.85em; color: #555;
           margin-left: auto; font-family: monospace; align-items: center; }
  .stats b { color: #222; }
  .btn { padding: 4px 10px; font-size: 0.82em; border: 1px solid #bbb;
         background: #fff; border-radius: 4px; cursor: pointer; }
  .btn:hover { background: #f2f2f2; }
  .btn.danger { border-color: #d79a9a; color: #b42318; }
  .btn.primary { border-color: #0366d6; color: #0366d6; }
  #progress { font-family: monospace; font-size: 0.85em; padding: 2px 8px;
              background: #eef3f8; border-radius: 10px; }

  details.help { margin: 10px 16px 0; border: 1px solid #e4e4e4;
                 border-radius: 6px; background: #fbfbfb; }
  details.help > summary { padding: 8px 12px; font-weight: 600;
                           font-size: 0.9em; color: #333; }
  .help-body { padding: 0 16px 12px; font-size: 0.87em; line-height: 1.55;
               color: #333; }
  .help-body h4 { margin: 10px 0 4px; font-size: 0.92em; }
  .help-body code { background: #f1f3f5; padding: 1px 4px; border-radius: 3px;
                    font-size: 0.88em; }
  .help-body ul { margin: 4px 0 8px; padding-left: 20px; }
  .help-body li { margin: 2px 0; }
  .help-body .weight { color: #666; font-weight: normal; font-size: 0.85em; }

  #cards { padding: 12px 16px; }
  .card { border: 1px solid #ddd; border-radius: 6px; margin: 0 0 14px 0;
          padding: 12px; background: #fff; }
  .card-header { display: flex; justify-content: space-between;
                 align-items: baseline; border-bottom: 1px solid #eee;
                 padding-bottom: 6px; margin-bottom: 8px; gap: 10px; }
  .card-title { font-weight: 600; font-family: monospace; font-size: 0.95em; }
  .card-file { color: #0366d6; cursor: pointer; margin-left: 4px; }
  .card-file:hover { text-decoration: underline; }
  .card-meta { font-size: 0.82em; color: #666; font-family: monospace;
               text-align: right; }
  .topic { margin: 6px 0; padding: 6px 10px; border-left: 3px solid #5b9bd5;
           background: #f4f8fc; border-radius: 0 4px 4px 0; }
  .topic-name { font-weight: 600; color: #1a1a1a; font-family: monospace;
                font-size: 0.92em; }
  .topic-desc { font-size: 0.85em; color: #444; margin: 3px 0 5px; line-height: 1.4; }
  .span-chip { display: inline-block; padding: 2px 8px; margin: 2px 3px 0 0;
               background: #e7f0f9; border: 1px solid #cde0f1; border-radius: 10px;
               font-family: monospace; font-size: 0.78em; cursor: pointer;
               color: #0366d6; }
  .span-chip:hover { background: #cde0f1; }
  .status-ok { color: #1a7f37; }
  .status-bad { color: #b42318; }
  .dup-warn { color: #b42318; font-size: 0.75em; margin-left: 6px;
              font-family: -apple-system, sans-serif; font-weight: normal; }

  .score-row { display: flex; align-items: center; gap: 10px; margin-top: 10px;
               padding: 8px 10px; background: #f7f9fc; border-top: 1px solid #eef;
               border-radius: 0 0 4px 4px; flex-wrap: wrap; font-size: 0.85em; }
  .score-row label { font-family: monospace; color: #555; display: flex;
                     align-items: center; gap: 4px; }
  .score-row select { font-size: 0.85em; padding: 2px 4px; }
  .score-row input.notes { flex: 1; min-width: 120px; padding: 3px 6px;
                           font-size: 0.85em; border: 1px solid #ccc;
                           border-radius: 3px; }
  .q-badge { font-family: monospace; font-weight: 600; padding: 3px 8px;
             border-radius: 10px; background: #eee; color: #555;
             min-width: 56px; text-align: center; }
  .q-badge.pass { background: #dcf5e0; color: #1a7f37; }
  .q-badge.fail { background: #fde3df; color: #b42318; }
  .q-inline { font-family: monospace; font-size: 0.82em; }

  .sidebar h3 { margin: 0 0 8px; font-size: 0.95em; }
  .sidebar .file-label { font-family: monospace; color: #555; font-size: 0.82em;
                         margin-bottom: 8px; word-break: break-all; }
  .source { font-family: "SF Mono", Consolas, monospace; font-size: 0.8em;
            white-space: pre; line-height: 1.45; background: #fff;
            border: 1px solid #e4e4e4; border-radius: 4px; padding: 6px 0;
            overflow-x: auto; }
  .line { padding: 0 10px; display: block; }
  .line.hl { background: #fff3b8; }
  .line.hl-strong { background: #ffd86e; }
  .line-num { color: #bbb; user-select: none; display: inline-block;
              width: 40px; text-align: right; margin-right: 10px; }

  pre.raw { font-size: 0.75em; max-height: 200px; overflow: auto;
            background: #fff5f5; padding: 6px; margin: 4px 0 0; }
  .toast { position: fixed; bottom: 16px; left: 50%; transform: translateX(-50%);
           background: #222; color: #fff; padding: 8px 14px; border-radius: 4px;
           font-size: 0.85em; opacity: 0; transition: opacity 0.25s;
           pointer-events: none; z-index: 100; }
  .toast.show { opacity: 1; }
</style>
</head>
<body>
<div class="main">
  <div class="controls">
    <label>Model:
      <select id="modelFilter"><option value="">(all)</option></select>
    </label>
    <label>File:
      <select id="fileFilter"><option value="">(all)</option></select>
    </label>
    <span id="progress">scored: 0 / 0</span>
    <button class="btn primary" id="exportBtn" title="Download manual-rubric.md">Export .md</button>
    <button class="btn" id="copyBtn" title="Copy manual-rubric.md to clipboard">Copy</button>
    <button class="btn danger" id="clearBtn" title="Clear all scores (localStorage)">Clear</button>
    <div class="stats" id="stats"></div>
  </div>

  <details class="help" id="helpPanel" open>
    <summary>How to score (dims 5-8)</summary>
    <div class="help-body">
      <p>
        Each dim is scored <code>0-3</code>. Weighted quality =
        <code>0.35·dim5 + 0.35·dim6 + 0.20·dim7 + 0.10·dim8</code>.
        Exit threshold for this spike: <b>≥ 2.2</b>.
        Scores persist in your browser (localStorage, keyed by run_id).
      </p>

      <h4>dim5 — Name quality <span class="weight">(35%)</span></h4>
      <ul>
        <li><b>3</b> — Specific, concise, memorable. Reads like a domain term.
          e.g. <code>latent_topic_graph</code>, <code>vram_budget_constraints</code></li>
        <li><b>2</b> — Accurate but generic. e.g. <code>retrieval_system</code>, <code>repo_structure</code></li>
        <li><b>1</b> — Vague or catch-all. e.g. <code>memory_architecture</code>, <code>development_workflow</code></li>
        <li><b>0</b> — Missing, placeholder, or name contradicts content</li>
      </ul>

      <h4>dim6 — Description quality <span class="weight">(35%)</span></h4>
      <ul>
        <li><b>3</b> — Concrete, references real content with specifics
          ("12GB VRAM limit shapes model selection…")</li>
        <li><b>2</b> — Accurate but general; could fit many files</li>
        <li><b>1</b> — Boilerplate prefix ("This topic describes…") or filler</li>
        <li><b>0</b> — Wrong, empty, or unrelated to the spans</li>
      </ul>

      <h4>dim7 — Boundary sanity <span class="weight">(20%)</span></h4>
      <p style="margin:4px 0;">Click the span chips and verify: do the highlighted lines actually contain what the topic name claims?</p>
      <ul>
        <li><b>3</b> — Every span tight on topic, no irrelevant lines included</li>
        <li><b>2</b> — Minor overreach (a few adjacent off-topic lines)</li>
        <li><b>1</b> — Significant off-topic content inside spans</li>
        <li><b>0</b> — Spans miss the topic entirely or point to wrong material</li>
      </ul>

      <h4>dim8 — Mutual coverage <span class="weight">(10%)</span></h4>
      <p style="margin:4px 0;">Judge all topics together for this (model, file): do they cover the file without heavy overlap or duplication?</p>
      <ul>
        <li><b>3</b> — Complementary, minimal overlap, file well covered</li>
        <li><b>2</b> — Some overlap or small gaps — acceptable</li>
        <li><b>1</b> — Noticeable redundancy or blind spots</li>
        <li><b>0</b> — Duplicate span-sets (auto-flagged ⚠) or major areas missing</li>
      </ul>

      <p style="margin-top:10px; color:#666;">
        Tip: click the file name in the card header to load the source with
        <i>no</i> highlights — useful before you judge coverage for the whole
        record. Then click individual span chips to audit dim 7.
      </p>
    </div>
  </details>

  <div id="cards"></div>
</div>
<div class="sidebar">
  <h3>Source preview</h3>
  <div class="file-label" id="sidebarFile">Click a span chip or file name to load source.</div>
  <div class="source" id="source"></div>
</div>
<div class="toast" id="toast"></div>

<script>
const DATA = __DATA_JSON__;
const SOURCES = __SOURCES_JSON__;
const TAG = "__TAG__";
const SCORES_KEY = "sweep-scores-" + TAG;
const DIMS = ["dim5", "dim6", "dim7", "dim8"];
const DIM_LABELS = { dim5: "name", dim6: "desc", dim7: "bound", dim8: "cover" };
const WEIGHTS = { dim5: 0.35, dim6: 0.35, dim7: 0.20, dim8: 0.10 };
const EXIT_THRESHOLD = 2.2;

let SCORES = loadScores();

// ---------- helpers ----------
function el(tag, props = {}, children = []) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k === "class") n.className = v;
    else if (k === "text") n.textContent = v;
    else if (k === "data") for (const [dk, dv] of Object.entries(v)) n.dataset[dk] = dv;
    else if (k === "on") for (const [ek, ev] of Object.entries(v)) n.addEventListener(ek, ev);
    else n.setAttribute(k, v);
  }
  for (const c of children) if (c) n.appendChild(c);
  return n;
}
function txt(s) { return document.createTextNode(s == null ? "" : String(s)); }
function fmtPct(n) { return n == null ? "-" : (n * 100).toFixed(0) + "%"; }
function fmtNum(n, d = 1) { return n == null ? "-" : Number(n).toFixed(d); }
function clear(n) { while (n.firstChild) n.removeChild(n.firstChild); }

// ---------- scores ----------
function loadScores() {
  try { return JSON.parse(localStorage.getItem(SCORES_KEY) || "{}"); }
  catch (e) { return {}; }
}
function saveScores() {
  localStorage.setItem(SCORES_KEY, JSON.stringify(SCORES));
}
function getScore(runId) { return SCORES[runId] || {}; }
function setDim(runId, dim, val) {
  SCORES[runId] = SCORES[runId] || {};
  if (val === "" || val == null) delete SCORES[runId][dim];
  else SCORES[runId][dim] = Number(val);
  saveScores();
  updateProgress();
  updateCardQuality(runId);
}
function setNotes(runId, notes) {
  SCORES[runId] = SCORES[runId] || {};
  if (!notes) delete SCORES[runId].notes;
  else SCORES[runId].notes = notes;
  saveScores();
}
function weightedQuality(s) {
  if (DIMS.some(d => s[d] == null)) return null;
  return DIMS.reduce((acc, d) => acc + WEIGHTS[d] * s[d], 0);
}
function isScored(s) { return DIMS.every(d => s[d] != null); }

function updateProgress() {
  const total = DATA.length;
  const done = DATA.filter(r => isScored(getScore(r.run_id))).length;
  document.getElementById("progress").textContent = `scored: ${done} / ${total}`;
}

function updateCardQuality(runId) {
  const badge = document.querySelector(`[data-qbadge="${runId}"]`);
  const inline = document.querySelector(`[data-qinline="${runId}"]`);
  if (!badge) return;
  const q = weightedQuality(getScore(runId));
  badge.classList.remove("pass", "fail");
  if (q == null) {
    badge.textContent = "q=—";
  } else {
    badge.textContent = "q=" + q.toFixed(2);
    badge.classList.add(q >= EXIT_THRESHOLD ? "pass" : "fail");
  }
  if (inline) inline.textContent = q == null ? "q=—" : "q=" + q.toFixed(2);
}

// ---------- dropdowns ----------
const models = [...new Set(DATA.map(r => r.model))].sort();
const files  = [...new Set(DATA.map(r => r.file))].sort();
const modelSel = document.getElementById("modelFilter");
const fileSel  = document.getElementById("fileFilter");
for (const m of models) modelSel.add(new Option(m, m));
for (const f of files)  fileSel.add(new Option(f, f));
modelSel.addEventListener("change", render);
fileSel.addEventListener("change", render);

// ---------- rendering ----------
function filtered() {
  const m = modelSel.value, f = fileSel.value;
  return DATA.filter(r => (!m || r.model === m) && (!f || r.file === f));
}

function render() {
  const rows = filtered();
  const cardsDiv = document.getElementById("cards");
  clear(cardsDiv);

  const avg = xs => xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null;
  const cov = avg(rows.map(r => r.rubric?.dim3_span_coverage).filter(x => x != null));
  const nc  = avg(rows.map(r => r.rubric?.dim4_noncontiguity_rate).filter(x => x != null));
  const tps = avg(rows.map(r => r.rubric?.dim10_latency_tps).filter(x => x));
  const tc  = avg(rows.map(r => r.rubric?.dim2_topic_count).filter(x => x != null));

  const stats = document.getElementById("stats");
  clear(stats);
  const stat = (label, val) => {
    const s = el("span");
    s.appendChild(txt(label + "="));
    s.appendChild(el("b", { text: val }));
    return s;
  };
  stats.appendChild(stat("n", String(rows.length)));
  stats.appendChild(stat("topics", fmtNum(tc)));
  stats.appendChild(stat("cov", fmtPct(cov)));
  stats.appendChild(stat("NC", fmtPct(nc)));
  stats.appendChild(stat("TPS", fmtNum(tps)));

  for (const r of rows) cardsDiv.appendChild(renderCard(r));
  updateProgress();
}

function spanKey(span) { return span[0] + "-" + span[1]; }
function spanSig(t) { return (t.spans || []).map(spanKey).sort().join("|"); }

function renderCard(r) {
  const rb = r.rubric || {};
  const statusCls = r.status === "ok" ? "status-ok" : "status-bad";

  const sigCount = {};
  for (const t of (r.parsed_topics || [])) {
    const s = spanSig(t);
    sigCount[s] = (sigCount[s] || 0) + 1;
  }

  const fileLink = el("span", {
    class: "card-file",
    text: "· " + r.file,
    on: { click: () => loadSource(r.file, null) },
  });
  const title = el("div", { class: "card-title" }, [txt(r.model + " "), fileLink]);

  const qBadge = el("span", {
    class: "q-badge",
    text: "q=—",
    data: { qbadge: r.run_id },
  });
  const meta = el("div", { class: "card-meta" });
  const metaLine1 = el("div");
  metaLine1.appendChild(el("span", { class: statusCls, text: r.status }));
  metaLine1.appendChild(txt(
    ` · topics=${rb.dim2_topic_count ?? "-"}` +
    ` · cov=${fmtPct(rb.dim3_span_coverage)}` +
    ` · NC=${fmtPct(rb.dim4_noncontiguity_rate)}` +
    ` · ${fmtNum(rb.dim10_latency_tps)}tok/s` +
    ` · ${r.prompt_tokens}→${r.output_tokens}tok`
  ));
  meta.appendChild(metaLine1);
  const metaLine2 = el("div", { style: "margin-top:3px;" });
  metaLine2.appendChild(qBadge);
  meta.appendChild(metaLine2);

  const header = el("div", { class: "card-header" }, [title, meta]);
  const card = el("div", { class: "card" }, [header]);

  for (const t of (r.parsed_topics || [])) {
    card.appendChild(renderTopic(t, r.file, sigCount[spanSig(t)] > 1));
  }

  if (r.status !== "ok" && (!r.parsed_topics || r.parsed_topics.length === 0)) {
    const summary = el("summary", { text: "raw response" });
    const pre = el("pre", { class: "raw", text: (r.raw_response || "").slice(0, 2000) });
    card.appendChild(el("details", {}, [summary, pre]));
  }

  card.appendChild(renderScoreRow(r));
  // set initial quality display
  setTimeout(() => updateCardQuality(r.run_id), 0);
  return card;
}

function renderTopic(t, file, isDup) {
  const name = el("div", { class: "topic-name", text: t.name || "(no name)" });
  if (isDup) name.appendChild(el("span", { class: "dup-warn", text: "⚠ duplicate span set" }));
  const desc = el("div", { class: "topic-desc", text: t.description || "" });

  const wrap = el("div", { class: "topic" }, [name, desc]);
  for (const sp of (t.spans || [])) {
    const [a, b] = sp;
    wrap.appendChild(el("span", {
      class: "span-chip",
      text: `${a}–${b}`,
      on: { click: () => loadSource(file, { allSpans: t.spans, pick: [a, b] }) },
    }));
  }
  return wrap;
}

function renderScoreRow(r) {
  const row = el("div", { class: "score-row" });
  const current = getScore(r.run_id);

  for (const dim of DIMS) {
    const lbl = el("label", { text: DIM_LABELS[dim] + ":" });
    const sel = el("select");
    sel.add(new Option("—", ""));
    for (let v = 0; v <= 3; v++) sel.add(new Option(String(v), String(v)));
    sel.value = current[dim] != null ? String(current[dim]) : "";
    sel.addEventListener("change", () => setDim(r.run_id, dim, sel.value));
    lbl.appendChild(sel);
    row.appendChild(lbl);
  }

  const notes = el("input", {
    class: "notes",
    type: "text",
    placeholder: "notes (optional)",
    value: current.notes || "",
  });
  notes.addEventListener("input", () => setNotes(r.run_id, notes.value));
  row.appendChild(notes);

  row.appendChild(el("span", { class: "q-inline", text: "q=—",
                               data: { qinline: r.run_id } }));
  return row;
}

// ---------- source pane ----------
function loadSource(relPath, highlight) {
  const text = SOURCES[relPath] || "(source unavailable)";
  document.getElementById("sidebarFile").textContent = relPath;
  const src = document.getElementById("source");
  clear(src);

  const hl = new Set(), strong = new Set();
  if (highlight?.allSpans) for (const [a, b] of highlight.allSpans)
    for (let i = a; i <= b; i++) hl.add(i);
  if (highlight?.pick) {
    const [a, b] = highlight.pick;
    for (let i = a; i <= b; i++) strong.add(i);
  }

  const lines = text.split("\n");
  let firstStrong = null;
  lines.forEach((line, idx) => {
    const n = idx + 1;
    const cls = "line" + (strong.has(n) ? " hl-strong" : (hl.has(n) ? " hl" : ""));
    const row = el("span", { class: cls }, [
      el("span", { class: "line-num", text: String(n) }),
      txt(line || " "),
    ]);
    src.appendChild(row);
    if (strong.has(n) && firstStrong == null) firstStrong = row;
  });
  if (firstStrong) firstStrong.scrollIntoView({ block: "center" });
  else src.scrollTop = 0;
}

// ---------- export ----------
function buildMarkdown() {
  const header =
    "# Phase 1 Manual Rubric Scores\n" +
    "# weighted_quality = 0.35*dim5 + 0.35*dim6 + 0.20*dim7 + 0.10*dim8\n" +
    "# Stability bonus: +0.5 if Jaccard >= 0.85, +0.25 if >= 0.80\n" +
    "# Speed penalty: only if dim10_latency_tps < 15 tok/s\n" +
    "# Exit threshold: >= 2.2\n" +
    `# Source: retrieval/runs/${TAG}.jsonl\n\n` +
    "| run_id | model | file | dim5_name | dim6_desc | dim7_boundary | dim8_coverage | weighted_quality | notes |\n" +
    "|---|---|---|---|---|---|---|---|---|\n";

  const rows = DATA.map(r => {
    const s = getScore(r.run_id);
    const q = weightedQuality(s);
    const qStr = q == null ? "-" : q.toFixed(2);
    const fname = r.file.split("/").pop();
    const prefix = r.run_id.slice(0, 8);
    const cell = v => (v == null ? "-" : String(v));
    const notes = (s.notes || "").replace(/\|/g, "\\|");
    return `| ${prefix} | ${r.model} | ${fname} | ${cell(s.dim5)} | ${cell(s.dim6)} | ${cell(s.dim7)} | ${cell(s.dim8)} | ${qStr} | ${notes} |`;
  });

  return header + rows.join("\n") + "\n";
}

function toast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 1800);
}

document.getElementById("exportBtn").addEventListener("click", () => {
  const md = buildMarkdown();
  const blob = new Blob([md], { type: "text/markdown" });
  const url  = URL.createObjectURL(blob);
  const a = el("a", { href: url, download: `${TAG}-manual-rubric.md` });
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
  toast("Downloaded " + TAG + "-manual-rubric.md");
});

document.getElementById("copyBtn").addEventListener("click", async () => {
  const md = buildMarkdown();
  try {
    await navigator.clipboard.writeText(md);
    toast("Copied " + md.length + " chars to clipboard");
  } catch (e) {
    toast("Copy failed — use Export instead");
  }
});

document.getElementById("clearBtn").addEventListener("click", () => {
  if (!confirm("Clear ALL scores for this sweep? This cannot be undone.")) return;
  SCORES = {};
  saveScores();
  render();
  toast("Cleared all scores");
});

render();
</script>
</body>
</html>
"""


def build_html(records: list[dict], sources: dict[str, str], tag: str) -> str:
    return (
        HTML_TEMPLATE
        .replace("__TAG__", tag)
        .replace("__DATA_JSON__", json.dumps(records))
        .replace("__SOURCES_JSON__", json.dumps(sources))
    )


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path/to/runs/TAG.jsonl>", file=sys.stderr)
        sys.exit(2)

    jsonl_path = Path(sys.argv[1]).resolve()
    if not jsonl_path.exists():
        print(f"File not found: {jsonl_path}", file=sys.stderr)
        sys.exit(1)

    records = load_records(jsonl_path)
    sources = load_sources(records)
    tag = jsonl_path.stem
    html = build_html(records, sources, tag)
    out_path = jsonl_path.with_suffix(".html")
    out_path.write_text(html, encoding="utf-8")
    print(f"Wrote: {out_path}")
    print(f"  {len(records)} records, {len(sources)} source files embedded")


if __name__ == "__main__":
    main()
