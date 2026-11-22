// Draws the list from data.json. Text from GitHub and the forum is only ever set with textContent.

const $ = (id) => document.getElementById(id);
const state = { q: "", type: "all", category: "all" };
let data;

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === "text") node.textContent = v;
    else if (k === "style") node.style.cssText = v;
    else node.setAttribute(k, v);
  }
  node.append(...children.filter(Boolean));
  return node;
}

const swatch = (cat) => el("span", { class: "swatch", style: `--sw: var(--${cat})`, "aria-hidden": "true" });

function formatDate(iso) {
  return new Date(iso + "T00:00:00").toLocaleDateString(undefined, { year: "numeric", month: "short" });
}

// GIFs show their first frame until clicked, so nothing moves on its own.
function thumb(entry) {
  const style = `--sw: var(--${entry.category})`;
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

function row(entry) {
  const home = entry.repo || entry.forum;
  const meta = el("ul", { class: "meta" },
    el("li", {}, swatch(entry.category), data.categories[entry.category]),
    el("li", { text: entry.type }),
    entry.version && el("li", { text: entry.version }),
    entry.license && el("li", { text: entry.license }),
    entry.stars != null && el("li", { text: `${entry.stars} stars` }),
    (entry.krita || entry.os) && el("li", { text: ["Tested",
      entry.krita && `in Krita ${entry.krita.join(", ")}`,
      entry.os && `on ${entry.os.join(", ")}`].filter(Boolean).join(" ") }),
    entry.updated && el("li", { text: `Updated ${formatDate(entry.updated)}` }),
    entry.archived && el("li", { class: "archived", text: "Archived" }),
  );
  const links = el("div", { class: "links" },
    el("a", { class: "download", href: entry.download, text: "Download" }),
    entry.repo && el("a", { href: entry.repo, text: "GitHub" }),
    entry.forum && el("a", { href: entry.forum, text: "Krita Artists" }),
  );
  return el("li", { class: "entry", id: entry.id },
    thumb(entry),
    el("div", {},
      el("h2", {}, el("a", { href: home, text: entry.name })),
      el("div", { class: "by", text: `by ${entry.author}` }),
      entry.description && el("p", { class: "desc", text: entry.description }),
      meta,
      links,
    ),
  );
}

function matches(entry) {
  if (state.type !== "all" && entry.type !== state.type) return false;
  if (state.category !== "all" && entry.category !== state.category) return false;
  if (!state.q) return true;
  const hay = [entry.name, entry.author, entry.description].join(" ").toLowerCase();
  return state.q.split(/\s+/).every((w) => hay.includes(w));
}

function render() {
  const shown = data.entries.filter(matches);
  $("list").replaceChildren(...shown.map(row));
  $("count").textContent = shown.length === 1 ? "1 entry" : `${shown.length} entries`;
  $("empty").hidden = shown.length > 0;
}

function buttons(container, key, options, withSwatch) {
  const all = { all: "All", ...options };
  const used = new Set(data.entries.map((e) => e[key]));
  const list = Object.entries(all).filter(([value]) => value === "all" || used.has(value));
  container.parentElement.hidden = list.length < 3; // only one option: nothing to filter
  container.replaceChildren(...list.map(([value, label]) => {
    const b = el("button", { type: "button", "aria-pressed": String(state[key] === value) },
      withSwatch && value !== "all" && swatch(value), label);
    b.addEventListener("click", () => {
      state[key] = value;
      for (const other of container.children) other.setAttribute("aria-pressed", String(other === b));
      render();
    });
    return b;
  }));
}

fetch("data.json")
  .then((r) => r.json())
  .then((json) => {
    data = json;
    buttons($("types"), "type", data.types, false);
    buttons($("categories"), "category", data.categories, true);
    $("generated").textContent = `Last refresh: ${formatDate(data.generated)}.`;
    $("q").addEventListener("input", (e) => { state.q = e.target.value.trim().toLowerCase(); render(); });
    render();
  })
  .catch(() => { $("count").textContent = "The list could not be loaded. Try reloading the page."; });
