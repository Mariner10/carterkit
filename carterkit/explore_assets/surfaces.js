/* Surfaces section: HTML/CSS approximations ("preview") of the widget, Island and
   Lock Screen scenes, sized to real points. Data comes from /api/surfaces. */
(function () {
  const esc = s => String(s).replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
  function fmt(v) {
    if (v === null || v === undefined) return "—";
    if (typeof v === "number") return Number.isInteger(v) ? String(v) : v.toFixed(1);
    if (typeof v === "boolean") return v ? "On" : "Off";
    return String(v);
  }
  function frac(t) {
    const lo = Number(t.min ?? 0), hi = Number(t.max ?? 100), v = Number(t.value);
    if (!isFinite(v) || hi === lo) return 0;
    return Math.max(0, Math.min(1, (v - lo) / (hi - lo)));
  }
  function tile(t) {
    const k = t.tile, cls = "sf-tile" + (t.sample ? " sample" : "");
    const label = t.label ? `<span class="l">${esc(t.label)}</span>` : "";
    const style = t.span ? ` style="flex-grow:${Number(t.span) || 1}"` : "";
    let body;
    if (k === "gauge" || k === "ring")
      body = `<div class="sf-ring" style="background:conic-gradient(#0a84ff ${Math.round(frac(t) * 100)}%,#3a3a3c 0)">` +
             `<span style="background:#1c1c1e;border-radius:50%;width:34px;height:34px;display:grid;place-items:center">${esc(fmt(t.value))}</span></div>`;
    else if (k === "bar") body = `<span class="v">${esc(fmt(t.value))}</span><div class="sf-bar"><i style="width:${frac(t) * 100}%"></i></div>`;
    else if (k === "light") body = `<span class="sf-dot" style="background:${t.value ? "#30d158" : "#8e8e93"}"></span>`;
    else if (k === "spacer") body = "";
    else if (k === "icon") body = `<span class="v">◎</span>`;
    else if (k === "freshness") body = `<span class="v" style="font-size:11px;color:#30d158">LIVE</span>`;
    else if (k === "timer") body = `<span class="v">${esc(fmt(t.value ?? "0:00"))}</span>`;
    else if (k === "sparkline") body = `<span class="v">▁▃▅▆▇</span>`;
    else if (k === "toggle" || k === "button" || k === "step" || k === "open")
      body = `<span class="v" style="font-size:12px;border:1px solid #636366;border-radius:8px;padding:2px 8px">${k === "step" ? "− +" : esc(t.label || k)}</span>`;
    else body = `<span class="v">${esc(fmt(t.value ?? t.label ?? ""))}</span>`;
    return `<div class="${cls}"${style}>${body}${["value", "text"].includes(k) || !t.control ? "" : label}</div>`;
  }
  const rows = rs => (rs || []).map(r => `<div class="sf-row">${r.map(tile).join("")}</div>`).join("");
  function box(s, inner) {
    const kind = /^compact|^expanded/.test(s.name) ? "island" : s.name === "lockScreen" ? "lockScreen" : "";
    return `<div class="sf-item"><div class="sf-box ${kind}" style="width:${s.width}px;height:${s.height}px">${inner}</div>` +
           `<div class="sf-cap"><b>${esc(s.label)}</b> · ${s.width}×${s.height} pt · preview</div></div>`;
  }
  function one(s) {
    if (s.regions) {
      const r = s.regions;
      return box(s, `<div class="sf-exp">${rows(r.leading)}${rows(r.center)}${rows(r.trailing)}</div>` + rows(s.rows));
    }
    if (s.tile) return box(s, `<div class="sf-row">${tile(s.tile)}</div>`);
    return box(s, rows(s.rows));
  }
  window.refreshSurfaces = async function () {
    const host = document.getElementById("surfaces");
    if (!host) return;
    try {
      const d = await (await fetch("/api/surfaces")).json();
      host.innerHTML = d.hint ? `<div class="sf-hint">${esc(d.hint)}</div>`
        : `<div class="sf-wrap">${d.surfaces.map(one).join("")}</div>`;
    } catch (e) { host.innerHTML = `<div class="sf-hint">surfaces unavailable</div>`; }
  };
  document.addEventListener("DOMContentLoaded", () => window.refreshSurfaces());
})();
