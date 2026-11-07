// Scenes for: why airplane food tastes so bland
// Told as a short story in the "story" theme (calm, cinematic). See REEL-FORMAT.md.

// An airplane window with clouds drifting past. dim = how dark the sky inside is (0..1).
const windowHTML = (id, top, dim) => `
  <div id="${id}" class="abs" style="left:290px;top:${top}px;width:500px;height:680px;border-radius:250px;
       background:#E9E3D9;box-shadow:0 40px 90px rgba(0,0,0,.45),inset 0 0 0 18px #D6CEC1;opacity:0">
    <div class="abs" style="left:46px;top:46px;right:46px;bottom:46px;border-radius:210px;overflow:hidden;
         background:linear-gradient(180deg,${dim ? '#1B2540 0%,#3A3550 60%,#7A4A48 100%' : '#6F8FC8 0%,#B9B7D6 55%,#F2B98A 100%'})">
      <div class="cl abs" style="left:-80px;top:330px;width:520px;height:200px;background:radial-gradient(ellipse at center,rgba(255,255,255,${dim ? .25 : .85}) 0%,rgba(255,255,255,0) 70%)"></div>
      <div class="cl abs" style="left:160px;top:430px;width:460px;height:180px;background:radial-gradient(ellipse at center,rgba(255,255,255,${dim ? .2 : .75}) 0%,rgba(255,255,255,0) 70%)"></div>
      <div class="cl abs" style="left:20px;top:200px;width:360px;height:130px;background:radial-gradient(ellipse at center,rgba(255,255,255,${dim ? .15 : .6}) 0%,rgba(255,255,255,0) 70%)"></div>
      <div class="abs" style="inset:0;background:linear-gradient(115deg,rgba(255,255,255,.22) 0%,rgba(255,255,255,0) 40%)"></div>
    </div>
  </div>`;
const driftClouds = (root, lt) => root.querySelectorAll('.cl').forEach((c, i) => {
  c.style.transform = `translateX(${-((lt * (40 + i * 18)) % 700) + 260}px)`;
});

REEL({
  theme: "story",
  hud: "A SHORT STORY ABOUT TASTE",
  counter: false,
  scenes: [
    // the hook: a window seat, clouds drifting
    { at: 0, type: "custom", punch: false,
      html: windowHTML('w', 320, 0) +
        `<div id="t" class="headline abs" style="left:60px;right:60px;top:1060px;height:260px;text-align:center;font-size:96px">${'Ever noticed airplane food tastes <span class="em">bland</span>?'}</div>`,
      update: (root, lt, H) => {
        H.pop(root.querySelector('#w'), lt, 0, { dy: 0, scale: .96, dur: .9 });
        driftClouds(root, lt);
        H.pop(root.querySelector('#t'), lt, .25, { dy: 30, dur: .8 });
      } },
    { at: "It's not the chef", type: "statement", kicker: "Chapter one", title: "It's not the *chef*." },
    // the cabin: same window, now at night
    { at: "It's the cabin", type: "custom", punch: false,
      html: windowHTML('w', 320, 1) +
        `<div id="t" class="headline abs" style="left:60px;right:60px;top:1080px;text-align:center;font-size:150px">It's the <span class="em">cabin</span>.</div>`,
      update: (root, lt, H) => {
        H.pop(root.querySelector('#w'), lt, 0, { dy: 0, scale: 1.04, dur: .9 });
        driftClouds(root, lt);
        H.pop(root.querySelector('#t'), lt, .1, { dy: 30, dur: .7 });
      } },
    { at: "Up there", type: "compare", title: "The air up there is drier than...",
      left: { icon: "🏜️", label: "Most deserts", value: "dry", at: 0.2 },
      right: { icon: "✈️", label: "The cabin", value: "*drier*", at: "drier" } },
    { at: "so your nose", type: "statement", kicker: "So", title: "Your nose *dries out*." },
    { at: "and most of", type: "statement", kicker: "And most of taste", title: "is really *smell*." },
    { at: "A Lufthansa study", type: "stat", kicker: "A Lufthansa study", value: 30, prefix: "up to −", suffix: "%", label: "salty and *sweet*", labelAt: "salty", countDur: 2.6 },
    { at: "weaker in the", type: "statement", title: "Weaker, *in the air*." },
    { at: "Even the engine", type: "statement", kicker: "Even the engine", title: "Noise dulls *sweetness*." },
    { at: "But one taste", type: "statement", dark: true, kicker: "One taste survives", title: "*Umami*", size: 230, bodyAt: "umami", body: "the savoury fifth taste" },
    { at: "That's why so many", type: "compare", title: "So on a plane, people order...",
      left: { icon: "🥤", label: "Soda", value: "sweet", at: 0.3 },
      right: { icon: "🍅", label: "Tomato juice", value: "*umami*", at: "tomato juice" } },
    { at: "Follow for more", type: "statement", kicker: "The end", title: "Follow for more *food science*." },
  ]
});
