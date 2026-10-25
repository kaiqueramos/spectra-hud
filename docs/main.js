(() => {
  "use strict";

  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const finePointer = window.matchMedia("(pointer: fine)").matches;

  /* ---------- nav: scrolled state (observer, no scroll listener) ---------- */
  const nav = document.querySelector("[data-nav]");
  if (nav) {
    const sentinel = document.createElement("div");
    sentinel.setAttribute("aria-hidden", "true");
    sentinel.style.cssText = "position:absolute;top:0;left:0;width:1px;height:1px;pointer-events:none;";
    document.body.prepend(sentinel);

    new IntersectionObserver(
      ([entry]) => nav.classList.toggle("is-scrolled", !entry.isIntersecting),
      { threshold: 0 }
    ).observe(sentinel);
  }

  /* ---------- active section link ---------- */
  const navLinks = [...document.querySelectorAll(".nav-links a")];
  const sections = ["how", "features", "hotkeys", "privacy"]
    .map((id) => document.getElementById(id))
    .filter(Boolean);

  if (navLinks.length && sections.length) {
    const byId = new Map(navLinks.map((a) => [a.getAttribute("href").slice(1), a]));
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          navLinks.forEach((a) => a.classList.remove("is-active"));
          const link = byId.get(entry.target.id);
          if (link) link.classList.add("is-active");
        });
      },
      { rootMargin: "-45% 0px -50% 0px", threshold: 0 }
    );
    sections.forEach((s) => io.observe(s));
  }

  /* ---------- scroll reveal ---------- */
  const reveals = document.querySelectorAll(".reveal");
  if (reveals.length) {
    if (reduce) {
      reveals.forEach((el) => el.classList.add("in"));
    } else {
      const io = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (!entry.isIntersecting) return;
            entry.target.classList.add("in");
            io.unobserve(entry.target);
          });
        },
        { threshold: 0.12 }
      );
      reveals.forEach((el) => io.observe(el));
    }
  }

  /* ---------- how it works: step sync ---------- */
  const sticky = document.querySelector("[data-how-sticky]");
  const steps = [...document.querySelectorAll("[data-step-block]")];
  const triggers = [...document.querySelectorAll("[data-trigger]")];
  if (sticky && steps.length) {
    if (reduce) {
      sticky.dataset.step = "4";
      steps.forEach((s) => s.classList.add("is-active"));
    } else if (triggers.length) {
      const io = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (!entry.isIntersecting) return;
            const n = entry.target.dataset.trigger;
            sticky.dataset.step = n;
            steps.forEach((s) => s.classList.toggle("is-active", s.dataset.stepBlock === n));
          });
        },
        { rootMargin: "-45% 0px -45% 0px", threshold: 0 }
      );
      triggers.forEach((t) => io.observe(t));
    }
  }

  /* ---------- cursor reticle ---------- */
  const cursor = document.querySelector(".cursor");
  const coord = document.querySelector("[data-coord]");
  if (cursor && finePointer && !reduce) {
    let tx = window.innerWidth / 2;
    let ty = window.innerHeight / 2;
    let cx = tx;
    let cy = ty;
    let raf = null;

    const loop = () => {
      cx += (tx - cx) * 0.18;
      cy += (ty - cy) * 0.18;
      cursor.style.transform = `translate3d(calc(${cx}px - 50%), calc(${cy}px - 50%), 0)`;
      if (coord) {
        const x = String(Math.max(0, Math.round(cx))).padStart(4, "0");
        const y = String(Math.max(0, Math.round(cy))).padStart(4, "0");
        coord.textContent = `${x} / ${y}`;
      }
      raf = requestAnimationFrame(loop);
    };

    window.addEventListener("pointermove", (event) => {
      tx = event.clientX;
      ty = event.clientY;
      document.body.classList.add("has-cursor");
      if (!raf) loop();
    }, { passive: true });

    window.addEventListener("pointerleave", () => {
      document.body.classList.remove("has-cursor");
      cancelAnimationFrame(raf);
      raf = null;
    });
  }

  /* ---------- reduced motion: keep the hero video still ---------- */
  const heroVideo = document.querySelector(".hero-video");
  if (heroVideo && reduce) {
    heroVideo.removeAttribute("autoplay");
    heroVideo.pause();
  }

  /* ---------- copy install command ---------- */
  const copyBtn = document.querySelector("[data-copy]");
  const code = document.getElementById("install-code");
  if (copyBtn && code) {
    copyBtn.addEventListener("click", async () => {
      const text = code.textContent || "";
      try {
        await navigator.clipboard.writeText(text);
      } catch {
        const ta = document.createElement("textarea");
        ta.value = text;
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        ta.remove();
      }
      copyBtn.textContent = "COPIED";
      copyBtn.classList.add("is-done");
      window.setTimeout(() => {
        copyBtn.textContent = "COPY";
        copyBtn.classList.remove("is-done");
      }, 1600);
    });
  }
})();
