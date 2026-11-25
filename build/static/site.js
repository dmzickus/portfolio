// dylanzickus.com — filters, resume focus switcher, logo replay. No dependencies.
(() => {
  "use strict";
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

  // ── filterable lists (timeline + projects) ──────────────────────
  const filters = document.querySelector("[data-filters]");
  const list = document.querySelector("[data-list]");
  if (filters && list) {
    const input = filters.querySelector("[data-search-input]");
    const empty = filters.querySelector("[data-empty]");
    const items = $$("[data-search]", list);
    const state = { area: new Set(), status: new Set(), tag: new Set() };

    // restore from URL (?area=homelab&status=live&tag=docker&q=mqtt) so filtered views can be shared
    const params = new URLSearchParams(location.search);
    for (const k of Object.keys(state)) (params.get(k) || "").split(",").filter(Boolean).forEach(v => state[k].add(v));
    if (input && params.get("q")) input.value = params.get("q");
    $$("button[data-filter]", filters).forEach(b => {
      if (state[b.dataset.filter].has(b.dataset.value)) b.setAttribute("aria-pressed", "true");
    });

    const apply = () => {
      const q = (input?.value || "").trim().toLowerCase();
      const words = q.split(/\s+/).filter(Boolean);
      let shown = 0;
      for (const el of items) {
        const tags = (el.dataset.tags || "").split("|");
        const ok =
          (!state.area.size || state.area.has(el.dataset.area)) &&
          (!state.status.size || state.status.has(el.dataset.status)) &&
          (!state.tag.size || [...state.tag].every(t => tags.includes(t))) &&
          words.every(w => el.dataset.search.includes(w));
        el.toggleAttribute("data-hidden", !ok);
        if (ok) shown++;
      }
      $$("[data-group]", list).forEach(g => g.toggleAttribute("data-hidden", !g.querySelector("[data-search]:not([data-hidden])")));
      if (empty) empty.hidden = shown > 0;

      const p = new URLSearchParams();
      for (const [k, set] of Object.entries(state)) if (set.size) p.set(k, [...set].join(","));
      if (q) p.set("q", q);
      const qs = p.toString();
      history.replaceState(null, "", qs ? `?${qs}` : location.pathname);
    };

    filters.addEventListener("click", e => {
      const b = e.target.closest("button[data-filter]");
      if (b) {
        const set = state[b.dataset.filter];
        const on = b.getAttribute("aria-pressed") !== "true";
        b.setAttribute("aria-pressed", String(on));
        on ? set.add(b.dataset.value) : set.delete(b.dataset.value);
        apply();
      }
      if (e.target.closest("[data-clear]")) {
        Object.values(state).forEach(s => s.clear());
        $$("button[data-filter]", filters).forEach(x => x.setAttribute("aria-pressed", "false"));
        if (input) input.value = "";
        apply();
      }
    });
    input?.addEventListener("input", apply);
    apply();
  }

  // ── resume focus switcher ───────────────────────────────────────
  const sw = document.querySelector("[data-focus-switch]");
  const resume = document.querySelector("[data-resume]");
  if (sw && resume) {
    // remember the original order so "Everything" restores it
    $$("[data-sortable]", resume).forEach(ul => [...ul.children].forEach((li, i) => (li.dataset.i = i)));
    const set = focus => {
      $$("[data-sortable]", resume).forEach(ul => {
        const kids = [...ul.children];
        kids.forEach(li => li.classList.toggle("match", focus !== "all" && (li.dataset.focus || "").split(" ").includes(focus)));
        kids.sort((a, b) => {
          if (focus !== "all") {
            const d = Number(b.classList.contains("match")) - Number(a.classList.contains("match"));
            if (d) return d;
          }
          return a.dataset.i - b.dataset.i;
        }).forEach(li => ul.appendChild(li));
      });
      focus === "all" ? resume.removeAttribute("data-focus") : resume.setAttribute("data-focus", focus);
      $$("[data-pdf-for]").forEach(a => (a.hidden = a.dataset.pdfFor !== focus));
      const u = new URL(location.href);
      focus === "all" ? u.searchParams.delete("focus") : u.searchParams.set("focus", focus);
      history.replaceState(null, "", u);
    };
    sw.addEventListener("change", e => set(e.target.value));
    const initial = new URLSearchParams(location.search).get("focus");
    const radio = initial && sw.querySelector(`input[value="${CSS.escape(initial)}"]`);
    if (radio) { radio.checked = true; set(initial); }
  }

  // ── hero mark: hover/click drops the signal again ──────────────
  const mark = document.querySelector(".hero-mark");
  if (mark && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
    let busy = false;
    const replay = () => {
      if (busy) return;
      busy = true;
      mark.classList.remove("replay");
      void mark.offsetWidth;
      mark.classList.add("replay");
      setTimeout(() => (busy = false), 1600);
    };
    mark.addEventListener("pointerenter", replay);
    mark.addEventListener("click", replay);
  }
})();
