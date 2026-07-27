# Site Starter Kit

A one-page marketing/proposal site template. Plain HTML + CSS + vanilla JS — no build step. Drop it on GitHub Pages, Netlify, or any static host.

## Files
- `index.html` — the page, built from reusable section blocks with placeholder copy.
- `css/styles.css` — the full design system. Rebrand by editing the tokens in `:root`.
- `js/main.js` — scroll-progress bar, scroll-reveal animations, mobile nav.

## How to reuse
1. **Rebrand:** edit the 4 brand colors + font in `:root` at the top of `styles.css`.
2. **Rename:** replace "Your Project Name" and the `<title>`/meta tags.
3. **Write content:** each `<section>` follows the same formula —
   `eyebrow → h2 → lede → a grid of items`. Copy a block, change the words.
4. **Alternate backgrounds:** switch between `class="section"` and `class="section section-alt"`
   down the page. Use `class="section band"` **once**, for your most important section.
5. **Animate:** add `class="reveal"` to anything you want to fade/rise in on scroll.

## Components included
Hero · pillars (quick value props) · logo/credibility row · dark stat band ·
card grid · two-column "yes/no" list · 16:9 video embed · timeline ·
closing statement · FAQ accordion · footer.

## Preview locally
```
python3 -m http.server 8000
```
Then open http://localhost:8000
