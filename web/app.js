const QUESTIONS = [
  {
    key: "genre",
    title: "What kind of game?",
    lede: "Pick a shape. You can still type slang, or mix Bahasa and English.",
    render() {
      return `
        <div class="choices">
          <button type="button" class="choice" data-genre="runner"><strong>Runner</strong><small>Lari, loncat, jangan nabrak.</small></button>
          <button type="button" class="choice" data-genre="arena"><strong>Brawl</strong><small>Gebukin musuh di arena kecil.</small></button>
          <button type="button" class="choice" data-genre="collect"><strong>Collect</strong><small>Kumpulin barang sebelum waktu habis.</small></button>
        </div>
        <label for="genre_text">Or say it your way</label>
        <input id="genre_text" placeholder="e.g. game lari-larian, atau 1v1 gitu" />
      `;
    },
    bind() {
      document.querySelectorAll(".choice").forEach((btn) => {
        btn.addEventListener("click", () => {
          document.querySelectorAll(".choice").forEach((b) => b.classList.remove("on"));
          btn.classList.add("on");
          answers.genre = btn.dataset.genre;
        });
        if (answers.genre === btn.dataset.genre) btn.classList.add("on");
      });
      const input = document.getElementById("genre_text");
      input.value = answers.genre_text || "";
      input.addEventListener("input", () => { answers.genre_text = input.value; });
    },
    ok() { return Boolean(answers.genre || (answers.genre_text || "").trim()); },
  },
  {
    key: "hero",
    title: "Who is the hero?",
    lede: "A color, an animal, a vibe. “Naga kecil warna hijau” is plenty.",
    render() {
      return `
        <label for="hero">Hero</label>
        <textarea id="hero" placeholder="a tiny green dragon kid named Bima"></textarea>
      `;
    },
    bind() {
      const el = document.getElementById("hero");
      el.value = answers.hero || "";
      el.addEventListener("input", () => { answers.hero = el.value; });
    },
    ok() { return (answers.hero || "").trim().length > 1; },
  },
  {
    key: "enemy",
    title: "What gets in the way?",
    lede: "Rocks, bats, a grumpy blob — keep it one sentence.",
    render() {
      return `
        <label for="enemy">Enemy or obstacle</label>
        <textarea id="enemy" placeholder="spiky brown rocks / kelelawar nakal"></textarea>
      `;
    },
    bind() {
      const el = document.getElementById("enemy");
      el.value = answers.enemy || "";
      el.addEventListener("input", () => { answers.enemy = el.value; });
    },
    ok() { return true; },
  },
  {
    key: "goal",
    title: "How do you win?",
    lede: "Sampai finish, kumpulin 8 bintang, atau kalahin 6 musuh.",
    render() {
      return `
        <label for="goal">Goal</label>
        <textarea id="goal" placeholder="collect 8 stars / reach the finish"></textarea>
      `;
    },
    bind() {
      const el = document.getElementById("goal");
      el.value = answers.goal || "";
      el.addEventListener("input", () => { answers.goal = el.value; });
    },
    ok() { return true; },
  },
  {
    key: "mood",
    title: "What should it feel like?",
    lede: "This only tweaks colors. The template stays the same.",
    render() {
      return `
        <div class="moods">
          <button type="button" class="mood" data-mood="cozy">Cozy afternoon</button>
          <button type="button" class="mood" data-mood="cute">Cute / pink-ish</button>
          <button type="button" class="mood" data-mood="chaotic">Loud and messy</button>
          <button type="button" class="mood" data-mood="night">Night run</button>
        </div>
      `;
    },
    bind() {
      document.querySelectorAll(".mood").forEach((btn) => {
        btn.addEventListener("click", () => {
          document.querySelectorAll(".mood").forEach((b) => b.classList.remove("on"));
          btn.classList.add("on");
          answers.mood = btn.dataset.mood;
        });
        if ((answers.mood || "cozy") === btn.dataset.mood) btn.classList.add("on");
      });
    },
    ok() { return true; },
  },
];

const STEPS = [
  ["understand", "Reading your answers"],
  ["draw", "Drawing your hero"],
  ["cleanup", "Clearing the background"],
  ["sculpt", "Making a chunky 3D figure"],
  ["skeleton", "Adding a skeleton so they can move"],
  ["template", "Dropping them into a template"],
  ["build", "Packing the playable build"],
  ["ready", "Ready to play"],
];

