/* Epsilon Publishing Group — shared front-end for the static export.
   Real, independently-hosted pages: no client-side router, no data-URI
   image lookups. This only wires up the bits of interactivity the
   prerendered markup needs (hero animation, reveals, nav, book search,
   cover lightbox). Everything else is a plain link the browser follows. */
(() => {
  const PREFIX = window.__PREFIX || "";
  let META = {};
  let CAT_COVERS = {};

  /* ---- book-world hero: scroll flies the camera between real covers ---- */
  const DEPTH = 2600, PASS = 700, CHAR_LEAD = 680, CHAR_BEHIND = 90;
  const fl = { root: null, cam: null, layers: [], chars: [], copy: null, aside: null,
               hint: null, gaugeN: null, gaugeFill: null, white: null, steps: 4,
               t: { p: 0, rx: 0, ry: 0 }, c: { p: 0, rx: 0, ry: 0 } };
  const calm = matchMedia("(prefers-reduced-motion: reduce)");
  const smoo = (v) => v * v * (3 - 2 * v);
  const cl01 = (v) => Math.min(1, Math.max(0, v));

  (function loop() {
    if (fl.root) {
      const c = fl.c, t = fl.t;
      c.p += (t.p - c.p) * (calm.matches ? 1 : 0.12);
      c.rx += (t.rx - c.rx) * 0.06;
      c.ry += (t.ry - c.ry) * 0.06;
      const camT = `rotateX(${c.rx.toFixed(3)}deg) rotateY(${c.ry.toFixed(3)}deg)`;
      if (fl.cam) fl.cam.style.transform = camT;
      if (fl.glasses) for (const g of fl.glasses) if (g.cam) g.cam.style.transform = camT;

      const travel = DEPTH + PASS;
      for (let i = 0; i < fl.layers.length; i += 1) {
        const el = fl.layers[i];
        const dv = Number(el.dataset.d);
        const zb = c.p * travel - dv * DEPTH;
        let o = 1;
        if (zb > PASS) o = 0;
        else if (zb > 300) o = 1 - (zb - 300) / (PASS - 300);
        const op = o.toFixed(3);
        const vis = o <= 0.001 ? "hidden" : "visible";
        const q = cl01((zb + dv * DEPTH) / travel);
        const tr = `translate(-50%, -50%) translateZ(${zb.toFixed(1)}px) rotate(${(q * Number(el.dataset.drift)).toFixed(2)}deg)`;
        el.style.opacity = op;
        el.style.visibility = vis;
        el.style.transform = tr;
        if (fl.glasses) for (const g of fl.glasses) {
          const gl = g.layers[i];
          if (!gl) continue;
          gl.style.opacity = op;
          gl.style.visibility = vis;
          gl.style.transform = tr;
        }
      }

      for (const ch of fl.chars) {
        const bookEl = fl.layers[Number(ch.dataset.b)];
        if (!bookEl) continue;
        const dv = Number(bookEl.dataset.d);
        const zb = c.p * travel - dv * DEPTH;
        const raw = cl01((zb + 250) / 800);
        const delay = Number(ch.dataset.delay);
        const e = smoo(cl01((smoo(raw) - delay) / (1 - delay)));
        const dz = e * CHAR_LEAD * Number(ch.dataset.lead) - CHAR_BEHIND;
        const zc = zb + dz;
        let op = 1, blur = 0;
        if (zc > 430) {
          const tt = cl01((zc - 430) / 320);
          op = 1 - tt;
          blur = tt * 10;
        }
        ch.style.opacity = op.toFixed(3);
        ch.style.visibility = op <= 0.001 || e <= 0.001 ? "hidden" : "visible";
        ch.style.filter = blur > 0.2 ? `blur(${blur.toFixed(1)}px)` : "none";
        ch.style.transform =
          `translate(-50%, -50%) translate3d(${(Number(ch.dataset.dx) * e).toFixed(2)}vw, ${(Number(ch.dataset.dy) * e).toFixed(2)}vh, ${dz.toFixed(1)}px) rotate(${(Number(ch.dataset.rot) * e).toFixed(2)}deg)`;
      }

      const outCopy = smoo(cl01((c.p - 0.4) / 0.24));
      const outAside = smoo(cl01((c.p - 0.5) / 0.24));
      if (fl.copy) {
        fl.copy.style.opacity = (1 - outCopy).toFixed(3);
        fl.copy.style.transform =
          `translate3d(${(-outCopy * 7).toFixed(2)}vw, ${(-outCopy * 4).toFixed(2)}vh, 0) scale(${(1 + outCopy * 0.22).toFixed(4)})`;
        fl.copy.style.visibility = outCopy >= 0.999 ? "hidden" : "visible";
      }
      if (fl.copyInner) fl.copyInner.style.transform =
        `translate3d(${(-outCopy * 9).toFixed(2)}vw, ${(-outCopy * 6).toFixed(2)}vh, 0) scale(${(1 + outCopy * 0.18).toFixed(4)})`;
      if (fl.aside) {
        fl.aside.style.opacity = (1 - outAside).toFixed(3);
        fl.aside.style.transform =
          `translate3d(${(outAside * 8).toFixed(2)}vw, ${(outAside * 6).toFixed(2)}vh, 0) scale(${(1 + outAside * 0.2).toFixed(4)})`;
        fl.aside.style.visibility = outAside >= 0.999 ? "hidden" : "visible";
      }
      if (fl.asideInner) fl.asideInner.style.transform =
        `translate3d(${(outAside * 10).toFixed(2)}vw, ${(outAside * 7).toFixed(2)}vh, 0) scale(${(1 + outAside * 0.15).toFixed(4)})`;
      if (fl.hint) {
        const h = Math.max(0, 1 - c.p * 9);
        fl.hint.style.opacity = h.toFixed(3);
        fl.hint.style.visibility = h <= 0.01 ? "hidden" : "visible";
      }
      if (fl.white) fl.white.style.opacity = smoo(cl01((c.p - 0.9) / 0.1)).toFixed(3);

      if (fl.glasses && fl.vp) {
        const vr = fl.vp.getBoundingClientRect();
        const reveal = (smoo(cl01((c.p - 0.02) / 0.12)) * 0.62).toFixed(3);
        for (const g of fl.glasses) {
          const pr = g.pane.getBoundingClientRect();
          g.clone.style.translate = `${(vr.left - pr.left).toFixed(1)}px ${(vr.top - pr.top).toFixed(1)}px`;
          g.clone.style.opacity = reveal;
        }
      }
      if (fl.gaugeFill) fl.gaugeFill.style.transform = `scaleY(${c.p.toFixed(4)})`;
      if (fl.gaugeN) {
        const step = Math.min(fl.steps, Math.max(1, Math.ceil(c.p * fl.steps || 1)));
        const label = String(step).padStart(2, "0");
        if (fl.gaugeN.textContent !== label) fl.gaugeN.textContent = label;
      }
    }
    requestAnimationFrame(loop);
  })();

  addEventListener("scroll", () => {
    if (!fl.root) return;
    const r = fl.root.getBoundingClientRect();
    const usable = r.height - innerHeight;
    fl.t.p = cl01(-r.top / Math.max(usable, 1));
  }, { passive: true });

  addEventListener("pointermove", (e) => {
    if (!fl.root || calm.matches || e.pointerType !== "mouse") return;
    fl.t.ry = ((e.clientX / innerWidth) * 2 - 1) * 2.5;
    fl.t.rx = ((e.clientY / innerHeight) * 2 - 1) * -1.8;
  }, { passive: true });

  const wireHero = (root) => {
    const el = root.querySelector(".hb");
    fl.root = el || null;
    fl.t = { p: 0, rx: 0, ry: 0 };
    fl.c = { p: 0, rx: 0, ry: 0 };
    fl.layers = [];
    fl.chars = [];
    if (!el) return;
    fl.cam = el.querySelector(".hb-cam");
    fl.copy = el.querySelector(".hb-copy > div");
    fl.copyInner = el.querySelector(".hb-copy .hb-pane-inner");
    fl.aside = el.querySelector(".hb-aside");
    fl.asideInner = el.querySelector(".hb-aside .hb-pane-inner");
    fl.hint = el.querySelector(".hb-hint");
    fl.white = el.querySelector(".hb-white");
    fl.gaugeN = el.querySelector(".hb-gauge-n");
    fl.gaugeFill = el.querySelector(".hb-gauge-fill");
    fl.layers = [...el.querySelectorAll(".hb-layer")];
    fl.chars = [...el.querySelectorAll(".hb-char")];
    fl.steps = fl.layers.length || 4;
    fl.glasses = [];
    fl.vp = el.querySelector(".hb-viewport");
    const stage = el.querySelector(".hb-stage");
    for (const pane of [fl.copy, fl.aside]) {
      if (!pane || !stage) continue;
      const holder = document.createElement("div");
      holder.className = "hb-glass";
      holder.setAttribute("aria-hidden", "true");
      const clone = stage.cloneNode(true);
      clone.classList.add("hb-glass-stage");
      for (const n of [...clone.querySelectorAll(".hb-char")]) n.remove();
      holder.appendChild(clone);
      pane.prepend(holder);
      fl.glasses.push({ pane, clone, holder, cam: clone.querySelector(".hb-cam"), layers: [...clone.querySelectorAll(".hb-layer")] });
    }
    if (calm.matches) el.style.height = "100svh";
  };

  /* ---- scroll reveal ---- */
  const wireReveal = (root) => {
    if (calm.matches) return;
    const io = new IntersectionObserver((entries) => {
      for (const en of entries) if (en.isIntersecting) {
        en.target.classList.add("rv-in");
        io.unobserve(en.target);
      }
    }, { rootMargin: "0px 0px -8% 0px" });
    for (const sec of root.querySelectorAll("section")) {
      if (sec.getBoundingClientRect().top > innerHeight * 0.92) {
        sec.classList.add("rv");
        io.observe(sec);
      }
    }
  };

  /* ---- category index: dim + cursor-following cover preview ---- */
  const buildCatCovers = () => {
    CAT_COVERS = {};
    for (const [slug, m] of Object.entries(META)) {
      if (!m.p) continue;
      const arr = (CAT_COVERS[m.c] = CAT_COVERS[m.c] || []);
      if (arr.length < 2) arr.push({ src: m.p, sq: !!m.sq });
    }
  };
  const wireCatIndex = (root) => {
    const list = root.querySelector(".cat-index");
    if (!list || !matchMedia("(hover: hover) and (pointer: fine)").matches || calm.matches) return;

    const preview = document.createElement("div");
    preview.className = "cat-preview";
    preview.setAttribute("aria-hidden", "true");
    preview.innerHTML =
      '<div class="cat-preview-cover"><img alt="" style="width:100%;height:100%;object-fit:cover"></div>' +
      '<div class="cat-preview-cover cat-preview-cover-2"><img alt="" style="width:100%;height:100%;object-fit:cover"></div>';
    list.appendChild(preview);
    const imgs = preview.querySelectorAll("img");

    const links = [...list.querySelectorAll("a")];
    list.addEventListener("pointermove", (e) => {
      const r = list.getBoundingClientRect();
      list.style.setProperty("--px", `${e.clientX - r.left}px`);
      list.style.setProperty("--py", `${e.clientY - r.top}px`);
    });
    for (const a of links) {
      a.addEventListener("pointerenter", () => {
        const slug = new URLSearchParams((a.getAttribute("href") || "").split("?")[1] || "").get("category");
        const covers = slug ? CAT_COVERS[slug] : null;
        for (const other of links) other.style.opacity = other === a ? "" : "0.35";
        if (covers && covers[0]) {
          imgs[0].src = covers[0].src;
          imgs[1].src = (covers[1] || covers[0]).src;
          preview.classList.toggle("cat-preview-square", !!covers[0].sq);
          preview.classList.add("cat-preview-on");
        } else {
          preview.classList.remove("cat-preview-on");
        }
      });
    }
    list.addEventListener("pointerleave", () => {
      for (const other of links) other.style.opacity = "";
      preview.classList.remove("cat-preview-on");
    });
  };

  /* ---- count-up statistics ---- */
  const wireCountUp = (root) => {
    if (calm.matches) return;
    const io = new IntersectionObserver((entries) => {
      for (const en of entries) {
        if (!en.isIntersecting) continue;
        io.unobserve(en.target);
        const el = en.target;
        const value = Number(el.dataset.countup || 0);
        if (!value) continue;
        const prefix = el.dataset.prefix || "";
        const suffix = el.dataset.suffix || "";
        const fmt = (n) => prefix + new Intl.NumberFormat("en-GB").format(Math.round(n)) + suffix;
        const start = performance.now();
        const dur = Math.min(2000, 900 + value);
        const tick = (now) => {
          const t = Math.min(1, (now - start) / dur);
          el.textContent = fmt(value * (1 - Math.pow(1 - t, 3)));
          if (t < 1) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
      }
    }, { threshold: 0.6 });
    for (const el of root.querySelectorAll("[data-countup]")) io.observe(el);
  };

  /* ---- cursor spotlight ---- */
  const wireSpotlight = (root) => {
    for (const el of root.querySelectorAll("[data-spotlight]")) {
      el.addEventListener("pointermove", (e) => {
        if (e.pointerType !== "mouse") return;
        const r = el.getBoundingClientRect();
        el.style.setProperty("--sx", `${e.clientX - r.left}px`);
        el.style.setProperty("--sy", `${e.clientY - r.top}px`);
      });
    }
  };

  /* ---- header: transparent over the hero, glass when scrolled ---- */
  const GLASS = ["border-black/6", "bg-white/65", "backdrop-blur-xl"];
  const CLEAR = ["border-transparent", "bg-transparent"];
  const syncHeader = () => {
    const h = document.querySelector("header");
    if (!h) return;
    const hero = document.querySelector("[data-hero]");
    const limit = hero ? hero.offsetHeight - innerHeight * 1.1 : 24;
    const on = scrollY > Math.max(limit, 24);
    h.classList.remove(...(on ? CLEAR : GLASS));
    h.classList.add(...(on ? GLASS : CLEAR));
  };
  addEventListener("scroll", syncHeader, { passive: true });

  /* ---- desktop dropdowns: rebuilt from the mobile nav tree ---- */
  const wireDropdowns = (root) => {
    const header = root.querySelector("header");
    const mobile = root.querySelector("#mobile-nav");
    if (!header || !mobile) return;
    const mobileParents = [...mobile.querySelectorAll(":scope nav > ul > li")];
    for (const btn of header.querySelectorAll('nav[aria-label="Main"] button[aria-expanded]')) {
      const label = btn.textContent.trim();
      const src = mobileParents.find((li) => {
        const a = li.querySelector(":scope > a");
        return a && a.textContent.trim() === label;
      });
      if (!src) continue;
      const parentHref = src.querySelector(":scope > a").getAttribute("href");
      const kids = [...src.querySelectorAll(":scope > ul a")];
      const panel = document.createElement("ul");
      panel.className = "absolute top-full left-0 min-w-56 rounded-md border border-rule bg-surface p-2 shadow-pop";
      panel.hidden = true;
      const mk = (href, text) => {
        const li = document.createElement("li");
        const a = document.createElement("a");
        a.href = href;
        a.textContent = text;
        a.className = "block rounded-sm px-3 py-2 text-sm text-ink-2 transition-colors hover:bg-paper-2 hover:text-ink";
        li.appendChild(a);
        return li;
      };
      panel.appendChild(mk(parentHref, "Overview"));
      for (const k of kids) panel.appendChild(mk(k.getAttribute("href"), k.textContent.trim()));
      const holder = btn.closest("li");
      holder.style.position = "relative";
      holder.appendChild(panel);
      const set = (open) => {
        panel.hidden = !open;
        btn.setAttribute("aria-expanded", String(open));
      };
      btn.addEventListener("click", (e) => { e.preventDefault(); set(panel.hidden); });
      holder.addEventListener("mouseenter", () => set(true));
      holder.addEventListener("mouseleave", () => set(false));
    }
  };

  /* ---- mobile menu ---- */
  const wireMenu = (root) => {
    const btn = root.querySelector('button[aria-controls="mobile-nav"]');
    const nav = root.querySelector("#mobile-nav");
    if (!btn || !nav) return;
    btn.addEventListener("click", () => {
      const open = nav.hidden;
      nav.hidden = !open;
      btn.setAttribute("aria-expanded", String(open));
    });
  };

  /* ---- /books: client-side search / facets / sort over the static grid ---- */
  const CAT_LABELS = {
    "Children's Books": "childrens-books",
    "Adult Fiction": "adult-fiction",
    "Non-Fiction": "non-fiction",
    "Young Adult": "young-adult",
  };
  const wireBrowse = (root, preselectCat) => {
    const grid = root.querySelector("main ul.grid");
    if (!grid) return false;
    const cards = [...grid.querySelectorAll(":scope > li")].map((li) => {
      const a = li.querySelector('a[href*="/books/"], a[href^="books/"], a[href^="../books/"]');
      let slug = null;
      if (a) {
        const href = a.getAttribute("href");
        const mm = href.match(/books\/([^/?#]+)\/?/);
        if (mm) slug = mm[1];
      }
      return { li, m: slug ? META[slug] : null };
    });
    if (!cards.some((c) => c.m)) return false;

    const state = { q: "", cat: new Set(), lang: new Set(), dec: new Set() };
    const countEl = [...root.querySelectorAll("p,span,div")].find((el) =>
      /^\d+\s+titles?$/.test(el.textContent.trim()));

    const apply = () => {
      let shown = 0;
      const q = state.q.toLowerCase();
      for (const c of cards) {
        const m = c.m || {};
        let ok = true;
        if (q) ok = (m.t || "").toLowerCase().includes(q) || (m.a || "").toLowerCase().includes(q);
        if (ok && state.cat.size) ok = state.cat.has(m.c);
        if (ok && state.lang.size) ok = (m.l || []).some((x) => state.lang.has(x));
        if (ok && state.dec.size) ok = state.dec.has(m.y);
        c.li.style.display = ok ? "" : "none";
        if (ok) shown += 1;
      }
      if (countEl) countEl.textContent = `${shown} ${shown === 1 ? "title" : "titles"}`;
    };

    for (const fs of root.querySelectorAll("main fieldset")) {
      const kind = (fs.querySelector("legend")?.textContent || "").trim();
      if (!/^(Category|Translated into|Published)$/.test(kind)) continue;
      for (const label of fs.querySelectorAll("label")) {
        const input = label.querySelector('input[type="checkbox"]');
        if (!input) continue;
        input.disabled = false;
        const text = (label.querySelector("span[title]")?.getAttribute("title")
          || label.textContent.replace(/\d+$/, "")).trim();
        input.addEventListener("change", () => {
          let set, val;
          if (kind === "Category") { set = state.cat; val = CAT_LABELS[text] || text; }
          else if (kind === "Translated into") { set = state.lang; val = text; }
          else { set = state.dec; val = text.replace(/s$/, "") + "s"; }
          if (input.checked) set.add(val); else set.delete(val);
          apply();
        });
        if (kind === "Category" && preselectCat && CAT_LABELS[text] === preselectCat) {
          input.checked = true;
          state.cat.add(preselectCat);
        }
      }
    }

    const search = root.querySelector('main input[type="search"]');
    if (search) {
      search.disabled = false;
      search.addEventListener("input", () => { state.q = search.value.trim(); apply(); });
    }

    const sort = root.querySelector("main select");
    if (sort) {
      sort.disabled = false;
      sort.addEventListener("change", () => {
        const v = sort.value || sort.selectedOptions[0]?.textContent || "";
        const key = /Z–A|desc/i.test(v) ? "zdesc"
          : /Newest|newest/i.test(v) ? "new"
          : /Oldest|oldest/i.test(v) ? "old"
          : /Featured|featured/i.test(v) ? "feat" : "az";
        const val = (c) => c.m || {};
        const sorted = [...cards].sort((x, y) => {
          const a = val(x), b = val(y);
          if (key === "az") return (a.t || "").localeCompare(b.t || "");
          if (key === "zdesc") return (b.t || "").localeCompare(a.t || "");
          if (key === "feat") return Number(!!b.f) - Number(!!a.f) || (a.t || "").localeCompare(b.t || "");
          const ya = parseInt(a.y) || 0, yb = parseInt(b.y) || 0;
          return key === "new" ? yb - ya : ya - yb;
        });
        for (const c of sorted) grid.appendChild(c.li);
      });
    }

    apply();
    return true;
  };

  /* ---- controls that have no live backend on a static export stay quiet ---- */
  const trim = (root, isBrowsePage) => {
    if (!isBrowsePage) {
      for (const el of root.querySelectorAll("input[type=search], select"))
        if (el.closest("div")?.parentElement) el.disabled = true;
    }

  };

  /* ---- book cover lightbox: click a detail-page cover to see it in full ---- */
  let lightboxEl = null;
  const ensureLightbox = () => {
    if (lightboxEl) return lightboxEl;
    lightboxEl = document.createElement("div");
    lightboxEl.className = "cover-lightbox";
    lightboxEl.innerHTML = '<button type="button" class="cover-lightbox-close" aria-label="Close">&times;</button><img alt=""/>';
    document.body.appendChild(lightboxEl);
    const closeIt = () => lightboxEl.classList.remove("cover-lightbox-on");
    lightboxEl.addEventListener("click", (e) => {
      if (e.target === lightboxEl || e.target.closest(".cover-lightbox-close")) closeIt();
    });
    addEventListener("keydown", (e) => { if (e.key === "Escape") closeIt(); });
    lightboxEl._img = lightboxEl.querySelector("img");
    return lightboxEl;
  };
  const wireCoverLightbox = (root) => {
    const img = root.querySelector(".cover:not(.lift-object) img");
    if (!img || img.closest("a")) return;
    img.addEventListener("click", () => {
      const lb = ensureLightbox();
      lb._img.src = img.src || img.currentSrc;
      lb._img.alt = img.alt || "";
      lb.classList.add("cover-lightbox-on");
    });
  };

  /* Native POST preserves FormSubmit verification and works without JavaScript. */
  const wireContact = () => {
    const form = document.getElementById("contact-form");
    if (!form) return;
    const status = document.getElementById("contact-status");
    const fields = [...form.querySelectorAll("[required]")];
    const validate = (field) => {
      field.setCustomValidity(field.value.trim() ? "" : "Please complete this field.");
      field.setAttribute("aria-invalid", String(!field.validity.valid));
    };
    for (const field of fields) {
      field.addEventListener("input", () => validate(field));
      field.addEventListener("invalid", () => {
        field.setAttribute("aria-invalid", "true");
        status.textContent = "Please complete all required fields and enter a valid email address.";
      });
    }
    form.addEventListener("submit", (event) => {
      for (const field of fields) validate(field);
      if (!form.reportValidity()) { event.preventDefault(); return; }
      status.textContent = "Opening secure verification. Your message has not yet been confirmed as delivered.";
    });
  };

  const boot = () => {
    wireContact();
    wireHero(document);
    wireReveal(document);
    wireCountUp(document);
    wireSpotlight(document);
    wireMenu(document);
    wireDropdowns(document);
    wireCoverLightbox(document);
    syncHeader();

    const needsMeta = document.querySelector(".cat-index") || document.querySelector("main ul.grid");
    if (needsMeta) {
      fetch(PREFIX + "assets/meta.json")
        .then((r) => r.json())
        .then((m) => {
          for (const item of Object.values(m)) {
            if (item.p?.startsWith("/assets/")) item.p = PREFIX + item.p.slice(1);
          }
          META = m;
          buildCatCovers();
          wireCatIndex(document);
          const preselect = new URLSearchParams(location.search).get("category");
          const browseWired = wireBrowse(document, preselect);
          trim(document, browseWired);
        })
        .catch(() => trim(document, false));
    } else {
      trim(document, false);
    }
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
