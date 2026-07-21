"""The Layout Link explorer page — a single self-contained HTML app.

Served by :mod:`carterkit.explore`. No external assets (works offline / air-gapped
LAN): all CSS/JS inline. The page reads `/api/contract` and `/api/status`, streams
`/events` (SSE), and POSTs to `/api/push`, `/api/fill`, `/api/repull`.
"""

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CAR-TER Layout Link</title>
<style>
  :root {
    --bg: #0b0e14; --panel: #12161f; --card: #171c27; --edge: #232a38;
    --text: #e7ebf3; --dim: #8a94a7; --faint: #5b6474;
    --accent: #667eea; --accent-soft: #667eea33;
    --ok: #34d399; --warn: #fbbf24; --err: #f87171;
    --t-number: #60a5fa; --t-boolean: #34d399; --t-string: #f472b6;
    --t-object: #a78bfa; --t-none: #6b7280; --t-array: #fb923c; --t-json: #a78bfa;
    --mono: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  }
  * { box-sizing: border-box; margin: 0; }
  ::-webkit-scrollbar { width: 8px; height: 8px; }
  ::-webkit-scrollbar-thumb { background: var(--edge); border-radius: 99px; }
  ::-webkit-scrollbar-track { background: transparent; }
  * { scrollbar-width: thin; scrollbar-color: var(--edge) transparent; }
  html, body { height: 100%; }
  body {
    background: var(--bg); color: var(--text);
    font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    display: flex; flex-direction: column;
  }
  /* ── header ─────────────────────────────────────────── */
  header {
    display: flex; align-items: center; gap: 14px;
    padding: 12px 20px; background: var(--panel);
    border-bottom: 1px solid var(--edge); flex-wrap: wrap;
  }
  .logo { display: flex; align-items: center; gap: 10px; }
  .logo-mark {
    width: 30px; height: 30px; border-radius: 8px;
    background: linear-gradient(135deg, var(--accent), #764ba2);
    display: grid; place-items: center; font-weight: 800; font-size: 15px; color: #fff;
  }
  .logo h1 { font-size: 16px; font-weight: 700; }
  .logo .sub { font-size: 11px; color: var(--dim); }
  #layout-name { color: var(--accent); }
  .status {
    display: flex; align-items: center; gap: 8px; margin-left: auto;
    font-size: 12px; color: var(--dim); flex-wrap: wrap;
  }
  .pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: var(--card); border: 1px solid var(--edge);
    border-radius: 99px; padding: 3px 10px; white-space: nowrap;
  }
  .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--faint); }
  .dot.on { background: var(--ok); box-shadow: 0 0 6px var(--ok); }
  .dot.wait { background: var(--warn); }
  .btn {
    background: var(--card); color: var(--text); border: 1px solid var(--edge);
    border-radius: 8px; padding: 5px 12px; font-size: 12px; cursor: pointer;
    text-decoration: none; display: inline-flex; align-items: center; gap: 6px;
  }
  .btn:hover { border-color: var(--accent); color: var(--accent); }
  .btn.primary { background: var(--accent); border-color: var(--accent); color: #fff; }
  .btn.primary:hover { filter: brightness(1.1); color: #fff; }
  /* ── device mirror ──────────────────────────────────── */
  #mirror {
    display: none; gap: 12px; align-items: center; flex-wrap: wrap;
    padding: 9px 20px; background: var(--panel);
    border-bottom: 1px solid var(--edge);
  }
  #mirror.on { display: flex; }
  #mirror .m-title {
    font-size: 11px; text-transform: uppercase; letter-spacing: .12em; color: var(--dim);
  }
  #mirror .m-device { font-weight: 700; }
  #mirror .m-layout { color: var(--accent); font-weight: 600; }
  #mirror .m-dim { color: var(--faint); font-size: 12px; }
  .tab-pills { display: flex; gap: 6px; flex-wrap: wrap; }
  .tab-pill {
    font-size: 11.5px; border-radius: 99px; padding: 2px 10px;
    border: 1px solid var(--edge); background: var(--card); color: var(--dim);
  }
  .tab-pill.active {
    border-color: var(--accent); background: var(--accent-soft); color: var(--text);
    font-weight: 600;
  }
  #mirror-ticker {
    margin-left: auto; display: flex; gap: 8px; align-items: center;
    overflow-x: auto; max-width: 100%; font-family: var(--mono); font-size: 11px;
  }
  .tick {
    display: inline-flex; gap: 6px; align-items: center; white-space: nowrap;
    background: var(--card); border: 1px solid var(--edge); border-radius: 8px;
    padding: 2px 8px; color: var(--dim);
  }
  .tick .k { font-size: 9.5px; text-transform: uppercase; letter-spacing: .06em; }
  .tick.action .k { color: var(--t-string); }
  .tick.value  .k { color: var(--t-number); }
  .tick .cid { color: var(--accent); cursor: pointer; text-decoration: underline dotted; }
  .tick .cid:hover { color: var(--text); }
  .tick .pl { color: var(--faint); max-width: 26ch; overflow: hidden; text-overflow: ellipsis; }
  /* ── layout ─────────────────────────────────────────── */
  main {
    flex: 1; display: grid; gap: 14px; padding: 14px 20px 20px;
    grid-template-columns: minmax(300px, 1fr) minmax(300px, 1fr) minmax(300px, 1fr) minmax(280px, 0.85fr);
    min-height: 0;
  }
  @media (max-width: 1400px) { main { grid-template-columns: 1fr 1fr; overflow: auto; } }
  @media (max-width: 1100px) { main { grid-template-columns: 1fr; overflow: auto; } }
  /* ── controls (device view) ─────────────────────────── */
  .ctl { padding: 9px 12px; }
  .ctl .card-head { gap: 6px; }
  .ctl-id { font-family: var(--mono); font-size: 12.5px; font-weight: 700; color: var(--text); }
  .ctl-val {
    font-family: var(--mono); font-size: 11px; color: var(--ok);
    max-width: 18ch; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }
  .ctl-val.unset { color: var(--faint); }
  section { display: flex; flex-direction: column; min-height: 0; }
  section > h2 {
    font-size: 11px; text-transform: uppercase; letter-spacing: 0.12em;
    color: var(--dim); margin-bottom: 8px; display: flex; align-items: center; gap: 8px;
  }
  section > h2 .count {
    background: var(--card); border: 1px solid var(--edge);
    border-radius: 99px; padding: 0 8px; font-size: 11px; color: var(--text);
  }
  .scroll { overflow-y: auto; min-height: 0; display: flex; flex-direction: column;
            gap: 10px; padding-right: 4px; }
  /* ── cards ──────────────────────────────────────────── */
  .card {
    background: var(--card); border: 1px solid var(--edge); border-radius: 12px;
    padding: 12px 14px; transition: box-shadow .5s, border-color .5s;
  }
  .card.flash { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft);
                transition: none; }
  .card.flash-ok { border-color: var(--ok); box-shadow: 0 0 0 3px #34d39933;
                   transition: none; }
  .card-head { display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap; }
  .cmd { font-family: var(--mono); font-weight: 700; font-size: 14px; color: var(--accent); }
  .feed-label { font-weight: 600; }
  .badge {
    font-size: 10px; text-transform: uppercase; letter-spacing: .06em;
    border-radius: 5px; padding: 1px 7px; border: 1px solid var(--edge); color: var(--dim);
  }
  .badge.broadcast { color: var(--t-number); border-color: #60a5fa44; }
  .badge.routed { color: var(--t-array); border-color: #fb923c44; }
  .badge.legacy { color: var(--warn); border-color: #fbbf2444; }
  .badge.gesture { color: var(--t-string); border-color: #f472b644; }
  .type-chip {
    font-family: var(--mono); font-size: 11px; border-radius: 5px; padding: 1px 7px;
    background: #0d1017;
  }
  .type-number { color: var(--t-number); } .type-boolean { color: var(--t-boolean); }
  .type-string { color: var(--t-string); } .type-object { color: var(--t-object); }
  .type-none { color: var(--t-none); }     .type-array { color: var(--t-array); }
  .type-json { color: var(--t-json); }     .type-native { color: var(--t-object); }
  .where { font-size: 11px; color: var(--faint); margin-left: auto; }
  .meta { font-size: 12px; color: var(--dim); margin-top: 6px;
          display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
  .meta code, pre.payload {
    font-family: var(--mono); font-size: 11.5px; color: var(--text);
  }
  pre.payload {
    margin-top: 8px; background: #0d1017; border: 1px solid var(--edge);
    border-radius: 8px; padding: 8px 10px; overflow-x: auto; white-space: pre;
  }
  pre.payload .tok { color: var(--t-object); font-weight: 700; }
  .tokens { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
  .last-fired { font-size: 11px; color: var(--faint); margin-top: 6px; }
  .last-fired b { color: var(--ok); font-weight: 600; }
  /* ── feed inputs ────────────────────────────────────── */
  .push-row { display: flex; gap: 8px; margin-top: 10px; align-items: center; }
  .push-row input[type=text], .push-row input[type=number], .push-row select,
  .push-row textarea {
    flex: 1; background: #0d1017; color: var(--text); border: 1px solid var(--edge);
    border-radius: 8px; padding: 6px 10px; font-family: var(--mono); font-size: 12px;
    min-width: 0;
  }
  .push-row textarea { resize: vertical; min-height: 34px; }
  .push-row input:focus, .push-row select:focus, .push-row textarea:focus {
    outline: none; border-color: var(--accent);
  }
  .switch { display: inline-flex; align-items: center; gap: 8px; flex: 1;
            font-family: var(--mono); font-size: 12px; color: var(--dim); }
  .range-wrap { flex: 1; display: flex; gap: 10px; align-items: center; }
  .range-wrap input[type=range] { flex: 1; accent-color: var(--accent); }
  .range-val { font-family: var(--mono); font-size: 12px; min-width: 48px; text-align: right; }
  .hint { font-size: 11px; color: var(--faint); margin-top: 5px; }
  .hint a { color: var(--accent); cursor: pointer; text-decoration: none; }
  /* ── wire log ───────────────────────────────────────── */
  #wire-controls { display: flex; gap: 8px; margin-bottom: 8px; }
  #wire-filter {
    flex: 1; background: var(--card); border: 1px solid var(--edge); color: var(--text);
    border-radius: 8px; padding: 5px 10px; font-size: 12px; font-family: var(--mono);
  }
  #wire { font-family: var(--mono); font-size: 11.5px; gap: 6px; }
  .frame { background: var(--card); border: 1px solid var(--edge); border-radius: 8px;
           padding: 6px 10px; overflow-x: auto; }
  .frame .fh { display: flex; gap: 8px; color: var(--faint); font-size: 10.5px;
               margin-bottom: 2px; align-items: center; }
  .frame .dir-in { color: var(--t-string); }   /* phone → computer */
  .frame .dir-out { color: var(--t-number); }  /* computer → phone */
  .frame pre { white-space: pre-wrap; word-break: break-all; color: var(--text); }
  /* ── empty / waiting states ─────────────────────────── */
  .empty {
    border: 1px dashed var(--edge); border-radius: 12px; padding: 26px 18px;
    text-align: center; color: var(--dim); font-size: 13px;
  }
  .empty .big { font-size: 15px; color: var(--text); font-weight: 600; margin-bottom: 6px; }
  .qr-note { margin-top: 10px; }
  .qr-note code {
    display: block; font-family: var(--mono); font-size: 11px; margin-top: 8px;
    background: #0d1017; border: 1px solid var(--edge); border-radius: 8px;
    padding: 8px; word-break: break-all; text-align: left;
  }
  .qr-card {
    margin: 16px auto 0; max-width: 280px; display: flex; flex-direction: column;
    align-items: center; gap: 10px; background: var(--panel);
    border: 1px solid var(--edge); border-radius: 14px; padding: 16px;
  }
  .qr-card-title { font-weight: 700; font-size: 13px; color: var(--text); }
  .qr-card svg { width: 200px; height: 200px; border-radius: 6px; }
  .qr-payload { width: 100%; display: flex; flex-direction: column; gap: 6px; align-items: stretch; }
  .qr-payload code {
    display: block; font-family: var(--mono); font-size: 10.5px;
    background: #0d1017; border: 1px solid var(--edge); border-radius: 8px;
    padding: 7px 8px; word-break: break-all; text-align: left; color: var(--dim);
  }
  #toast {
    position: fixed; bottom: 18px; left: 50%; transform: translateX(-50%);
    background: var(--card); border: 1px solid var(--edge); border-radius: 10px;
    padding: 9px 16px; font-size: 13px; opacity: 0; pointer-events: none;
    transition: opacity .25s; z-index: 10; max-width: 80vw;
  }
  #toast.show { opacity: 1; }
  #toast.err { border-color: var(--err); color: var(--err); }
</style>
</head>
<body>
<header>
  <div class="logo">
    <div class="logo-mark">⌁</div>
    <div>
      <h1>Layout Link · <span id="layout-name">…</span></h1>
      <div class="sub">the live, typed API of your layout</div>
    </div>
  </div>
  <div class="status">
    <span class="pill"><span class="dot" id="relay-dot"></span><span id="relay-label">connecting…</span></span>
    <span class="pill" id="peer-pill"><span class="dot" id="peer-dot"></span><span id="peer-label">no device yet</span></span>
    <a class="btn" href="/api/contract" download="contract.json">contract.json</a>
    <a class="btn" href="/api/layout" download="layout.json">layout.json</a>
    <a class="btn primary" href="/api/stub" download="bridge.py">⇩ typed server stub</a>
  </div>
</header>

<!-- Device Mirror: what the phone is doing right now, narrated by `studio.event`
     frames during a Studio Session. Hidden until the phone says hello. -->
<div id="mirror">
  <span class="m-title">Device Mirror</span>
  <span class="pill"><span class="dot" id="mirror-dot"></span><span class="m-device" id="mirror-device">—</span></span>
  <span class="m-layout" id="mirror-layout">no layout open</span>
  <span class="m-dim" id="mirror-meta"></span>
  <span class="tab-pills" id="mirror-tabs"></span>
  <span id="mirror-ticker"></span>
</div>

<main>
  <section id="sec-triggers">
    <h2>Triggers <span class="count" id="n-triggers">0</span>
        <span style="font-weight:400;text-transform:none;letter-spacing:0">— what your controls fire</span></h2>
    <div class="scroll" id="triggers"></div>
  </section>

  <section id="sec-feeds">
    <h2>Data feeds <span class="count" id="n-feeds">0</span>
        <span style="font-weight:400;text-transform:none;letter-spacing:0">— push values, watch the phone update</span></h2>
    <div class="scroll" id="feeds"></div>
  </section>

  <section id="sec-controls">
    <h2>Controls <span class="count" id="n-controls">0</span>
        <span style="font-weight:400;text-transform:none;letter-spacing:0">— every control on the device, wired or not</span></h2>
    <div class="scroll" id="controls"></div>
  </section>

  <section id="sec-wire">
    <h2>Live wire</h2>
    <div id="wire-controls">
      <input id="wire-filter" placeholder="filter frames…">
      <button class="btn" id="wire-pause">pause</button>
      <button class="btn" id="wire-clear">clear</button>
    </div>
    <div class="scroll" id="wire"></div>
  </section>
</main>

<div id="toast"></div>

<script>
"use strict";
const $ = (s, el=document) => el.querySelector(s);
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let paused = false, wireFilter = "";
const state = { contract: null, status: null, controls: [], values: {} };

function toast(msg, isErr) {
  const t = $("#toast");
  t.textContent = msg; t.className = isErr ? "show err" : "show";
  clearTimeout(t._h); t._h = setTimeout(() => t.className = "", 2600);
}

function typeChip(spec) {
  if (!spec) return "";
  const t = spec.type || "json";
  let txt = t;
  if (spec.enum) txt = "enum: " + spec.enum.slice(0, 4).join(" | ") + (spec.enum.length > 4 ? " | …" : "");
  else if (t === "number" && spec.min !== undefined && spec.max !== undefined)
    txt = `number ${spec.min}–${spec.max}` + (spec.step ? ` ·${spec.step}` : "");
  else if (spec.format) txt = t + " (" + spec.format + ")";
  else if (spec.shape) txt = "{" + Object.keys(spec.shape).join(", ") + "}";
  return `<span class="type-chip type-${esc(t)}" title="${esc(spec.note || "")}">${esc(txt)}</span>`;
}

function prettyPayload(p) {
  let s = esc(JSON.stringify(p, null, 1));
  return s.replace(/\{\{(\w+)\}\}/g, '<span class="tok">{{$1}}</span>')
          .replace(/\$value\.(\w+)/g, '<span class="tok">$value.$1</span>');
}

/* ── triggers ─────────────────────────────────────────── */
function renderTriggers(list) {
  const host = $("#triggers");
  $("#n-triggers").textContent = list.length;
  if (!list.length) {
    host.innerHTML = `<div class="empty"><div class="big">No triggers</div>
      This layout's controls don't fire any actions yet — add an
      <b>action</b> to a control in the editor and re-pull.</div>`;
    return;
  }
  host.innerHTML = list.map(t => {
    const srcs = t.sources.map(s =>
      `<span>${esc(s.label)} <span class="badge">${esc(s.type)}</span>` +
      (s.gesture === "long-press" ? ' <span class="badge gesture">long-press</span>' : "") +
      `</span>`).join(" · ");
    const toks = Object.entries(t.tokens || {}).map(([n, spec]) =>
      `<span class="type-chip type-${esc(spec.type)}" title="${esc(spec.description || spec.note || "")}">{{${esc(n)}}} : ${esc(spec.type === "native" ? "?" : spec.type)}${spec.enum ? " " + esc(spec.enum.join("|")) : ""}${spec.type === "number" && spec.min !== undefined ? ` ${spec.min}–${spec.max}` : ""}</span>`).join("");
    return `<div class="card" id="trig-${esc(t.command)}">
      <div class="card-head">
        <span class="cmd">${esc(t.command)}</span>
        <span class="badge ${esc(t.wire.transport)}">${esc(t.wire.transport)}</span>
        <span class="badge">${esc(t.wire.mode)}</span>
        <span class="where">${esc(t.sources[0]?.where || "")}</span>
      </div>
      <div class="meta">${srcs}</div>
      ${t.payloadTemplate ? `<pre class="payload">${prettyPayload(t.payloadTemplate)}</pre>` : ""}
      ${toks ? `<div class="tokens">${toks}</div>` : ""}
      <div class="last-fired" id="fired-${esc(t.command)}">never fired — tap it on the phone</div>
    </div>`;
  }).join("");
}

/* ── feeds ────────────────────────────────────────────── */
function inputFor(f, i) {
  const e = f.expects || {}, id = `in-${i}`;
  if (e.enum)
    return `<select id="${id}">${e.enum.map(o => `<option>${esc(o)}</option>`).join("")}</select>`;
  if (e.type === "boolean")
    return `<label class="switch"><input type="checkbox" id="${id}"> true / false</label>`;
  if (e.type === "number") {
    if (e.min !== undefined && e.max !== undefined) {
      const mid = (e.min + e.max) / 2, step = e.step || (e.max - e.min <= 2 ? 0.01 : 1);
      return `<span class="range-wrap">
        <input type="range" id="${id}" min="${e.min}" max="${e.max}" step="${step}" value="${mid}"
               oninput="document.getElementById('${id}v').textContent=this.value">
        <span class="range-val" id="${id}v">${mid}</span></span>`;
    }
    return `<input type="number" id="${id}" placeholder="42">`;
  }
  if (e.type === "string")
    return `<input type="text" id="${id}" placeholder="${esc(e.format || "text")}">`;
  return `<textarea id="${id}" rows="1" placeholder='JSON — e.g. ${esc(JSON.stringify(sampleFor(e)))}'></textarea>`;
}
function sampleFor(e) {
  if (e.enum) return e.enum[0];
  switch (e.type) {
    case "number": return e.min !== undefined && e.max !== undefined ? (e.min + e.max) / 2 : 42;
    case "boolean": return true;
    case "string": return "hello";
    case "array": return [];
    default: return {};
  }
}

function renderFeeds(list) {
  const host = $("#feeds");
  $("#n-feeds").textContent = list.length;
  if (!list.length) {
    host.innerHTML = `<div class="empty"><div class="big">No data feeds</div>
      No control listens for data yet. You can still drive every control by id from
      the <b>Controls</b> section — add a <b>sync</b> binding in the editor and
      re-pull to give this layout a wire contract.</div>`;
    return;
  }
  host.innerHTML = list.map((f, i) => `<div class="card" id="feed-${esc(f.id)}">
      <div class="card-head">
        <span class="feed-label">${esc(f.label)}</span>
        <span class="badge">${esc(f.type)}</span>
        ${typeChip(f.expects)}
        <span class="where">${esc(f.where)}</span>
      </div>
      <div class="meta">
        <code>id: ${esc(f.id)}</code>
        ${Object.keys(f.filter).length ? `<code>filter: ${esc(JSON.stringify(f.filter))}</code>` : ""}
        ${f.valuePath ? `<code>valuePath: ${esc(f.valuePath)}</code>` : "<code>whole payload</code>"}
      </div>
      <div class="push-row">${inputFor(f, i)}
        <button class="btn primary" onclick="pushFeed(${i})">push</button>
      </div>
      <div class="hint">wire frame: <a onclick="pushExample(${i})" title="send this now">
        ${esc(JSON.stringify(f.example))}</a></div>
    </div>`).join("");
}

/* ── controls (the device view) ────────────────────────────
   Triggers/Feeds are the wire contract — a layout with no `sync` bindings has
   nothing there. This section lists EVERY control and drives it by id over the
   routed `set-control-state` verb, which is what makes a demo-style layout live. */
function controlInput(c, i) {
  const id = `ctl-in-${i}`, v = state.values[c.id];
  if (c.expects === "enum" && c.options)
    return `<select id="${id}">${c.options.map(o =>
      `<option${String(v) === String(o) ? " selected" : ""}>${esc(o)}</option>`).join("")}</select>`;
  if (c.expects === "boolean")
    return `<label class="switch"><input type="checkbox" id="${id}"${v === true ? " checked" : ""}> on / off</label>`;
  if (c.expects === "number") {
    if (c.min !== undefined && c.min !== null && c.max !== undefined && c.max !== null) {
      const val = typeof v === "number" ? v : (c.min + c.max) / 2;
      const step = c.step || (c.max - c.min <= 2 ? 0.01 : 1);
      return `<span class="range-wrap">
        <input type="range" id="${id}" min="${c.min}" max="${c.max}" step="${step}" value="${val}"
               oninput="document.getElementById('${id}v').textContent=this.value">
        <span class="range-val" id="${id}v">${val}</span></span>`;
    }
    return `<input type="number" id="${id}" value="${typeof v === "number" ? v : ""}" placeholder="42">`;
  }
  if (c.expects === "array" || c.expects === "json")
    return `<textarea id="${id}" rows="1" placeholder='${c.expects === "array" ? "[…]" : "{…}"}'></textarea>`;
  return `<input type="text" id="${id}" value="${v === undefined || v === null ? "" : esc(String(v))}" placeholder="text">`;
}

function valueText(v) {
  if (v === undefined || v === null) return "unset";
  return typeof v === "object" ? JSON.stringify(v) : String(v);
}

function renderControls(list) {
  const host = $("#controls");
  $("#n-controls").textContent = list.length;
  if (!list.length) {
    host.innerHTML = `<div class="empty"><div class="big">No controls</div>
      Waiting for a layout from the phone.</div>`;
    return;
  }
  host.innerHTML = list.map((c, i) => {
    const v = state.values[c.id];
    return `<div class="card ctl" id="ctl-${esc(c.id)}">
      <div class="card-head">
        <span class="ctl-id">${esc(c.id)}</span>
        <span class="badge">${esc(c.type)}</span>
        <span class="ctl-val${v === undefined || v === null ? " unset" : ""}" id="ctlv-${esc(c.id)}">${esc(valueText(v))}</span>
        <span class="where">${esc(c.where)}</span>
      </div>
      <div class="push-row">${controlInput(c, i)}
        <button class="btn primary" onclick="setControl(${i})">set</button>
      </div>
    </div>`;
  }).join("");
}

function readControlInput(c, i) {
  const el = document.getElementById(`ctl-in-${i}`);
  if (!el) return null;
  if (c.expects === "enum") return el.value;
  if (c.expects === "boolean") return el.checked;
  if (c.expects === "number") return Number(el.value);
  if (c.expects === "array" || c.expects === "json") {
    if (!el.value.trim()) return c.expects === "array" ? [] : {};
    try { return JSON.parse(el.value); }
    catch { toast("that isn't valid JSON", true); throw new Error("bad json"); }
  }
  return el.value;
}

async function setControl(i) {
  const c = state.controls[i];
  try {
    const value = readControlInput(c, i);
    const res = await api("/api/set", { id: c.id, value });
    if ((res.skipped || []).includes(c.id)) {
      toast(`the device skipped '${c.id}' — wrong value shape for a ${c.type}?`, true);
      flash("ctl-" + c.id);
      return;
    }
    applyControlValue(c.id, value);
    flash("ctl-" + c.id, "flash-ok");
  } catch (err) { if (err.message !== "bad json") toast("set failed: " + err.message, true); }
}

/* Repaint one row's current value — from our own push, or from a mirrored
   `value` event when the user moves the control on the phone. */
function applyControlValue(id, value) {
  state.values[id] = value;
  const el = document.getElementById("ctlv-" + id);
  if (!el) return;
  el.textContent = valueText(value);
  el.classList.toggle("unset", value === undefined || value === null);
}

async function refreshControls() {
  try {
    const r = await fetch("/api/controls");
    if (!r.ok) return;
    const d = await r.json();
    state.controls = d.controls || [];
    state.values = d.values || {};
    renderControls(state.controls);
  } catch { /* server restarting */ }
}

function readInput(f, i) {
  const e = f.expects || {}, el = document.getElementById(`in-${i}`);
  if (!el) return sampleFor(e);
  if (e.enum) return el.value;
  if (e.type === "boolean") return el.checked;
  if (e.type === "number") return Number(el.value);
  if (e.type === "string") return el.value;
  try { return el.value.trim() ? JSON.parse(el.value) : sampleFor(e); }
  catch { toast("that isn't valid JSON", true); throw new Error("bad json"); }
}

async function api(path, body) {
  const r = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" },
                                body: JSON.stringify(body) });
  const j = await r.json().catch(() => ({}));
  if (!r.ok || j.error) throw new Error(j.error || r.statusText);
  return j;
}

async function pushFeed(i) {
  const f = state.contract.feeds[i];
  try {
    await api("/api/push", { id: f.id, value: readInput(f, i) });
    flash("feed-" + f.id, "flash-ok");
  } catch (err) { toast("push failed: " + err.message, true); }
}
async function pushExample(i) {
  const f = state.contract.feeds[i];
  try { await api("/api/push", { id: f.id, value: sampleFor(f.expects || {}) });
        flash("feed-" + f.id, "flash-ok"); }
  catch (err) { toast("push failed: " + err.message, true); }
}

function flash(id, cls) {
  const el = document.getElementById(id);
  if (!el) return;
  el.classList.add(cls || "flash");
  setTimeout(() => el.classList.remove(cls || "flash"), 700);
}

/* ── wire log ─────────────────────────────────────────── */
function addFrame(evt) {
  if (paused) return;
  const wire = $("#wire");
  const txt = JSON.stringify(evt.data);
  if (wireFilter && !txt.toLowerCase().includes(wireFilter)) return;
  const div = document.createElement("div");
  div.className = "frame";
  const dir = evt.kind === "push" ? '<span class="dir-out">→ phone</span>'
                                  : '<span class="dir-in">← phone</span>';
  const label = evt.command || (evt.kind === "studio" ? "studio · " + evt.event : "");
  const tag = label ? ` <span class="cmd" style="font-size:11px">${esc(label)}</span>` : "";
  div.innerHTML = `<div class="fh">${dir}${tag}<span style="margin-left:auto">${new Date(evt.ts * 1000).toLocaleTimeString()}</span></div>
                   <pre>${esc(JSON.stringify(evt.data, null, 1))}</pre>`;
  wire.prepend(div);
  while (wire.children.length > 200) wire.lastChild.remove();
}

/* ── device mirror ────────────────────────────────────────
   The phone narrates its own navigation over `studio.event`; this paints it and
   lets you jump from a mirrored control id straight to that control's feed input,
   which is the "respond" half of the loop. */
const mirror = { tabs: [], tab: null, fires: new Map() };

function renderMirror(m) {
  if (!m) return;
  const host = $("#mirror");
  const live = !!(m.device || m.layout);
  host.classList.toggle("on", live);
  if (!live) return;
  $("#mirror-dot").className = "dot " + (m.alive ? "on" : "wait");
  $("#mirror-device").textContent = m.device || "phone";
  $("#mirror-layout").textContent = m.layout || "no layout open";
  const bits = [];
  if (m.appVersion) bits.push("v" + m.appVersion);
  if (m.controls != null) bits.push(m.controls + " controls");
  // A mirror primed from the routed pull is not "ended" — it just hasn't heard
  // the phone narrate anything yet. Only an actual `bye` retires the session.
  if (!m.alive) bits.push(m.lastEvent === "bye" ? "session ended" : "awaiting events");
  $("#mirror-meta").textContent = bits.join(" · ");
  mirror.tabs = m.tabs || [];
  mirror.tab = m.tab;
  renderMirrorTabs();
}

function renderMirrorTabs() {
  $("#mirror-tabs").innerHTML = mirror.tabs.map(t =>
    `<span class="tab-pill${t.id === mirror.tab ? " active" : ""}">${esc(t.title || t.id)}</span>`
  ).join("");
}

/* One line in the live ticker of what the user touched. */
function addTick(kind, controlId, detail) {
  const host = $("#mirror-ticker");
  const div = document.createElement("span");
  div.className = "tick " + kind;
  div.innerHTML = `<span class="k">${esc(kind)}</span>` +
    `<span class="cid" onclick="revealFeed('${esc(controlId)}')" title="jump to this control's feed input">${esc(controlId)}</span>` +
    `<span class="pl">${esc(detail)}</span>`;
  host.prepend(div);
  while (host.children.length > 12) host.lastChild.remove();
}

/* Click a mirrored control id -> scroll its feed card into view and focus the
   typed input, so answering what the phone just did is one click away. */
function revealFeed(id) {
  const card = document.getElementById("feed-" + id);
  if (!card) { toast("no data feed for '" + id + "' in this contract"); return; }
  card.scrollIntoView({ behavior: "smooth", block: "center" });
  flash("feed-" + id);
  const i = (state.contract && state.contract.feeds || []).findIndex(f => f.id === id);
  const input = i >= 0 && document.getElementById("in-" + i);
  if (input) input.focus();
}

/* A mirrored `action` flashes its trigger card immediately — usually before the
   phone's own action frame reaches us through the relay. Remember what we flashed
   so the real frame arriving a moment later doesn't double-count the fire. */
function noteMirrorFire(command, data) {
  const key = command + " | " + JSON.stringify(data);
  mirror.fires.set(key, Date.now());
  return key;
}
function wasMirrorFire(command, data) {
  const key = command + " | " + JSON.stringify(data);
  const at = mirror.fires.get(key);
  if (at === undefined || Date.now() - at > 2000) return false;
  mirror.fires.delete(key);
  return true;
}

function markFired(command, data) {
  const el = document.getElementById("fired-" + command);
  if (el) {
    el._n = (el._n || 0) + 1;
    el.innerHTML = `<b>fired ×${el._n}</b> · ${new Date().toLocaleTimeString()} · <code style="font-family:var(--mono)">${esc(JSON.stringify(data))}</code>`;
  }
  flash("trig-" + command);
}

function handleStudio(evt) {
  const d = evt.data || {};
  if (evt.event === "tab") { mirror.tab = d.tab; renderMirrorTabs(); }
  if (evt.event === "action") {
    const payload = d.payload || {};
    addTick("action", d.control, JSON.stringify(payload));
    const command = payload.msg_type || payload.type;
    if (command) { noteMirrorFire(command, payload); markFired(command, payload); }
  }
  if (evt.event === "value") {
    addTick("value", d.control, JSON.stringify(d.value));
    applyControlValue(d.control, d.value);      // the phone moved it — repaint the row
  }
  // hello / layout / layout-closed / bye all land in `mirror` server-side, so one
  // status fetch repaints the panel. Activity events (action/value) are already
  // painted above — don't spend a round trip on each one.
  if (["hello", "layout", "layout-closed", "bye"].includes(evt.event)) refresh();
}

/* ── status + contract loading ────────────────────────── */
function renderStatus(s) {
  state.status = s;
  renderMirror(s.mirror);
  const rd = $("#relay-dot"), rl = $("#relay-label");
  rd.className = "dot " + (s.connected ? "on" : "wait");
  const where = s.kind === "local"
    ? `local relay :${s.port || ""} · ch ${s.channel}`
    : `${s.url || "relay"} · ch ${s.channel}`;
  rl.textContent = s.connected ? where
    : s.connectError ? `connecting… (${s.connectError})` : `connecting… ${where}`;
  const pd = $("#peer-dot"), pl = $("#peer-label");
  if (s.peers && s.peers.length) {
    pd.className = "dot on";
    pl.textContent = s.peers.join(", ");
  } else {
    pd.className = "dot wait";
    pl.textContent = "waiting for the phone…";
  }
}

/* ── app-direct (MQTT / HTTP / sensor — the app serves these, not a server) ── */
function renderAppDirect(list) {
  if (!list || !list.length) return;
  const host = $("#feeds");
  const rows = list.map(a => `<div class="card">
    <div class="card-head">
      <span class="feed-label">${esc(a.label)}</span>
      <span class="badge">${esc(a.transport)}</span>
      <span class="badge">${a.direction === "out" ? "→ out" : "← in"}</span>
      <span class="where">${esc(a.where)}</span>
    </div>
    <div class="meta"><code>id: ${esc(a.id)}</code>${
      a.address ? `<code>${esc(a.transport)}: ${esc(a.address)}</code>` : ""}</div>
    <div class="hint">app-direct — the phone speaks this itself; no server serves it</div>
  </div>`).join("");
  host.insertAdjacentHTML("beforeend",
    `<div class="hint" style="margin:10px 2px 4px">App-direct (MQTT / HTTP / sensor) · ${list.length}</div>` + rows);
}

function renderContract(c) {
  state.contract = c;
  $("#layout-name").textContent = c.layout.name;
  document.title = "Layout Link · " + c.layout.name;
  renderTriggers(c.triggers);
  renderFeeds(c.feeds);
  renderAppDirect(c.appDirect);
  refreshControls();
}

/* ── pairing QR (inline SVG, drawn from the module matrix the server sends —
   the encoding itself is server-side Python; this just paints rects) ───── */
function qrSvg(matrix, moduleSize, quiet) {
  moduleSize = moduleSize || 6; quiet = quiet === undefined ? 4 : quiet;
  const n = matrix.length, total = n + quiet * 2, px = total * moduleSize;
  let rects = "";
  for (let r = 0; r < n; r++)
    for (let c = 0; c < n; c++)
      if (matrix[r][c])
        rects += `<rect x="${(c + quiet) * moduleSize}" y="${(r + quiet) * moduleSize}" width="${moduleSize}" height="${moduleSize}"/>`;
  // A white backing rect under the whole viewBox (module area + quiet zone) —
  // a scanner needs that light quiet zone regardless of the page's own theme.
  return `<svg viewBox="0 0 ${px} ${px}" width="${px}" height="${px}" xmlns="http://www.w3.org/2000/svg">` +
         `<rect width="${px}" height="${px}" fill="#fff"/><g fill="#000">${rects}</g></svg>`;
}

function copyQrPayload() {
  const text = state.status && state.status.qr;
  if (!text) return;
  navigator.clipboard.writeText(text)
    .then(() => toast("pairing JSON copied"))
    .catch(() => toast("copy failed — select the text manually", true));
}

function renderWaiting(qr, qrMatrix) {
  $("#layout-name").textContent = "waiting…";
  $("#triggers").innerHTML = `<div class="empty">
    <div class="big">📱 Pair your phone</div>
    In CAR-TER, start a <b>Studio Session</b> (Settings → Studio Session → Open Scanner) and scan the code below —
    the layout will appear here the moment it connects.
    ${qrMatrix ? `<div class="qr-card">
        <div class="qr-card-title">Scan with CAR-TER to pair</div>
        ${qrSvg(qrMatrix)}
        <div class="qr-payload">
          <code>${esc(qr)}</code>
          <button class="btn" onclick="copyQrPayload()">⧉ copy pairing JSON</button>
        </div>
      </div>` : qr ? `<div class="qr-note">pairing JSON:<code>${esc(qr)}</code></div>` : ""}
  </div>`;
  $("#feeds").innerHTML = "";
  renderControls([]);
}

async function refresh() {
  try {
    const s = await (await fetch("/api/status")).json();
    renderStatus(s);
    if (s.hasLayout && !state.contract) {
      renderContract(await (await fetch("/api/contract")).json());
    } else if (!s.hasLayout && !state.contract) {
      renderWaiting(s.qr, s.qrMatrix);
    }
  } catch { /* server restarting */ }
}

/* ── SSE ──────────────────────────────────────────────── */
const es = new EventSource("/events");
es.onmessage = m => {
  const evt = JSON.parse(m.data);
  if (evt.kind === "contract") { state.contract = null; refresh(); return; }
  if (evt.kind === "controls") {
    state.values = (evt.data || {}).values || {};
    renderControls(state.controls);
    return;
  }
  if (evt.kind === "studio") { handleStudio(evt); addFrame(evt); return; }
  if (evt.kind === "trigger") {
    // Skip if the mirror already flashed this exact fire moments ago.
    if (!wasMirrorFire(evt.command, evt.data)) markFired(evt.command, evt.data);
  }
  addFrame(evt);
};

$("#wire-pause").onclick = e => { paused = !paused; e.target.textContent = paused ? "resume" : "pause"; };
$("#wire-clear").onclick = () => $("#wire").innerHTML = "";
$("#wire-filter").oninput = e => wireFilter = e.target.value.toLowerCase();

refresh();
setInterval(refresh, 4000);
</script>
</body>
</html>
"""