const answers = { genre: null, genre_text: "", hero: "", enemy: "", goal: "", mood: "cozy" };
let stepIndex = 0;

const pips = document.getElementById("pips");
const qBody = document.getElementById("q-body");
const nextBtn = document.getElementById("next-btn");
const backBtn = document.getElementById("back-btn");

function renderPips() {
  pips.innerHTML = QUESTIONS.map((_, i) => `<span class="${i <= stepIndex ? "on" : ""}"></span>`).join("");
}

function showQuestion() {
  const q = QUESTIONS[stepIndex];
  document.getElementById("kicker").textContent = `Question ${stepIndex + 1} of ${QUESTIONS.length}`;
  document.getElementById("q-title").textContent = q.title;
  document.getElementById("q-lede").textContent = q.lede;
  qBody.innerHTML = q.render();
  q.bind();
  backBtn.disabled = stepIndex === 0;
  nextBtn.textContent = stepIndex === QUESTIONS.length - 1 ? "Make my game" : "Next";
  renderPips();
}

backBtn.addEventListener("click", () => {
  if (stepIndex === 0) return;
  stepIndex -= 1;
  showQuestion();
});

nextBtn.addEventListener("click", async () => {
  const q = QUESTIONS[stepIndex];
  if (!q.ok()) return;
  if (stepIndex < QUESTIONS.length - 1) {
    stepIndex += 1;
    showQuestion();
    return;
  }
  await startJob();
});

async function startJob() {
  document.getElementById("ask").classList.add("hidden");
  document.getElementById("progress").classList.remove("hidden");
  const timeline = document.getElementById("timeline");
  timeline.innerHTML = STEPS.map(
    ([key, label]) => `<li data-step="${key}"><span class="mark"></span><div><strong>${label}</strong><span class="cap"></span></div></li>`
  ).join("");

  const res = await fetch("/api/jobs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(answers),
  });
  const { id } = await res.json();
  const src = new EventSource(`/api/jobs/${id}/events`);
  src.onmessage = (ev) => {
    const data = JSON.parse(ev.data);
    if (data.step === "stream-end") {
      src.close();
      return;
    }
    const li = document.querySelector(`[data-step="${data.step}"]`);
    if (li) {
      li.classList.remove("run", "ok", "fall");
      if (data.status === "running") li.classList.add("run");
      if (data.status === "done") li.classList.add("ok");
      if (data.status === "fallback") li.classList.add("fall");
      const cap = li.querySelector(".cap");
      if (cap && data.caption) cap.textContent = data.caption;
    }
    if (data.caption) document.getElementById("live-caption").textContent = data.caption;
    if (data.image_url) {
      const img = document.getElementById("peek-img");
      img.src = data.image_url + "?t=" + Date.now();
      img.hidden = false;
      document.getElementById("peek-ph").hidden = true;
    }
    if (data.spec && data.spec.ui_text) {
      document.getElementById("peek-title").textContent = data.spec.ui_text.title;
    }
    if (data.note) document.getElementById("peek-note").textContent = data.note;
    if (data.source) document.getElementById("peek-note").textContent = data.source;
    if (data.step === "done" || (data.step === "ready" && data.play_url)) {
      finish(data.play_url, data.caption);
      src.close();
    }
  };
}

function finish(playUrl, note) {
  document.getElementById("progress").classList.add("hidden");
  document.getElementById("done").classList.remove("hidden");
  document.getElementById("play-link").href = playUrl || "/play.html?job=backup-collect";
  if (note) document.getElementById("done-note").textContent = note;
}

document.getElementById("panic-btn").addEventListener("click", async () => {
  const res = await fetch("/api/demo-panic", { method: "POST" });
  const data = await res.json();
  window.location.href = data.play_url;
});

async function loadHealth() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    const text = document.getElementById("health-text");
    const bits = [data.llm];
    bits.push(data.unity ? "Unity connected" : "HTML5 player");
    bits.push(`Hunyuan ${data.hunyuan.remaining}/${data.hunyuan.max} ${data.hunyuan.enabled ? "ON" : "off"}`);
    text.textContent = bits.join(" · ");
  } catch {
    document.getElementById("health-text").textContent = "Can't reach the orchestrator";
    document.querySelector(".dot").classList.add("warn");
  }
}

showQuestion();
loadHealth();
