document.addEventListener("DOMContentLoaded", function () {
  /* --- Mobile nav toggle --- */
  var toggle = document.getElementById("navToggle");
  var nav = document.getElementById("siteNav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    nav.addEventListener("click", function (e) {
      if (e.target.tagName === "A") {
        nav.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  /* --- Scroll progress bar --- */
  var progress = document.getElementById("scrollProgress");
  if (progress) {
    function updateProgress() {
      var scrollTop = window.scrollY;
      var docHeight = document.documentElement.scrollHeight - window.innerHeight;
      var pct = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
      progress.style.width = pct + "%";
    }
    window.addEventListener("scroll", updateProgress, { passive: true });
    updateProgress();
  }

  /* --- Reveal on scroll --- */
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var revealEls = document.querySelectorAll(".reveal");
  if (reduceMotion || !("IntersectionObserver" in window)) {
    revealEls.forEach(function (el) { el.classList.add("is-visible"); });
  } else {
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15, rootMargin: "0px 0px -60px 0px" }
    );
    revealEls.forEach(function (el) { observer.observe(el); });
  }

  /* --- Testimonial carousel(s) --- */
  document.querySelectorAll("[data-carousel]").forEach(function (car) {
    var slides = car.querySelectorAll(".carousel-slide");
    var count = car.querySelector("[data-count]");
    if (!slides.length) return;
    var idx = 0, timer = null;
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    function show(n) {
      slides[idx].classList.remove("is-active");
      idx = (n + slides.length) % slides.length;
      slides[idx].classList.add("is-active");
      if (count) count.textContent = (idx + 1) + " / " + slides.length;
    }
    function stop() { if (timer) { clearInterval(timer); timer = null; } }
    function start() { if (reduce) return; stop(); timer = setInterval(function () { show(idx + 1); }, 6000); }
    var prev = car.querySelector("[data-prev]");
    var next = car.querySelector("[data-next]");
    if (prev) prev.addEventListener("click", function () { show(idx - 1); start(); });
    if (next) next.addEventListener("click", function () { show(idx + 1); start(); });
    car.addEventListener("mouseenter", stop);
    car.addEventListener("mouseleave", start);
    start();
  });
});
