// Draws the list from data.json. Text from GitHub and the forum is only ever set with textContent.

// The filters. To add one, add a line here. `key` is the field in data.json (text or a list),
// `options` returns { value: label } from data.json. A filter only shows when it would narrow the list,
// unless it has `always: true` (then options with no entries show greyed out).
const FACETS = [
  { key: "type", label: "Type", options: (d) => d.types, always: true },
  { key: "category", label: "Category", options: (d) => d.categories, swatch: true },
  { key: "krita", label: "Krita version", options: (d) => labels(d.krita, (v) => `Krita ${v}`) },
  { key: "os", label: "Tested on", options: (d) => labels(d.systems) },
];

// Icons from Lucide (ISC license), except krita from Simple Icons (CC0). Copied from their SVG files.
const ICONS = {
  download: { stroke: true, d: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/>' },
  github: { stroke: true, d: '<path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/>' },
  plug: { stroke: true, d: '<path d="M12 22v-5"/><path d="M9 8V2"/><path d="M15 8V2"/><path d="M18 8v5a4 4 0 0 1-4 4h-4a4 4 0 0 1-4-4V8Z"/>' },
  palette: { stroke: true, d: '<circle cx="13.5" cy="6.5" r=".5" fill="currentColor"/><circle cx="17.5" cy="10.5" r=".5" fill="currentColor"/><circle cx="8.5" cy="7.5" r=".5" fill="currentColor"/><circle cx="6.5" cy="12.5" r=".5" fill="currentColor"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z"/>' },
  brush: { stroke: true, d: '<path d="m9.06 11.9 8.07-8.06a2.85 2.85 0 1 1 4.03 4.03l-8.06 8.08"/><path d="M7.07 14.94c-1.66 0-3 1.35-3 3.02 0 1.33-2.5 1.52-2 2.02 1.08 1.1 2.49 2.02 4 2.02 2.2 0 4-1.8 4-4.04a3.01 3.01 0 0 0-3-3.02z"/>' },
  wrench: { stroke: true, d: '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>' },
  package: { stroke: true, d: '<path d="M11 21.73a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73z"/><path d="M12 22V12"/><path d="m3.3 7 7.703 4.734a2 2 0 0 0 1.994 0L20.7 7"/><path d="m7.5 4.27 9 5.15"/>' },
  tag: { stroke: true, d: '<path d="M12.586 2.586A2 2 0 0 0 11.172 2H4a2 2 0 0 0-2 2v7.172a2 2 0 0 0 .586 1.414l8.704 8.704a2.426 2.426 0 0 0 3.42 0l6.58-6.58a2.426 2.426 0 0 0 0-3.42z"/><circle cx="7.5" cy="7.5" r=".5" fill="currentColor"/>' },
  scale: { stroke: true, d: '<path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="M7 21h10"/><path d="M12 3v18"/><path d="M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"/>' },
  star: { stroke: true, d: '<path d="M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.123 2.123 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 .294.904l-3.736 3.638a2.123 2.123 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.122 2.122 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.122 2.122 0 0 0-.611-1.879L2.16 9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.122 2.122 0 0 0 1.597-1.16z"/>' },
  calendar: { stroke: true, d: '<path d="M8 2v4"/><path d="M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/>' },
  monitor: { stroke: true, d: '<rect width="20" height="14" x="2" y="3" rx="2"/><line x1="8" x2="16" y1="21" y2="21"/><line x1="12" x2="12" y1="17" y2="21"/>' },
  flag: { stroke: true, d: '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" x2="4" y1="22" y2="15"/>' },
  pencil: { stroke: true, d: '<path d="M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z"/><path d="m15 5 4 4"/>' },
  krita: { stroke: false, d: '<path d="M.652.76a.625.625 0 00-.5.246c-.352.448-.035.898.362 1.262.206.189 1.77 1.794 3.428 3.527a11.054 11.054 0 011.815-1.983C3.667 2.515 1.694 1.266 1.461 1.1 1.201.914.917.762.652.76zm5.105 3.052c1.848 1.148 3.786 2.332 4.693 2.84 1.469.821 3.758 2.684 4.092 4.434.535.466 2.182 1.916 2.596 2.413.698-.211 1.518.133 2.06 1.12.866 1.583.227 3.747-1.968 4.988a5.42 5.42 0 01-.296.267l.296-.267c1.14-1.468-.714-2.44-1.175-3.864a2.06 2.06 0 01-.11-.78c-.533-.282-2.11-1.452-2.795-1.965-1.801.16-4.207-1.773-5.35-3.08-.7-.802-2.32-2.517-3.858-4.123a11.052 11.052 0 00-2.046 6.393A11.052 11.052 0 1012.948 1.136c-2.64.004-5.19.954-7.19 2.676zm8.71 7.552c-.515.126-.968.831-1.118 1.306-.038.115-.04.303.066.342.802.592 1.556 1.168 2.4 1.7.162-.393.746-.963 1.096-1.2zm-11.53 1.639c.812 1.898 5.798 7.17 12.06 2.695a2.07 2.07 0 00.114.715c.46 1.42 2.36 2.427 1.238 3.89-2.135 1.364-5 1.201-6.989.528-3.558-1.204-5.914-4.332-6.424-7.828zm13.782.7a.771.771 0 00-.065.049c-.004.003-.008.008-.011.008.003-.003.007-.008.01-.008.024-.015.044-.034.066-.048z"/>' },
};

const $ = (id) => document.getElementById(id);
const state = { q: "", view: "list", sort: "name", filters: Object.fromEntries(FACETS.map((f) => [f.key, new Set()])) };
let data;

function labels(values = [], format = (v) => v) {
  return Object.fromEntries(values.map((v) => [v, format(v)]));
}

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === "text") node.textContent = v;
    else if (k === "style") node.style.cssText = v;
    else node.setAttribute(k, v);
  }
  node.append(...children.filter((c) => c != null && c !== false && c !== ""));
  return node;
}

