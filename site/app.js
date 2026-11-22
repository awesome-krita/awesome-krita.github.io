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

// Icons: download and github from Lucide (ISC license), krita from Simple Icons (CC0).
const ICONS = {
  download: { stroke: true, d: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/>' },
  github: { stroke: true, d: '<path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/>' },
  krita: { stroke: false, d: '<path d="M.652.76a.625.625 0 00-.5.246c-.352.448-.035.898.362 1.262.206.189 1.77 1.794 3.428 3.527a11.054 11.054 0 011.815-1.983C3.667 2.515 1.694 1.266 1.461 1.1 1.201.914.917.762.652.76zm5.105 3.052c1.848 1.148 3.786 2.332 4.693 2.84 1.469.821 3.758 2.684 4.092 4.434.535.466 2.182 1.916 2.596 2.413.698-.211 1.518.133 2.06 1.12.866 1.583.227 3.747-1.968 4.988a5.42 5.42 0 01-.296.267l.296-.267c1.14-1.468-.714-2.44-1.175-3.864a2.06 2.06 0 01-.11-.78c-.533-.282-2.11-1.452-2.795-1.965-1.801.16-4.207-1.773-5.35-3.08-.7-.802-2.32-2.517-3.858-4.123a11.052 11.052 0 00-2.046 6.393A11.052 11.052 0 1012.948 1.136c-2.64.004-5.19.954-7.19 2.676zm8.71 7.552c-.515.126-.968.831-1.118 1.306-.038.115-.04.303.066.342.802.592 1.556 1.168 2.4 1.7.162-.393.746-.963 1.096-1.2zm-11.53 1.639c.812 1.898 5.798 7.17 12.06 2.695a2.07 2.07 0 00.114.715c.46 1.42 2.36 2.427 1.238 3.89-2.135 1.364-5 1.201-6.989.528-3.558-1.204-5.914-4.332-6.424-7.828zm13.782.7a.771.771 0 00-.065.049c-.004.003-.008.008-.011.008.003-.003.007-.008.01-.008.024-.015.044-.034.066-.048z"/>' },
};

const $ = (id) => document.getElementById(id);
const state = { q: "", view: "list", filters: Object.fromEntries(FACETS.map((f) => [f.key, new Set()])) };
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

function formatDate(iso) {
  return new Date(iso + "T00:00:00").toLocaleDateString(undefined, { year: "numeric", month: "short" });
}

// --- one entry ---------------------------------------------------------------

// GIFs show their first frame until clicked, so nothing moves on its own.
function thumb(entry) {
  const style = `--sw: var(--${entry.category[0]})`;
  if (!entry.image) return el("div", { class: "thumb", style, "aria-hidden": "true" });

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

function chips(entry) {
  const tested = (entry.krita || entry.os) && ["Tested",
    entry.krita && `in Krita ${entry.krita.join(", ")}`,
    entry.os && `on ${entry.os.join(", ")}`].filter(Boolean).join(" ");
  // "minor" chips are left out of the grid view to keep cards short.
  return el("ul", { class: "chips", "aria-label": "Details" },
    ...entry.category.map((c) => el("li", { class: "chip cat" }, swatch(c), data.categories[c] || c)),
    el("li", { class: "chip", text: entry.type[0].toUpperCase() + entry.type.slice(1) }),
    entry.version && el("li", { class: "chip", text: entry.version }),
    entry.license && el("li", { class: "chip minor", text: entry.license }),
    entry.stars != null && el("li", { class: "chip minor", text: `${entry.stars} ${entry.stars === 1 ? "star" : "stars"}` }),
    tested && el("li", { class: "chip minor", text: tested }),
    entry.updated && el("li", { class: "chip minor", text: `Updated ${formatDate(entry.updated)}` }),
    entry.archived && el("li", { class: "chip warn", text: "Archived" }),
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
      el("h2", {}, el("a", { href: home, text: entry.name })),
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
  const shown = data.entries.filter(matches);
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
      if (details.open) for (const other of document.querySelectorAll(".facet[open]")) if (other !== details) other.open = false;
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

// Close an open filter menu when clicking elsewhere or pressing Escape.
document.addEventListener("click", (e) => {
  for (const d of document.querySelectorAll(".facet[open]")) if (!d.contains(e.target)) d.open = false;
});
document.addEventListener("keydown", (e) => {
  if (e.key !== "Escape") return;
  const open = document.querySelector(".facet[open]");
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
    render();
  })
  .catch(() => { $("count").textContent = "The list could not be loaded. Try reloading the page."; });
