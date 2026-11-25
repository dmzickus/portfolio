// dylanzickus.com — carousel, filters, resume focus switcher, logo poke. No dependencies.
(() => {
  "use strict";
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ── homepage carousel: drag, arrows, keyboard, year scrubber ─────
  const car = document.querySelector("[data-carousel]");
  if (car) {
    const vp = car.querySelector("[data-car-viewport]");
    const slides = $$(".slide", vp);
    const prev = car.querySelector("[data-car-prev]");
    const next = car.querySelector("[data-car-next]");
    const scrub = document.querySelector("[data-scrubber]");
    const yearBtns = scrub ? $$("button", scrub) : [];
    const signal = scrub ? $$(".scrub-signal .bars i", scrub) : [];
    const behavior = reduced ? "auto" : "smooth";
    const step = () => (slides[0]?.getBoundingClientRect().width || 300) + 24;

    const update = () => {
      const max = vp.scrollWidth - vp.clientWidth;
      prev.disabled = vp.scrollLeft <= 4;
      next.disabled = vp.scrollLeft >= max - 4;
      // which year is in the middle of the viewport?
      const mid = vp.getBoundingClientRect().left + vp.clientWidth / 2;
      let cur = slides[0];
      for (const s of slides) if (s.getBoundingClientRect().left <= mid) cur = s;
      const y = cur?.dataset.year;
      yearBtns.forEach(b => b.setAttribute("aria-current", String(b.dataset.yearJump === y)));
      // signal meter fills as you scroll toward "now"
      const frac = max > 0 ? vp.scrollLeft / max : 1;
      signal.forEach((bar, i) => bar.classList.toggle("on", frac >= i / 4 + 0.01 || i === 0));
    };
    vp.addEventListener("scroll", () => requestAnimationFrame(update), { passive: true });
    prev.addEventListener("click", () => vp.scrollBy({ left: -step(), behavior }));
    next.addEventListener("click", () => vp.scrollBy({ left: step(), behavior }));
    vp.addEventListener("keydown", e => {
      if (e.key === "ArrowRight") { vp.scrollBy({ left: step(), behavior }); e.preventDefault(); }
      if (e.key === "ArrowLeft") { vp.scrollBy({ left: -step(), behavior }); e.preventDefault(); }
    });
    yearBtns.forEach(b => b.addEventListener("click", () => {
      const s = slides.find(x => x.dataset.year === b.dataset.yearJump && !x.hasAttribute("data-hidden"));
      if (s) vp.scrollTo({ left: s.offsetLeft - vp.clientWidth / 2 + s.clientWidth / 2, behavior });
    }));

    // mouse drag to scroll (touch already scrolls natively)
    let down = false, startX = 0, startLeft = 0, moved = false;
    vp.addEventListener("pointerdown", e => {
      if (e.pointerType !== "mouse") return;
      down = true; moved = false; startX = e.clientX; startLeft = vp.scrollLeft;
    });
    addEventListener("pointermove", e => {
      if (!down) return;
      const dx = e.clientX - startX;
      if (Math.abs(dx) > 5) { moved = true; vp.classList.add("dragging"); }
      vp.scrollLeft = startLeft - dx;
    });
    addEventListener("pointerup", () => {
      if (!down) return;
      down = false;
      setTimeout(() => vp.classList.remove("dragging"), 0);
    });
    vp.addEventListener("click", e => { if (moved) { e.preventDefault(); moved = false; } }, true);
    // vertical mouse wheel scrolls the carousel sideways while hovered
    vp.addEventListener("wheel", e => {
      if (Math.abs(e.deltaY) <= Math.abs(e.deltaX)) return;
      const max = vp.scrollWidth - vp.clientWidth;
      if ((e.deltaY < 0 && vp.scrollLeft <= 0) || (e.deltaY > 0 && vp.scrollLeft >= max - 1)) return;
      vp.scrollLeft += e.deltaY;
      e.preventDefault();
    }, { passive: false });

    // open on the newest project
    vp.scrollLeft = vp.scrollWidth;
    update();
  }

  // ── filters (projects timeline) ─────────────────────────────────
  const filters = document.querySelector("[data-filters]");
  const list = document.querySelector("[data-list]");
  if (filters && list) {
    const input = filters.querySelector("[data-search-input]");
    const empty = filters.querySelector("[data-empty]");
    const items = $$("[data-search]", list);
    const state = { area: new Set(), status: new Set() };
    const params = new URLSearchParams(location.search);
    for (const k of Object.keys(state)) (params.get(k) || "").split(",").filter(Boolean).forEach(v => state[k].add(v));
    if (input && params.get("q")) input.value = params.get("q");
    $$("button[data-filter]", filters).forEach(b => {
      if (state[b.dataset.filter].has(b.dataset.value)) b.setAttribute("aria-pressed", "true");
    });

    const apply = () => {
      const words = (input?.value || "").trim().toLowerCase().split(/\s+/).filter(Boolean);
      let shown = 0;
      for (const el of items) {
        const tags = (el.dataset.tags || "").split("|");
        const ok = (!state.area.size || state.area.has(el.dataset.area)) &&
          (!state.status.size || state.status.has(el.dataset.status)) &&
          words.every(w => el.dataset.search.includes(w) || tags.some(t => t.startsWith(w)));
        el.toggleAttribute("data-hidden", !ok);
        if (ok) shown++;
      }
      $$("[data-group]", list).forEach(g => g.toggleAttribute("data-hidden", !g.querySelector("[data-search]:not([data-hidden])")));
      if (empty) empty.hidden = shown > 0;
      const p = new URLSearchParams();
      for (const [k, set] of Object.entries(state)) if (set.size) p.set(k, [...set].join(","));
      if (words.length) p.set("q", words.join(" "));
      history.replaceState(null, "", p.toString() ? `?${p}` : location.pathname);
    };
    filters.addEventListener("click", e => {
      const b = e.target.closest("button[data-filter]");
      if (b) {
        const on = b.getAttribute("aria-pressed") !== "true";
        b.setAttribute("aria-pressed", String(on));
        on ? state[b.dataset.filter].add(b.dataset.value) : state[b.dataset.filter].delete(b.dataset.value);
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
    // clicking a tag chip on the timeline filters by it
    list.addEventListener("click", e => {
      const t = e.target.closest(".tag");
      if (t && input) { input.value = t.textContent.trim().toLowerCase(); apply(); input.scrollIntoView({ block: "center", behavior: reduced ? "auto" : "smooth" }); }
    });
    apply();
  }

  // ── resume focus switcher ───────────────────────────────────────
  const sw = document.querySelector("[data-focus-switch]");
  const resume = document.querySelector("[data-resume]");
  if (sw && resume) {
    $$("[data-sortable]", resume).forEach(ul => [...ul.children].forEach((li, i) => (li.dataset.i = i)));
    const set = focus => {
      $$("[data-sortable]", resume).forEach(ul => {
        const kids = [...ul.children];
        kids.forEach(li => li.classList.toggle("match", focus !== "all" && (li.dataset.focus || "").split(" ").includes(focus)));
        kids.sort((a, b) => (focus !== "all" && (Number(b.classList.contains("match")) - Number(a.classList.contains("match")))) || a.dataset.i - b.dataset.i)
          .forEach(li => ul.appendChild(li));
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

  // ── logo: click to drop the signal again ────────────────────────
  const mark = document.querySelector(".hero-mark");
  if (mark && !reduced) {
    let pokes = 0;
    mark.addEventListener("click", () => {
      mark.classList.remove("replay"); void mark.offsetWidth; mark.classList.add("replay");
      if (++pokes === 5) mark.title = "okay okay, the connection's fine";
    });
  }
})();