const swatch = (cat) => el("span", { class: "swatch", style: `--sw: var(--${cat})`, "aria-hidden": "true" });
const valuesOf = (entry, key) => [].concat(entry[key] ?? []);

const TYPE_ICONS = { plugin: "plug", theme: "palette", brushes: "brush", tool: "wrench", resource: "package" };

const STALE_YEARS = 2; // entries not updated for this long get a note

// "Not updated since 2022" when the entry's last update is older than STALE_YEARS before the last build.
function staleSince(entry) {
  if (!entry.updated || entry.archived) return null;
  const limit = new Date(data.generated + "T00:00:00");
  limit.setFullYear(limit.getFullYear() - STALE_YEARS);
  return new Date(entry.updated + "T00:00:00") < limit ? entry.updated.slice(0, 4) : null;
}

const SORTS = {
  name: (a, b) => a.name.localeCompare(b.name),
  updated: (a, b) => (b.updated || "").localeCompare(a.updated || ""),
  stars: (a, b) => (b.stars ?? -1) - (a.stars ?? -1), // entries without stars (forum only) go last
};

function formatDate(iso) {
  return new Date(iso + "T00:00:00").toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

// --- one entry ---------------------------------------------------------------

// GIFs and videos show their first frame until clicked, so nothing moves on its own.
function thumb(entry) {
  const style = `--sw: var(--${entry.category[0]})`;
  if (!entry.image) return el("div", { class: "thumb", style, "aria-hidden": "true" });
  if (entry.video) return videoThumb(entry, style);

  const img = el("img", { src: entry.image, alt: "", loading: "lazy", referrerpolicy: "no-referrer" });
  img.addEventListener("error", () => img.remove());
  if (!/\.gif($|\?)/i.test(entry.image)) return el("div", { class: "thumb", style }, img);

  const button = el("button", { class: "thumb", style, type: "button", "aria-label": `Play preview of ${entry.name}` });
  const still = el("canvas", { "aria-hidden": "true" });
  const label = el("span", { class: "play", text: "Play" });
  const probe = new Image();
  probe.referrerPolicy = "no-referrer";
  probe.onload = () => {
    still.width = probe.naturalWidth;
    still.height = probe.naturalHeight;
    still.getContext("2d").drawImage(probe, 0, 0);
  };
  probe.src = entry.image;
  button.append(still, label);
  button.addEventListener("click", () => {
    const playing = button.contains(img);
    button.replaceChildren(playing ? still : img, label);
    label.textContent = playing ? "Play" : "Stop";
    button.setAttribute("aria-label", `${playing ? "Play" : "Stop"} preview of ${entry.name}`);
  });
  return button;
}

function videoThumb(entry, style) {
  // #t=0.1 makes browsers show a real first frame instead of a blank box
  const video = el("video", { src: `${entry.image}#t=0.1`, preload: "metadata", playsinline: "", loop: "", "aria-hidden": "true" });
  video.muted = true;
  const label = el("span", { class: "play", text: "Play" });
  const button = el("button", { class: "thumb", style, type: "button", "aria-label": `Play preview of ${entry.name}` }, video, label);
  button.addEventListener("click", () => {
    const start = video.paused;
    if (start) video.play().catch(() => {}); else video.pause();
    label.textContent = start ? "Stop" : "Play";
    button.setAttribute("aria-label", `${start ? "Stop" : "Play"} preview of ${entry.name}`);
  });
  return button;
}

// Icon plus value; `meaning` is the hover text and what screen readers say.
// "minor" chips are left out of the grid view to keep cards short.
function chip(iconName, value, meaning, cls = "", tag = "li") {
  return el(tag, { class: `chip ${cls}`.trim(), title: meaning }, icon(iconName),
    el("span", { class: "visually-hidden", text: `${meaning}: ` }), el("span", { text: value }));
}

function chips(entry) {
  const typeName = entry.type[0].toUpperCase() + entry.type.slice(1);
  return el("ul", { class: "chips", "aria-label": "Details" },
    ...entry.category.map((c) => el("li", { class: "chip cat", title: "Category" }, swatch(c), data.categories[c] || c)),
    chip(TYPE_ICONS[entry.type] || "package", typeName, "Type"),
    entry.license && chip("scale", entry.license, "License", "minor"),
    entry.stars != null && chip("star", String(entry.stars), "GitHub stars", "minor"),
    entry.krita && chip("krita", entry.krita.join(", "), "Tested in Krita", "minor"),
    entry.os && chip("monitor", entry.os.join(", "), "Tested on", "minor"),
    entry.min_krita && chip("krita", `Needs ${entry.min_krita}+`, "Minimum Krita version"),
    entry.updated && chip("calendar", formatDate(entry.updated), "Last updated", "minor"),
    entry.archived && el("li", { class: "chip warn", text: "Archived" }),
    staleSince(entry) && el("li", { class: "chip stale", title: `No changes for over ${STALE_YEARS} years. It may still work.`,
      text: `Not updated since ${staleSince(entry)}` }),
  );
}

function icon(name) {
  const { stroke, d } = ICONS[name];
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("class", "icon");
  if (stroke) {
    for (const [k, v] of Object.entries({ fill: "none", stroke: "currentColor", "stroke-width": 2, "stroke-linecap": "round", "stroke-linejoin": "round" })) svg.setAttribute(k, v);
  } else {
    svg.setAttribute("fill", "currentColor");
  }
  svg.innerHTML = d; // fixed icon markup from ICONS, never data from entries
  return svg;
}

function link(cls, href, iconName, label, title) {
  return el("a", { class: cls, href, title: title || label }, icon(iconName), el("span", { class: "label", text: label }));
}

// The flag button: opens a GitHub issue form with this entry filled in.
// The GitHub repo, from the address the site is served from, so links follow a move or a fork:
// owner.github.io/repo -> github.com/owner/repo, and owner.github.io -> github.com/owner/owner.github.io.
const REPO = (() => {
  const m = location.hostname.match(/^([\w-]+)\.github\.io$/i);
  if (!m) return "https://github.com/awesome-krita/awesome-krita.github.io"; // local preview
  const first = location.pathname.split("/")[1];
  const repo = first && !first.includes(".") ? first : location.hostname; // "/index.html" is not a repo
  return `https://github.com/${m[1]}/${repo}`;
})();
const ISSUES = `${REPO}/issues/new`;
for (const a of document.querySelectorAll("a[data-repo]")) a.href = REPO + a.dataset.repo;

function feedback(entry) {
  const form = (template, title) =>
    `${ISSUES}?${new URLSearchParams({ template, entry: entry.id, title: `${title}: ${entry.name}` })}`;
  return el("details", { class: "more" },
    el("summary", { title: "Suggest an edit or report a problem", "aria-label": `Suggest an edit or report ${entry.name}` }, icon("flag")),
    el("div", { class: "menu" },
      el("a", { href: form("edit.yml", "Edit") }, icon("pencil"), "Suggest an edit"),
      el("a", { href: form("report.yml", "Report") }, icon("flag"), "Report a problem"),
    ),
  );
}

function row(entry) {
  const home = entry.repo || entry.forum;
  const links = el("div", { class: "links" },
    link("download", entry.download, "download", "Download"),
    entry.repo && link("gh", entry.repo, "github", "GitHub"),
    entry.forum && link("forum", entry.forum, "krita", "Forum", "Krita Artists forum"),
  );
  return el("li", { class: "entry", id: entry.id },
    thumb(entry),
    el("div", { class: "body" },
      el("div", { class: "title" },
        el("h2", {}, el("a", { href: home, text: entry.name })),
        entry.version && chip("tag", entry.version.replace(/^v(?=\d)/i, ""), "Version", "", "span"),
        entry.krita?.includes("6") && el("span", { class: "chip k6", title: "Tested in Krita 6" }, icon("krita"), "Krita 6"),
        feedback(entry),
      ),
      el("div", { class: "by", text: `by ${entry.author}` }),
      entry.description && el("p", { class: "desc", text: entry.description }),
      chips(entry),
      links,
    ),
  );
}

// --- filtering ---------------------------------------------------------------

function matches(entry) {
  for (const { key } of FACETS) {
    const picked = state.filters[key];
    if (picked.size && !valuesOf(entry, key).some((v) => picked.has(v))) return false;
  }
  if (!state.q) return true;
  const hay = [entry.name, entry.author, entry.description].join(" ").toLowerCase();
  return state.q.split(/\s+/).every((w) => hay.includes(w));
}

// With types picked, the Category menu only offers their categories.
function pairCategoriesWithTypes() {
  const types = [...state.filters.type];
  const allowed = types.length ? new Set(types.flatMap((t) => data.category_types[t] || [])) : null;
  for (const c of controls) {
    if (c.key !== "category") continue;
    const fits = !allowed || allowed.has(c.value);
    c.row.hidden = !fits;
    if (!fits) state.filters.category.delete(c.value);
  }
}

function render() {
  pairCategoriesWithTypes();
  const shown = data.entries.filter(matches).sort(SORTS[state.sort] || SORTS.name);
  $("list").replaceChildren(...shown.map(row));
  $("count").textContent = shown.length === 1 ? "1 entry" : `${shown.length} entries`;
  $("empty").hidden = shown.length > 0;
  syncFilters();
}

const controls = []; // { key, value, input } for every checkbox, to keep them in step with state

function buildFacets() {
  const total = data.entries.length;
  const facets = FACETS.map((facet) => {
    const options = Object.entries(facet.options(data) || {})
      .map(([value, label]) => [value, label, data.entries.filter((e) => valuesOf(e, facet.key).includes(value)).length])
      .filter(([, , count]) => facet.always || count > 0);
    if (!facet.always && !options.some(([, , count]) => count < total)) return null; // would not narrow anything

    const count = el("span", { class: "n" });
    const panel = el("div", { class: "panel" }, ...options.map(([value, label, n]) => {
      const input = el("input", { type: "checkbox", value, disabled: n === 0 });
      input.addEventListener("change", () => {
        state.filters[facet.key][input.checked ? "add" : "delete"](value);
        render();
      });
      const row = el("label", { class: n === 0 ? "none" : null },
        input, facet.swatch && swatch(value), el("span", { text: label }), el("span", { class: "n", text: n }));
      controls.push({ key: facet.key, value, input, label, row, swatch: facet.swatch });
      return row;
    }));
    const details = el("details", { class: "facet", "data-key": facet.key },
      el("summary", {}, facet.label, count), panel);
    details.addEventListener("toggle", () => {
      if (details.open) closeMenus(details);
    });
    return details;
  });
  $("facets").replaceChildren(...facets.filter(Boolean));
}

function syncFilters() {
  for (const c of controls) c.input.checked = state.filters[c.key].has(c.value);
  for (const details of document.querySelectorAll(".facet")) {
    const n = state.filters[details.dataset.key].size;
    details.querySelector("summary .n").textContent = n ? String(n) : "";
    details.classList.toggle("on", n > 0);
  }

  const picked = controls.filter((c) => c.input.checked);
  const active = $("active");
  active.hidden = picked.length === 0;
  active.replaceChildren(
    ...picked.map((c) => {
      const b = el("button", { type: "button", class: "chip remove", "aria-label": `Remove filter ${c.label}` },
        c.swatch && swatch(c.value), c.label, el("span", { "aria-hidden": "true", text: "×" }));
      b.addEventListener("click", () => { state.filters[c.key].delete(c.value); render(); });
      return b;
    }),
    ...(picked.length > 1 ? [clearAll()] : []),
  );
}

function clearAll() {
  const b = el("button", { type: "button", class: "clear", text: "Clear all" });
  b.addEventListener("click", () => { for (const set of Object.values(state.filters)) set.clear(); render(); });
  return b;
}

// Close an open filter or flag menu when clicking elsewhere or pressing Escape. One open at a time.
const MENUS = ".facet[open], .more[open]";
function closeMenus(except) {
  for (const d of document.querySelectorAll(MENUS)) if (d !== except) d.open = false;
}
document.addEventListener("toggle", (e) => {
  if (e.target.matches?.(".more") && e.target.open) closeMenus(e.target);
}, true);
document.addEventListener("click", (e) => {
  for (const d of document.querySelectorAll(MENUS)) if (!d.contains(e.target)) d.open = false;
});
document.addEventListener("keydown", (e) => {
  if (e.key !== "Escape") return;
  const open = document.querySelector(MENUS);
  if (open) { open.open = false; open.querySelector("summary").focus(); }
});

// --- list or grid ------------------------------------------------------------

function setView(view) {
  state.view = view;
  $("list").classList.toggle("grid", view === "grid");
  for (const b of document.querySelectorAll(".view button")) b.setAttribute("aria-pressed", String(b.dataset.view === view));
  try { localStorage.setItem("view", view); } catch {}
}

for (const b of document.querySelectorAll(".view button")) b.addEventListener("click", () => setView(b.dataset.view));
try { if (localStorage.getItem("view") === "grid") setView("grid"); } catch {}

// --- start -------------------------------------------------------------------

fetch("data.json")
  .then((r) => r.json())
  .then((json) => {
    data = json;
    buildFacets();
    $("generated").textContent = `Last refresh: ${formatDate(data.generated)}.`;
    $("q").addEventListener("input", (e) => { state.q = e.target.value.trim().toLowerCase(); render(); });
    $("sort").addEventListener("change", (e) => { state.sort = e.target.value; render(); });
    render();
  })
  .catch(() => { $("count").textContent = "The list could not be loaded. Try reloading the page."; });
