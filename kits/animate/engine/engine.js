/* Reel engine: turns a reel's scenes.js + words.js into a 1080x1920 animation.
 *
 * Everything on screen is a pure function of time, so window.seek(t) can draw
 * any frame in any order. That is what lets tools/render.py export a smooth MP4
 * and lets tools/framecheck.py look at any moment of the reel.
 *
 * A reel folder holds:
 *   words.js   WORDS = [{w:'Airplane', s:1.12, e:1.40, em:false}, ...]   (made by tools/timing.py)
 *   scenes.js  REEL({ hud:'...', scenes:[ {at:'airplane food', type:'hook', title:'...'}, ... ] })
 * See ../REEL-FORMAT.md for every scene type and option.
 */
(function () {
'use strict';

/* ---------------- maths and easing ---------------- */
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const P = (t, s, d) => clamp((t - s) / Math.max(d, 1e-6));
const eo = x => 1 - Math.pow(1 - x, 3);
const eio = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
const back = x => { const c1 = 1.9, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };
const lerp = (a, b, k) => a + (b - a) * k;
const rnd = i => { const x = Math.sin(i * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };

const W = 1080, H = 1920;
const SAFE = { top: 300, bottom: 1340 };      // scene content lives between these lines
const EXIT = 0.22;                             // seconds a scene takes to leave
const WARN = [];
const warn = m => { WARN.push(m); console.warn(m); };

/* ---------------- text helpers ---------------- */
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
// *word* becomes an accent (serif italic, accent colour). Line breaks with \n.
const rich = s => esc(s).replace(/\*([^*]+)\*/g, '<span class="em">$1</span>').replace(/\n/g, '<br>');
// Split rich text into word spans so they can pop in one by one.
function wordsHTML(s) {
  const parts = [];
  String(s == null ? '' : s).split('\n').forEach((line, li) => {
    if (li) parts.push('<br>');
    line.replace(/\*([^*]+)\*([^\s*]*)|(\S+)/g, (m, em, tail, plain) => {
      if (em) { const ws = em.split(/\s+/); ws.forEach((w, i) => parts.push(`<span class="w em">${esc(w)}${i === ws.length - 1 ? esc(tail || '') : ''}</span>`)); }
      else parts.push(`<span class="w">${esc(plain)}</span>`);
      return m;
    });
  });
  return '<span class="wl">' + parts.join(' ') + '</span>';
}
function el(tag, cls, css, html) {
  const d = document.createElement(tag);
  if (cls) d.className = cls;
  if (css) d.style.cssText = css;
  if (html != null) d.innerHTML = html;
  return d;
}
// Shrink text until it fits its box. Runs once at build time, after fonts load.
function fit(node, maxW, maxH, start, min = 24) {
  let size = start;
  node.style.fontSize = size + 'px';
  node.style.maxWidth = maxW + 'px';
  while (size > min && (node.scrollWidth > maxW + 1 || node.scrollHeight > maxH + 1)) {
    size -= 2;
    node.style.fontSize = size + 'px';
  }
  if (node.scrollWidth > maxW + 1 || node.scrollHeight > maxH + 1)
    warn(`Text is too long to fit: "${node.textContent.slice(0, 60)}"`);
  return size;
}

/* ---------------- words and timing ---------------- */
const norm = s => String(s).toLowerCase().replace(/[’']/g, "'").replace(/[^a-z0-9'%$.]+/g, ' ').replace(/(^|\s)'|'(\s|$)/g, ' ').replace(/\.(?!\d)/g, ' ').trim();
let WORDS = [], NW = [], cursor = 0;
function phraseIndex(phrase, from) {
  const toks = norm(phrase).split(/\s+/).filter(Boolean);
  if (!toks.length) return -1;
  const tryFrom = start => {
    for (let i = start; i < NW.length; i++) {
      let ok = true;
      for (let j = 0; j < toks.length; j++) {
        const w = NW[i + j];
        if (w == null) { ok = false; break; }
        const last = j === toks.length - 1;
        if (!(w === toks[j] || (last && w.startsWith(toks[j])))) { ok = false; break; }
      }
      if (ok) return i;
    }
    return -1;
  };
  let i = tryFrom(from);
  if (i < 0) i = tryFrom(0);
  return i;
}
// at: number = seconds (absolute for scenes, after scene start for items); string = when that phrase is spoken
function timeOf(at, base, fallback) {
  if (typeof at === 'number') return base + at;
  if (typeof at === 'string' && at.trim()) {
    const i = phraseIndex(at, cursor);
    if (i >= 0) { cursor = i + 1; return WORDS[i].s; }
    warn(`Could not find the words "${at}" in the voiceover. Check scenes.js against script.md.`);
  }
  return fallback;
}

/* ---------------- background ---------------- */
let PARTS = [], HZ = [];
function buildBackground() {
  const g = document.getElementById('horizon');
  let h = '';
  const vx = 540, vy = 60;
  for (let i = -14; i <= 14; i++) {
    const x = 540 + i * 120;
    h += `<line x1="${vx + (x - vx) * 0.04}" y1="${vy}" x2="${vx + (x - vx) * 3.2}" y2="760" stroke="#2563EB" stroke-opacity=".16" stroke-width="2"/>`;
  }
  for (let i = 0; i < 12; i++) h += `<line class="hz" x1="0" x2="1080" y1="0" y2="0" stroke="#2563EB" stroke-opacity=".16" stroke-width="2"/>`;
  g.innerHTML = h;
  HZ = [...g.querySelectorAll('.hz')];
  const box = document.getElementById('parts');
  for (let i = 0; i < 26; i++) {
    const s = 4 + rnd(i) * 8;
    const c = i % 3 === 0 ? '#FFB547' : (i % 3 === 1 ? '#2563EB' : '#0FA898');
    const d = el('div', '', `position:absolute;width:${s}px;height:${s}px;border-radius:${i % 4 === 0 ? '2px' : '50%'};background:${c};opacity:.35`);
    box.appendChild(d);
    PARTS.push({ el: d, x: rnd(i + 40) * W, y: rnd(i + 80) * H, v: 12 + rnd(i + 9) * 30, a: rnd(i + 3) * 6 });
  }
}
function drawBackground(t, night) {
  PARTS.forEach(p => {
    const y = ((p.y - t * p.v) % H + H) % H;
    p.el.style.transform = `translate(${p.x + Math.sin(t * .6 + p.a) * 18}px,${y}px)`;
  });
  HZ.forEach((l, i) => {
    const k = ((i / 12) + t * 0.035) % 1;
    const y = 60 + Math.pow(k, 2.2) * 700;
    l.setAttribute('y1', y); l.setAttribute('y2', y);
    l.setAttribute('stroke-opacity', (0.05 + k * 0.2).toFixed(3));
  });
  document.getElementById('orbit').style.transform = `rotate(${t * 2.2}deg)`;
  document.getElementById('sun').style.transform = `translate(${Math.sin(t * .2) * 30}px,${Math.cos(t * .17) * 20}px) scale(${1 + Math.sin(t * .5) * .03})`;
  document.getElementById('blobA').style.transform = `translate(${Math.sin(t * .23) * 60}px,${Math.cos(t * .19) * 40}px)`;
  document.getElementById('blobB').style.transform = `translate(${Math.cos(t * .21) * 50}px,${Math.sin(t * .27) * 60}px)`;
  document.getElementById('night').style.opacity = night;
}

/* ---------------- animation helpers handed to every scene ---------------- */
// Pop an element in at time `a` (scene-local seconds): fade + rise + slight overshoot.
function pop(node, lt, a, o = {}) {
  const d = o.dur || .42, dy = o.dy == null ? 40 : o.dy, s0 = o.scale == null ? .9 : o.scale;
  const k = eo(P(lt, a, d)), s = back(P(lt, a, d));
  node.style.opacity = k;
  node.style.transform = `${node.dataset.tf || ''} translateY(${(1 - s) * dy}px) scale(${s0 + (1 - s0) * Math.min(1.05, s)})`;
  return k;
}
// Reveal word spans one by one from time a, `gap` seconds apart.
function popWords(container, lt, a, gap = .07) {
  const ws = container.querySelectorAll('.w');
  ws.forEach((w, i) => {
    const k = eo(P(lt, a + i * gap, .32)), s = back(P(lt, a + i * gap, .32));
    w.style.opacity = k;
    w.style.transform = `translateY(${(1 - s) * 30}px)`;
    w.style.display = 'inline-block';
  });
  return a + ws.length * gap;
}
function typeText(node, text, lt, a, cps = 28, caret = true) {
  const n = Math.floor(clamp((lt - a) * cps, 0, text.length));
  const blink = caret && (Math.floor(lt * 2.2) % 2 === 0 || n < text.length);
  node.innerHTML = esc(text.slice(0, n)) + (caret ? `<span style="display:inline-block;width:4px;height:1em;vertical-align:-.12em;margin-left:3px;background:var(--acc);opacity:${blink ? 1 : 0}"></span>` : '');
  return n >= text.length;
}
function count(node, from, to, lt, a, d = 1.1, decimals = 0, prefix = '', suffix = '') {
  const v = lerp(from, to, eo(P(lt, a, d)));
  const s = v.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
  node.textContent = prefix + s + suffix;
}
const HELP = { clamp, P, eo, eio, back, lerp, rnd, pop, popWords, typeText, count, esc, rich, wordsHTML, el, fit };

/* ---------------- scene types ---------------- */
// Each type builds its DOM into `root` and returns update(lt) where lt = seconds since the scene started.
// `S` is the scene object; `T(at, def)` turns an item's `at` into scene-local seconds.
const TYPES = {};

TYPES.hook = (S, root, T) => {
  const top = 330;
  const orb = el('div', 'abs', `left:340px;top:${top}px;width:400px;height:400px`);
  const r1 = el('div', 'ring', 'left:-40px;top:-40px;width:480px;height:480px');
  const r2 = el('div', 'ring dash', 'left:-90px;top:-90px;width:580px;height:580px');
  const ic = el('div', 'iconOrb center', 'left:60px;top:60px;width:280px;height:280px;font-size:150px', esc(S.icon || '✨'));
  orb.append(r2, r1, ic);
  const kick = el('div', 'kicker abs', `left:60px;right:60px;top:${top + 520}px;text-align:center`, esc(S.kicker || ''));
  const title = el('div', 'headline abs', `left:60px;right:60px;top:${top + 580}px;text-align:center`, wordsHTML(S.title));
  root.append(orb, kick, title);
  fit(title, 960, S.sub ? 300 : 420, S.size || 132, 60);
  let sub;
  if (S.sub) { sub = el('div', 'chip holo abs', `left:50%;top:${SAFE.bottom - 110}px`, rich(S.sub)); sub.dataset.tf = 'translateX(-50%)'; root.append(sub); }
  const tSub = T(S.subAt, .9);
  return lt => {
    pop(orb, lt, 0, { dy: 60, scale: .7, dur: .5 });
    ic.style.transform = `translateY(${Math.sin(lt * 2) * 10}px)`;
    r1.style.transform = `rotate(${lt * 20}deg) scale(${1 + Math.sin(lt * 1.6) * .03})`;
    r2.style.transform = `rotate(${-lt * 12}deg)`;
    pop(kick, lt, .1, { dy: 20 });
    popWords(title, lt, .12, .07);
    if (sub) pop(sub, lt, tSub);
  };
};

TYPES.statement = (S, root, T) => {
  const box = el('div', 'abs', `left:60px;right:60px;top:${SAFE.top}px;height:${SAFE.bottom - SAFE.top}px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:34px`);
  let icon, kick, body;
  if (S.icon) { icon = el('div', 'iconOrb center', 'position:relative;width:200px;height:200px;font-size:110px;flex:none', esc(S.icon)); box.append(icon); }
  if (S.kicker) { kick = el('div', 'kicker', '', esc(S.kicker)); box.append(kick); }
  const title = el('div', 'headline', 'width:100%', wordsHTML(S.title));
  box.append(title);
  if (S.body) { body = el('div', 'body', 'max-width:900px', rich(S.body)); box.append(body); }
  root.append(box);
  fit(title, 960, S.body ? 520 : 700, S.size || 140, 56);
  if (body) fit(body, 900, 260, 44, 28);
  const tBody = T(S.bodyAt, .7);
  return lt => {
    if (icon) { pop(icon, lt, 0, { scale: .6 }); icon.style.translate = `0 ${Math.sin(lt * 2) * 8}px`; }
    if (kick) pop(kick, lt, .05, { dy: 20 });
    popWords(title, lt, .1, .07);
    if (body) pop(body, lt, tBody);
  };
};

TYPES.stat = (S, root, T) => {
  const box = el('div', 'abs', `left:60px;right:60px;top:${SAFE.top + 40}px;height:${SAFE.bottom - SAFE.top - 80}px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:24px`);
  const kick = S.kicker ? el('div', 'kicker', '', esc(S.kicker)) : null;
  const num = el('div', 'num acc', 'white-space:nowrap', '0');
  const label = el('div', 'headline', 'font-size:72px', rich(S.label || ''));
  const halo = el('div', 'ring dash abs', 'left:190px;top:190px;width:580px;height:580px;opacity:.6');
  root.append(halo);
  if (kick) box.append(kick);
  box.append(num, label);
  root.append(box);
  const to = Number(S.value) || 0, from = S.from != null ? Number(S.from) : 0;
  const dec = S.decimals || 0, pre = S.prefix || '', suf = S.suffix || '';
  num.textContent = pre + to.toLocaleString('en-US', { minimumFractionDigits: dec, maximumFractionDigits: dec }) + suf;
  fit(num, 960, 360, 330, 120);
  fit(label, 960, 300, 72, 36);
  const tL = T(S.labelAt, .5);
  return lt => {
    if (kick) pop(kick, lt, 0, { dy: 20 });
    pop(num, lt, 0, { scale: .7, dur: .5 });
    count(num, from, to, lt, .05, S.countDur || 1.1, dec, pre, suf);
    halo.style.transform = `rotate(${lt * 15}deg) scale(${.9 + eo(P(lt, 0, .6)) * .1})`;
    halo.style.opacity = .6 * eo(P(lt, 0, .5));
    pop(label, lt, tL);
  };
};

TYPES.list = (S, root, T) => {
  const items = S.items || [];
  const grid = S.layout === 'grid';
  const titleH = S.title ? 230 : 0;
  const title = S.title ? el('div', 'headline abs', `left:60px;right:60px;top:${SAFE.top}px;height:${titleH - 30}px;text-align:center;display:flex;align-items:center;justify-content:center`, wordsHTML(S.title)) : null;
  if (title) { root.append(title); fit(title, 960, titleH - 30, 110, 50); }
  const areaTop = SAFE.top + titleH, areaH = SAFE.bottom - areaTop;
  const tiles = [];
  if (grid) {
    const cols = items.length <= 4 ? 2 : 3, rows = Math.ceil(items.length / cols);
    const gap = 26, tw = (960 - gap * (cols - 1)) / cols, th = Math.min(300, (areaH - gap * (rows - 1)) / rows);
    const y0 = areaTop + (areaH - (rows * th + gap * (rows - 1))) / 2;
    items.forEach((it, i) => {
      const c = i % cols, r = Math.floor(i / cols);
      const t = el('div', 'tile center', `left:${60 + c * (tw + gap)}px;top:${y0 + r * (th + gap)}px;width:${tw}px;height:${th}px;flex-direction:column;gap:14px;text-align:center;padding:20px`);
      if (it.icon) t.append(el('div', '', `font-size:${Math.min(96, th * .36)}px;line-height:1`, esc(it.icon)));
      const lab = el('div', '', 'font-weight:800;line-height:1.15', rich(it.text));
      t.append(lab); root.append(t); fit(lab, tw - 40, th * .45, 40, 22);
      tiles.push(t);
    });
  } else {
    const gap = 22, th = Math.min(170, (areaH - gap * (items.length - 1)) / Math.max(1, items.length));
    const y0 = areaTop + (areaH - (items.length * th + gap * (items.length - 1))) / 2;
    items.forEach((it, i) => {
      const t = el('div', 'tile', `left:60px;top:${y0 + i * (th + gap)}px;width:960px;height:${th}px;display:flex;align-items:center;gap:28px;padding:0 36px`);
      const badge = it.icon ? el('div', 'center', `width:${th * .62}px;height:${th * .62}px;border-radius:24px;background:var(--holo);font-size:${th * .36}px;flex:none`, esc(it.icon))
        : el('div', 'center mono', `width:${th * .56}px;height:${th * .56}px;border-radius:50%;background:var(--acc);color:#fff;font-size:${th * .24}px;font-weight:600;flex:none`, String(i + 1).padStart(2, '0'));
      const lab = el('div', '', 'font-weight:800;line-height:1.15;flex:1', rich(it.text));
      t.append(badge, lab); root.append(t); fit(lab, 960 - 72 - th * .62 - 28, th - 20, 48, 24);
      tiles.push(t);
    });
  }
  const times = items.map((it, i) => T(it.at, .35 + i * .55));
  return lt => {
    if (title) popWords(title, lt, 0, .06);
    tiles.forEach((t, i) => pop(t, lt, times[i], { dy: 50 }));
  };
};
TYPES.list.events = (S, T) => (S.items || []).map((it, i) => ({ t: T(it.at, .35 + i * .55), kind: 'pop' }));

TYPES.compare = (S, root, T) => {
  const title = S.title ? el('div', 'headline abs', `left:60px;right:60px;top:${SAFE.top}px;height:200px;text-align:center;display:flex;align-items:center;justify-content:center`, wordsHTML(S.title)) : null;
  if (title) { root.append(title); fit(title, 960, 200, 104, 50); }
  const top = SAFE.top + (title ? 240 : 120), h = SAFE.bottom - top - 40;
  const mk = (side, x, accent) => {
    const t = el('div', 'tile center', `left:${x}px;top:${top}px;width:440px;height:${h}px;flex-direction:column;gap:26px;text-align:center;padding:30px;${accent ? 'border:3px solid var(--acc);box-shadow:0 20px 60px rgba(37,99,235,.28)' : ''}`);
    if (side.icon) t.append(el('div', '', 'font-size:110px;line-height:1', esc(side.icon)));
    const v = el('div', 'num ' + (accent ? 'acc' : ''), '', rich(side.value || ''));
    const l = el('div', 'kicker', `color:${accent ? 'var(--acc)' : 'var(--muted)'};letter-spacing:4px`, esc(side.label || ''));
    t.append(v, l); root.append(t);
    fit(v, 380, h * .4, 150, 50); fit(l, 380, 120, 30, 18);
    return t;
  };
  const L = mk(S.left || {}, 60, false), R = mk(S.right || {}, 580, true);
  const vs = el('div', 'center mono abs', `left:490px;top:${top + h / 2 - 50}px;width:100px;height:100px;border-radius:50%;background:var(--ink);color:#fff;font-size:30px;font-weight:600;z-index:2`, esc(S.vs || 'VS'));
  root.append(vs);
  const tL = T((S.left || {}).at, .15), tR = T((S.right || {}).at, .9);
  return lt => {
    if (title) popWords(title, lt, 0, .06);
    pop(L, lt, tL, { dy: 0, scale: .85 });
    pop(vs, lt, Math.min(tL, tR) + .3, { dy: 0, scale: .4 });
    pop(R, lt, tR, { dy: 0, scale: .85 });
  };
};
TYPES.compare.events = (S, T) => [{ t: T((S.right || {}).at, .9), kind: 'pop' }];

TYPES.chat = (S, root, T) => {
  const title = S.title ? el('div', 'kicker abs', `left:60px;right:60px;top:${SAFE.top}px;text-align:center`, esc(S.title)) : null;
  if (title) root.append(title);
  const win = el('div', 'glass', `left:40px;top:${SAFE.top + (title ? 70 : 0)}px;width:1000px;height:${SAFE.bottom - SAFE.top - (title ? 70 : 0)}px;border-radius:44px`);
  root.append(win);
  const msgs = S.messages || [];
  let y = 60;
  const B = msgs.map((m, i) => {
    const b = el('div', 'bubble ' + (m.from === 'you' ? 'you' : 'ai'), `top:${y}px`, `<span class="who">${esc(m.who || (m.from === 'you' ? 'You' : 'Claude'))}</span><span class="tx"></span>`);
    win.append(b);
    b.querySelector('.tx').innerHTML = rich(m.text);
    b.style.width = Math.ceil(b.getBoundingClientRect().width + 1) + 'px';   // keep the final size while typing
    const hgt = b.offsetHeight;
    y += hgt + 34;
    return { b, m, tx: b.querySelector('.tx'), t: T(m.at, .2 + i * 1.1) };
  });
  const maxH = SAFE.bottom - SAFE.top - (title ? 70 : 0);
  if (y > maxH) warn('Chat scene: too many or too long messages. Shorten them or split into two scenes.');
  const wh = Math.min(maxH, Math.max(420, y + 26));
  win.style.height = wh + 'px';
  win.style.top = (SAFE.top + (title ? 70 : 0) + (maxH - wh) / 2) + 'px';
  if (title) title.style.top = (parseFloat(win.style.top) - 70) + 'px';
  return lt => {
    if (title) pop(title, lt, 0, { dy: 20 });
    B.forEach(o => {
      pop(o.b, lt, o.t, { dy: 40, scale: .92 });
      if (o.m.from === 'you' && o.m.type !== false) typeText(o.tx, o.m.text.replace(/\*/g, ''), lt, o.t + .1, o.m.cps || 30, false);
    });
  };
};
TYPES.chat.events = (S, T) => (S.messages || []).map((m, i) => ({ t: T(m.at, .2 + i * 1.1), kind: m.from === 'you' ? 'type' : 'pop' }));

TYPES.image = (S, root, T) => {
  const iw = S.width || 1200, ih = S.height || 800;   // the image's real pixel size
  const bar = S.bar !== false;
  let top = SAFE.top, title;
  if (S.title) {
    title = el('div', 'headline abs', `left:60px;right:60px;top:${SAFE.top}px;height:190px;text-align:center;display:flex;align-items:center;justify-content:center`, wordsHTML(S.title));
    root.append(title); fit(title, 960, 190, 100, 46); top += 220;
  }
  const cw = 960, ch = Math.min(S.cardHeight || 900, SAFE.bottom - top);
  const card = el('div', 'shot', `left:60px;top:${top}px;width:${cw}px;height:${ch}px`);
  card.innerHTML = (bar ? `<div class="sbar"><span class="dots3"><i style="background:#FF5F57"></i><i style="background:#FEBC2E"></i><i style="background:#28C840"></i></span><span class="url">${esc(S.url || '')}</span></div>` : '')
    + `<div class="svp${bar ? '' : ' nobar'}"><div class="sin"><img src="${window.REEL_DIR + esc(S.src)}" width="${iw}" height="${ih}"></div></div>`;
  root.append(card);
  const vp = card.querySelector('.svp'), sin = card.querySelector('.sin');
  const vw = cw - 6, vh = ch - 6 - (bar ? 54 : 0);
  const fitZ = Math.min(vw / iw, vh / ih) > 0 ? vw / iw : 1;          // default: image fills the width
  const keys = (S.focus && S.focus.length ? S.focus : [{ at: 0, x: iw / 2, y: Math.min(ih / 2, vh / fitZ / 2), zoom: 1 }])
    .map((k, i) => ({ t: T(k.at, i * 1.2), x: k.x, y: k.y, z: (k.zoom || 1) * fitZ }));
  const marks = (S.marks || []).map((m, i) => {
    const d = el('div', 'mark', `left:${m.x}px;top:${m.y}px;width:${m.w}px;height:${m.h}px;opacity:0`);
    sin.append(d);
    return { d, t: T(m.at, .6 + i * .8) };
  });
  const view = lt => {
    let a = keys[0], b = keys[0];
    for (const k of keys) { if (k.t <= lt) a = k; }
    const ai = keys.indexOf(a); b = keys[Math.min(ai + 1, keys.length - 1)];
    const k = b === a ? 0 : eio(P(lt, b.t - .7, .7));
    const z = lerp(a.z, b.z, k), x = lerp(a.x, b.x, k), y = lerp(a.y, b.y, k);
    let tx = vw / 2 - x * z, ty = vh / 2 - y * z;
    tx = Math.min(0, Math.max(vw - iw * z, tx)); ty = Math.min(0, Math.max(vh - ih * z, ty));
    if (iw * z < vw) tx = (vw - iw * z) / 2;
    if (ih * z < vh) ty = (vh - ih * z) / 2;
    sin.style.transform = `translate(${tx}px,${ty}px) scale(${z})`;
  };
  return lt => {
    if (title) popWords(title, lt, 0, .06);
    pop(card, lt, .05, { dy: 70, scale: .94, dur: .5 });
    view(lt);
    marks.forEach(m => { const k = eo(P(lt, m.t, .45)); m.d.style.opacity = k > 0 ? 1 : 0; m.d.style.transform = `scaleX(${k})`; });
  };
};
TYPES.image.events = (S, T) => (S.marks || []).map((m, i) => ({ t: T(m.at, .6 + i * .8), kind: 'tick' }));

TYPES.steps = (S, root, T) => {
  const steps = S.steps || [];
  const title = S.title ? el('div', 'headline abs', `left:60px;right:60px;top:${SAFE.top}px;height:200px;text-align:center;display:flex;align-items:center;justify-content:center`, wordsHTML(S.title)) : null;
  if (title) { root.append(title); fit(title, 960, 200, 104, 50); }
  const top = SAFE.top + (title ? 240 : 40), avail = SAFE.bottom - top, gap = 20;
  const th = Math.min(150, (avail - gap * (steps.length - 1)) / Math.max(1, steps.length));
  const active = S.active == null ? steps.length - 1 : S.active;
  const rows = steps.map((s, i) => {
    const on = i === active, done = i < active;
    const r = el('div', 'tile', `left:${on ? 40 : 90}px;top:${top + i * (th + gap)}px;width:${on ? 1000 : 900}px;height:${th}px;display:flex;align-items:center;gap:26px;padding:0 34px;${on ? 'border:3px solid var(--acc);box-shadow:0 20px 60px rgba(37,99,235,.3)' : 'opacity:.9'}`);
    const n = el('div', 'center mono', `width:${th * .56}px;height:${th * .56}px;border-radius:50%;flex:none;font-weight:600;font-size:${th * .22}px;${done ? 'background:var(--ok);color:#fff' : on ? 'background:var(--acc);color:#fff' : 'background:#E8EEF8;color:var(--muted)'}`, done ? '✓' : String(i + 1));
    const lab = el('div', '', `font-weight:800;flex:1;color:${on || done ? 'var(--ink)' : 'var(--muted)'}`, rich(s));
    r.append(n, lab); root.append(r); fit(lab, (on ? 1000 : 900) - 68 - th * .56 - 26, th - 16, on ? 50 : 42, 22);
    r._n = n; r._lab = lab;
    return r;
  });
  // flow: light the steps up one by one (seconds per step); flowStart = when the first one lights
  const paint = (r, i, k) => {
    const on = i === k, done = i < k;
    r.style.left = (on ? 40 : 90) + 'px'; r.style.width = (on ? 1000 : 900) + 'px';
    r.style.border = on ? '3px solid var(--acc)' : '2px solid #fff';
    r.style.boxShadow = on ? '0 20px 60px rgba(37,99,235,.3)' : '';
    r._n.style.background = done ? 'var(--ok)' : on ? 'var(--acc)' : '#E8EEF8';
    r._n.style.color = done || on ? '#fff' : 'var(--muted)';
    r._n.textContent = done ? '✓' : String(i + 1);
    r._lab.style.color = on || done ? 'var(--ink)' : 'var(--muted)';
  };
  const flowStart = T(S.flowAt, S.flowStart != null ? S.flowStart : .05 + steps.length * .08 + .25);
  return lt => {
    if (title) popWords(title, lt, 0, .06);
    rows.forEach((r, i) => pop(r, lt, .05 + i * .08, { dy: 30 }));
    if (S.flow) {
      const k = lt < flowStart ? -1 : Math.floor((lt - flowStart) / S.flow);
      rows.forEach((r, i) => {
        paint(r, i, k);
        if (i === k) { const q = P(lt, flowStart + k * S.flow, .25); r.style.transform += ` scale(${1 + .04 * Math.sin(q * Math.PI)})`; }
      });
    }
  };
};

TYPES.steps.events = (S, T) => {
  if (!S.flow) return [];
  const n = (S.steps || []).length, st = T(S.flowAt, S.flowStart != null ? S.flowStart : .05 + n * .08 + .25);
  return (S.steps || []).map((_, i) => ({ t: st + i * S.flow, kind: 'tick' }));
};

TYPES.cta = (S, root, T) => {
  const kw = (S.keyword || 'KEYWORD').toUpperCase();
  const head = el('div', 'headline abs', `left:60px;right:60px;top:${SAFE.top}px;height:220px;text-align:center;display:flex;align-items:center;justify-content:center`, wordsHTML(S.title || 'Want it?'));
  root.append(head); fit(head, 960, 220, 120, 56);
  const panel = el('div', 'glass', `left:90px;top:${SAFE.top + 260}px;width:900px;height:${SAFE.bottom - SAFE.top - 280}px;border-radius:40px;background:#fff`);
  const ph = SAFE.bottom - SAFE.top - 280;
  panel.innerHTML = `<div class="abs" style="left:0;right:0;top:0;height:90px;border-bottom:2px solid #EEF1F5;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:32px">Comments</div>
   <div class="abs c1" style="left:40px;top:130px;right:40px;display:flex;gap:22px;align-items:flex-start"><div style="width:72px;height:72px;border-radius:50%;background:linear-gradient(135deg,#9CC0FF,#FFD8B0);flex:none"></div><div><div style="font-weight:800;font-size:28px">${esc(S.user1 || 'maya.codes')} <span style="color:#8A96A8;font-weight:500">2m</span></div><div style="font-size:30px;margin-top:6px">${esc(kw)} 🙌</div></div></div>
   <div class="abs c2" style="left:40px;top:250px;right:40px;display:flex;gap:22px;align-items:flex-start"><div style="width:72px;height:72px;border-radius:50%;background:linear-gradient(135deg,#B7F0E4,#C9D8FF);flex:none"></div><div><div style="font-weight:800;font-size:28px">${esc(S.user2 || 'arjun.builds')} <span style="color:#8A96A8;font-weight:500">1m</span></div><div style="font-size:30px;margin-top:6px">${esc(kw)}</div></div></div>
   <div class="abs dm chip holo" style="left:40px;top:370px;font-size:28px">📩 ${esc(S.dm || 'Sent! Check your DMs')}</div>
   <div class="abs" style="left:30px;right:30px;bottom:30px;height:96px;border-radius:999px;border:2px solid #E1E6EE;display:flex;align-items:center;padding:0 16px 0 34px;gap:16px"><div class="ty" style="flex:1;font-size:38px;font-weight:800;color:var(--ink)"></div><div class="post center" style="height:64px;padding:0 30px;border-radius:999px;background:var(--acc);color:#fff;font-weight:800;font-size:28px">Post</div></div>`;
  root.append(panel);
  if (ph < 520) panel.querySelector('.dm').style.display = 'none';
  const c1 = panel.querySelector('.c1'), c2 = panel.querySelector('.c2'), dm = panel.querySelector('.dm'), ty = panel.querySelector('.ty'), post = panel.querySelector('.post');
  const tType = T(S.keywordAt, .7);
  return lt => {
    popWords(head, lt, 0, .06);
    pop(panel, lt, .1, { dy: 60, scale: .95 });
    pop(c1, lt, .35, { dy: 20 }); pop(c2, lt, .55, { dy: 20 });
    typeText(ty, kw, lt, tType, 9);
    const pk = P(lt, tType + kw.length / 9 + .2, .25);
    post.style.transform = `scale(${1 - Math.sin(pk * Math.PI) * .12})`;
    pop(dm, lt, tType + kw.length / 9 + .55, { dy: 20 });
  };
};
TYPES.cta.events = (S, T) => {
  const kw = (S.keyword || 'KEYWORD'); const a = T(S.keywordAt, .7);
  return [{ t: a, kind: 'type' }, { t: a + kw.length / 9 + .2, kind: 'tick' }, { t: a + kw.length / 9 + .55, kind: 'ding' }];
};

// Escape hatch: write your own scene. html goes into the scene; update(root, lt, H) animates it.
TYPES.custom = (S, root, T) => {
  root.innerHTML = S.html || '';
  if (typeof S.setup === 'function') S.setup(root, HELP, T);
  return lt => { if (typeof S.update === 'function') S.update(root, lt, HELP, T); };
};

/* ---------------- captions ---------------- */
let GROUPS = [];
function buildCaptions(maxWords, maxChars) {
  GROUPS = [];
  let g = null;
  WORDS.forEach((w, i) => {
    const text = String(w.w);
    const len = g ? g.words.reduce((a, x) => a + x.w.length + 1, 0) : 0;
    if (!g || g.words.length >= maxWords || len + text.length > maxChars || (i > 0 && w.s - WORDS[i - 1].e > .45)) {
      g = { words: [], s: w.s };
      GROUPS.push(g);
    }
    g.words.push(w);
    if (/[.,!?;:]$/.test(text)) g = null;
  });
  GROUPS.forEach((g, i) => {
    const last = g.words[g.words.length - 1];
    const next = GROUPS[i + 1];
    g.e = next ? Math.min(next.s, last.e + .5) : last.e + .6;
  });
}
let capShown = -1;
function drawCaptions(t, show) {
  const cap = document.getElementById('cap');
  if (!show) { cap.innerHTML = ''; capShown = -1; return; }
  const gi = GROUPS.findIndex(g => t >= g.s - .04 && t < g.e);
  if (gi < 0) { if (capShown !== -1) { cap.innerHTML = ''; capShown = -1; } return; }
  const g = GROUPS[gi];
  if (capShown !== gi) {
    cap.innerHTML = g.words.map(w => `<span class="${w.em ? 'em' : ''}">${esc(String(w.w).replace(/[*]/g, ''))}</span>`).join(' ');
    capShown = gi;
  }
  const spans = cap.children;
  g.words.forEach((w, i) => {
    const on = t >= w.s - .02;
    spans[i].classList.toggle('on', on && !w.em && (i === g.words.length - 1 || t < g.words[i + 1].s));
    spans[i].style.opacity = on ? 1 : .35;
  });
  const k = back(P(t, g.s - .04, .22));
  cap.style.transform = `scale(${.86 + .14 * Math.min(1.04, k)})`;
}

/* ---------------- the reel ---------------- */
let CFG = null, SCENES = [], DUR = 10;
window.REEL = cfg => { CFG = cfg; };

function build() {
  WORDS = (window.WORDS || []).filter(w => w && w.w != null && isFinite(w.s));
  NW = WORDS.map(w => norm(w.w).replace(/\s+/g, ''));
  if (!CFG) throw new Error('scenes.js did not call REEL({...}).');
  const cfg = CFG;
  if (cfg.theme) document.body.classList.add('theme-' + cfg.theme);
  if (cfg.colors) Object.entries(cfg.colors).forEach(([k, v]) => document.documentElement.style.setProperty('--' + k, v));
  const lastWord = WORDS.length ? WORDS[WORDS.length - 1].e : 5;
  DUR = cfg.duration || (lastWord + (cfg.tail == null ? 1.2 : cfg.tail));
  buildBackground();
  document.getElementById('hudL').textContent = cfg.hud || '';

  // 1. When does each scene start?
  cursor = 0;
  const list = cfg.scenes || [];
  let prev = 0;
  list.forEach((S, i) => {
    S._start = i === 0 ? timeOf(S.at, 0, 0) : timeOf(S.at, 0, prev + 2.5);
    if (S._start < prev) { warn(`Scene ${i + 1} (${S.type}) starts before the scene above it. Check its "at".`); S._start = prev + .5; }
    prev = S._start;
  });
  list.forEach((S, i) => { S._end = i + 1 < list.length ? list[i + 1]._start : DUR; });

  // 2. Build each scene. Item times are resolved after the scene's start so phrases match in order.
  const host = document.getElementById('scenes');
  const events = [];
  list.forEach((S, i) => {
    const type = TYPES[S.type];
    const root = el('div', 'scene' + (S.dark ? ' dark' : ''));
    root.style.visibility = 'hidden';
    host.appendChild(root);
    cursor = Math.max(0, phraseIndex(typeof S.at === 'string' ? S.at : '', 0));
    const T = (at, def) => {
      const v = timeOf(at, 0, null);
      if (typeof at === 'number') return at;
      return v == null ? def : Math.max(0, v - S._start);
    };
    if (!type) { warn(`Unknown scene type "${S.type}" in scene ${i + 1}.`); S._update = () => {}; }
    else {
      try {
        S._update = type(S, root, T);
        if (type.events) type.events(S, T).forEach(e => { if (e.t != null && S._start + e.t < S._end) events.push({ t: S._start + e.t, kind: e.kind }); });
      } catch (e) { warn(`Scene ${i + 1} (${S.type}) failed to build: ${e.message}`); S._update = () => {}; }
    }
    (S.sounds || []).forEach(s => events.push({ t: S._start + T(s.at, 0), kind: s.kind || 'pop' }));
    S._root = root;
    events.push({ t: S._start, kind: i === 0 ? 'boom' : (S.dark || (list[i - 1] && list[i - 1].dark) ? 'boom' : 'cut') });
    SCENES.push(S);
  });
  buildCaptions(cfg.captionWords || 3, cfg.captionChars || 18);

  events.sort((a, b) => a.t - b.t);
  window.TIMELINE = {
    duration: DUR, fps: cfg.fps || 30, voice: cfg.voice || 'voice.wav',
    scenes: SCENES.map(S => ({ type: S.type, start: +S._start.toFixed(3), end: +S._end.toFixed(3), dark: !!S.dark })),
    events: events.map(e => ({ t: +e.t.toFixed(3), kind: e.kind })),
    warnings: WARN
  };
}

function seek(t) {
  t = clamp(t, 0, DUR);
  let night = 0, dark = false, caps = CFG.captions !== false, hud = CFG.hud || '';
  let punch = 0;
  SCENES.forEach((S, i) => {
    const vis = t >= S._start - .001 && t < S._end;
    S._root.style.visibility = vis ? 'visible' : 'hidden';
    // night fades in over the first .35 s of a dark scene
    if (S.dark) night = Math.max(night, (t >= S._start - .2 && t < S._end + .2) ? eio(P(t, S._start - .2, .35)) * (1 - eio(P(t, S._end - .15, .35))) : 0);
    if (!vis) return;
    dark = !!S.dark;
    if (S.captions === false) caps = false;
    if (S.hud != null) hud = S.hud;
    const lt = t - S._start;
    S._update(lt);
    // leave: last EXIT seconds fade and lift
    const out = eio(P(t, S._end - EXIT, EXIT));
    const isLast = i === SCENES.length - 1;
    S._root.style.opacity = isLast ? 1 : 1 - out;
    S._root.style.transform = isLast ? '' : `translateY(${-out * 40}px)`;
    if (S.punch !== false) punch = Math.max(punch, 1 - eo(P(lt, 0, .55)));
  });
  document.body.classList.toggle('dark', dark);
  drawBackground(t, night);
  const cam = document.getElementById('cam');
  const drift = `translate(${Math.sin(t * .35) * 6}px,${Math.cos(t * .29) * 8}px)`;
  cam.style.transform = `${drift} scale(${1.012 + Math.sin(t * .4) * .006 + punch * .035})`;
  // white flash on scenes that ask for it
  let fl = 0;
  SCENES.forEach(S => { if (S.flash) fl = Math.max(fl, 1 - eo(P(t, S._start, .28))) * (t >= S._start ? 1 : 0); });
  document.getElementById('flash').style.opacity = fl * .85;
  document.getElementById('hudL').textContent = hud;
  const si = SCENES.findIndex(S => t >= S._start && t < S._end);
  document.getElementById('hudR').textContent = CFG.counter === false ? '' : `${String(Math.max(0, si) + 1).padStart(2, '0')} / ${String(SCENES.length).padStart(2, '0')}`;
  drawCaptions(t, caps);
  return true;
}

/* ---------------- start / preview ---------------- */
async function start(q) {
  try { if (document.fonts && document.fonts.ready) await document.fonts.ready; } catch (e) {}
  // wait for images used by scenes
  build();
  const imgs = [...document.images];
  await Promise.all(imgs.map(im => im.complete ? 0 : new Promise(r => { im.onload = im.onerror = r; })));
  imgs.forEach(im => { if (!im.naturalWidth) warn(`Image not found: ${im.getAttribute('src')}`); });
  window.TIMELINE.warnings = WARN;
  window.seek = seek;
  seek(+(q.get('t') || 0));
  window.READY = true;
  if (q.get('play') === '1') preview();
}
function preview() {
  const a = new Audio(window.REEL_DIR + (CFG.voice || 'voice.wav'));
  const t0 = performance.now();
  let useAudio = false;
  a.play().then(() => { useAudio = true; }).catch(() => {});
  const loop = () => {
    const t = useAudio ? a.currentTime : (performance.now() - t0) / 1000 % DUR;
    seek(t);
    requestAnimationFrame(loop);
  };
  loop();
  document.body.addEventListener('click', () => { a.currentTime = 0; a.play(); useAudio = true; });
}
function fail(e) {
  window.READY = true;
  window.FAILED = String(e && e.message || e);
  const box = el('div', '', ''); box.id = 'err'; box.textContent = 'Reel could not load:\n' + window.FAILED;
  document.getElementById('stage').append(box);
}
window.ENGINE = { start: (q) => start(q).catch(fail), fail, TYPES, HELP };
})();
