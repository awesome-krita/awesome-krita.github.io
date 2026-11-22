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

function row(entry) {
  const home = entry.repo || entry.forum;
  const links = el("div", { class: "links" },
    el("a", { class: "download", href: entry.download, text: "Download" }),
    entry.repo && el("a", { href: entry.repo, text: "GitHub" }),
    entry.forum && el("a", { href: entry.forum, text: "Krita Artists" }),
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
