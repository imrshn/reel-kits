// Scenes for: why airplane food tastes so bland
// Each scene starts when the voice says its "at" words. See REEL-FORMAT.md.
REEL({
  hud: "FOOD SCIENCE",
  scenes: [
    { at: 0, type: "hook", icon: "✈️", kicker: "Food science", title: "Why airplane food tastes *bland*" },
    { at: "It's not the chef", type: "statement", icon: "👨‍🍳", title: "It's not the *chef*." },
    { at: "It's the cabin", type: "statement", icon: "🛫", kicker: "It's the", title: "*cabin*", size: 220 },
    { at: "Up there", type: "compare", title: "Air up there is drier than...",
      left: { icon: "🏜️", label: "Most deserts", value: "dry", at: 0.2 },
      right: { icon: "✈️", label: "The cabin", value: "*drier*", at: "drier" } },
    { at: "so your nose", type: "list", title: "So...",
      items: [
        { at: "nose", icon: "👃", text: "Your nose dries out" },
        { at: "taste is", icon: "👅", text: "And taste is mostly *smell*" },
      ] },
    { at: "A Lufthansa study", type: "stat", kicker: "Lufthansa study", value: 30, prefix: "−", suffix: "%", label: "salty and *sweet* taste", labelAt: "salty" },
    { at: "Even the engine", type: "statement", icon: "🔊", title: "Engine noise dulls *sweetness*" },
    { at: "But one taste", type: "statement", dark: true, kicker: "One taste survives", title: "*Umami*", size: 230, bodyAt: "umami", body: "the savoury fifth taste" },
    { at: "That's why so many", type: "compare", title: "On a plane, order...",
      left: { icon: "🥤", label: "Soda", value: "sweet", at: 0.3 },
      right: { icon: "🍅", label: "Tomato juice", value: "*umami*", at: "tomato juice" } },
    { at: "Follow for more", type: "statement", icon: "🧪", title: "Follow for more *food science*" },
  ]
});
