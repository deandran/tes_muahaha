const params = new URLSearchParams(location.search);
const job = params.get("job") || "backup-collect";

const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");
const overlay = document.getElementById("overlay");
const keys = new Set();
const tap = { jump: false, attack: false, left: false, right: false, up: false, down: false };

window.addEventListener("keydown", (e) => { keys.add(e.key.toLowerCase()); if (e.code === "Space") e.preventDefault(); });
window.addEventListener("keyup", (e) => keys.delete(e.key.toLowerCase()));

function hex(h, fallback) {
  if (!h || !h.startsWith("#")) return fallback;
  return h;
}

function extrasOf(cfg) {
  return new Set((cfg.heroExtras || "").split(",").map((s) => s.trim()).filter(Boolean));
}

function drawHero(x, y, s, cfg, facing = 1) {
  const fill = hex(cfg.heroColor, "#3d8b62");
  const light = hex(cfg.heroLight, "#f4efe6");
  const ink = hex(cfg.heroInk, "#241c14");
  const extras = extrasOf(cfg);
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(facing, 1);
  ctx.lineJoin = "round";
  ctx.strokeStyle = ink;
  ctx.lineWidth = 3;
  const poly = (color, pts) => {
    ctx.beginPath();
    ctx.moveTo(pts[0] * s, pts[1] * s);
    for (let i = 2; i < pts.length; i += 2) ctx.lineTo(pts[i] * s, pts[i + 1] * s);
    ctx.closePath();
    ctx.fillStyle = color;
    ctx.fill();
    ctx.stroke();
  };
  poly(fill, [-10, 8, -4, 8, -6, 38, -16, 38]);
  poly(fill, [4, 8, 10, 8, 16, 38, 6, 38]);
  if (extras.has("cape")) poly(ink, [-12, -6, 12, -6, 22, 30, -22, 30]);
  poly(fill, [-12, -12, 12, -12, 14, 10, -14, 10]);
  poly(fill, [-12, -10, -16, -8, -32, 8, -24, 12, -12, -2]);
  poly(fill, [12, -10, 16, -8, 32, 8, 24, 12, 12, -2]);
  if (cfg.heroSilhouette === "robot") {
    poly(fill, [-12, -36, 12, -36, 12, -12, -12, -12]);
    poly(light, [-7, -28, -2, -28, -2, -23, -7, -23]);
    poly(light, [2, -28, 7, -28, 7, -23, 2, -23]);
  } else {
    poly(fill, [0, -40, 14, -26, 10, -12, -10, -12, -14, -26]);
    poly(light, [-6, -24, -2, -24, -2, -20, -6, -20]);
    poly(light, [2, -24, 6, -24, 6, -20, 2, -20]);
  }
  if (extras.has("horns")) {
    poly(light, [-12, -32, -16, -48, -4, -34]);
    poly(light, [12, -32, 16, -48, 4, -34]);
  }
  if (extras.has("ears")) {
    poly(fill, [-12, -32, -20, -50, -2, -34]);
    poly(fill, [12, -32, 20, -50, 2, -34]);
  }
  if (extras.has("antenna")) {
    ctx.beginPath();
    ctx.moveTo(0, -36);
    ctx.lineTo(0, -52);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(0, -54, 4, 0, Math.PI * 2);
    ctx.fillStyle = light;
    ctx.fill();
    ctx.stroke();
  }
  if (extras.has("tail")) poly(fill, [-14, 8, -18, 8, -30, 26, -22, 28]);
  ctx.restore();
}

function drawEnemy(x, y, s, color) {
  ctx.save();
  ctx.translate(x, y);
  ctx.fillStyle = color;
  ctx.strokeStyle = "#241c14";
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(-14 * s, 10 * s);
  ctx.lineTo(14 * s, 10 * s);
  ctx.lineTo(10 * s, -12 * s);
  ctx.lineTo(0, -18 * s);
  ctx.lineTo(-10 * s, -12 * s);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
  ctx.fillStyle = "#f4ead7";
  ctx.fillRect(-6 * s, -8 * s, 4 * s, 4 * s);
  ctx.fillRect(2 * s, -8 * s, 4 * s, 4 * s);
  ctx.restore();
}

function configUrl() {
  if (job.startsWith("backup-")) {
    const name = job.replace("backup-", "");
    return `/backups/games/${name}/game_config.json`;
  }
  return `/jobs/${job}/game_config.json`;
}

function bindTouch(genre) {
  const row = document.getElementById("touch");
  if (genre === "runner") {
    row.innerHTML = `<button type="button">Jump</button>`;
    row.querySelector("button").addEventListener("pointerdown", () => { tap.jump = true; });
  } else if (genre === "arena") {
    row.innerHTML = `<button data-k="left">◀</button><button data-k="attack">Hit</button><button data-k="right">▶</button>`;
    row.querySelectorAll("button").forEach((b) => {
      b.addEventListener("pointerdown", () => { tap[b.dataset.k] = true; });
      b.addEventListener("pointerup", () => { tap[b.dataset.k] = false; });
    });
  } else {
    row.innerHTML = `<button data-k="left">◀</button><button data-k="up">▲</button><button data-k="down">▼</button><button data-k="right">▶</button>`;
    row.querySelectorAll("button").forEach((b) => {
      const down = () => { tap[b.dataset.k] = true; };
      const up = () => { tap[b.dataset.k] = false; };
      b.addEventListener("pointerdown", down);
      b.addEventListener("pointerup", up);
      b.addEventListener("pointercancel", up);
    });
  }
}

function endGame(title, body, restart) {
  overlay.classList.add("show");
  document.getElementById("end-title").textContent = title;
  document.getElementById("end-body").textContent = body;
  document.getElementById("retry").onclick = () => {
    overlay.classList.remove("show");
    restart();
  };
}

function axis() {
  let x = 0, y = 0;
  if (keys.has("a") || keys.has("arrowleft") || tap.left) x -= 1;
  if (keys.has("d") || keys.has("arrowright") || tap.right) x += 1;
  if (keys.has("w") || keys.has("arrowup") || tap.up) y -= 1;
  if (keys.has("s") || keys.has("arrowdown") || tap.down) y += 1;
  return { x, y };
}

function runRunner(cfg) {
  const ground = 430;
  let x = 140, y = ground, vy = 0, onGround = true;
  let dist = 0, coins = 0, dead = false, won = false;
  let obstacles = [];
  let items = [];
  let spawn = 0;
  const target = Number(cfg.target) || 350;
  const sky = hex(cfg.sky, "#f0d9b5");
  const dirt = hex(cfg.ground, "#7b8f4a");
  const obsC = hex(cfg.obstacleColor, "#6b5344");
  const itemC = hex(cfg.itemColor, "#e0b33a");

  function reset() {
    x = 140; y = ground; vy = 0; onGround = true;
    dist = 0; coins = 0; dead = false; won = false;
    obstacles = []; items = []; spawn = 0;
  }

  function loop() {
    if (!dead && !won) {
      dist += 0.85;
      spawn += 1;
      if (spawn % 70 === 0) obstacles.push({ x: 980, w: 36, h: 40 + Math.random() * 24 });
      if (spawn % 90 === 0) items.push({ x: 980, y: ground - 90 - Math.random() * 70, r: 12 });
      const wantJump = keys.has(" ") || keys.has("space") || tap.jump;
      tap.jump = false;
      if (wantJump && onGround) { vy = -13; onGround = false; }
      vy += 0.55;
      y += vy;
      if (y >= ground) { y = ground; vy = 0; onGround = true; }
      obstacles.forEach((o) => { o.x -= 6; });
      items.forEach((i) => { i.x -= 6; });
      obstacles = obstacles.filter((o) => o.x > -40);
      items = items.filter((i) => i.x > -20);
      for (const o of obstacles) {
        if (Math.abs(o.x - x) < 28 && y > ground - o.h + 8) dead = true;
      }
      for (const i of items) {
        if (Math.hypot(i.x - x, i.y - (y - 20)) < 28) { i.dead = true; coins += 1; }
      }
      items = items.filter((i) => !i.dead);
      if (dist >= target) won = true;
      if (dead) endGame(cfg.loseText || "Almost.", "You tripped. That's the whole joke.", reset);
      if (won) endGame(cfg.winText || "You did it!", `${cfg.heroName} ran ${Math.floor(dist)} steps.`, reset);
    }

    ctx.fillStyle = sky;
    ctx.fillRect(0, 0, 960, 540);
    ctx.fillStyle = dirt;
    ctx.fillRect(0, ground, 960, 540 - ground);
    ctx.fillStyle = "#241c14";
    ctx.fillRect(0, ground, 960, 4);
    const scroll = dist % 48;
    for (let i = -1; i < 22; i++) {
      ctx.fillRect(i * 48 - scroll, ground + 12, 24, 4);
    }
    obstacles.forEach((o) => {
      ctx.fillStyle = obsC;
      ctx.strokeStyle = "#241c14";
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.rect(o.x - o.w / 2, ground - o.h, o.w, o.h);
      ctx.fill();
      ctx.stroke();
    });
    items.forEach((i) => {
      ctx.fillStyle = itemC;
      ctx.beginPath();
      ctx.arc(i.x, i.y, i.r, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = "#241c14";
      ctx.stroke();
    });
    drawHero(x, y - 2, 1.15, cfg, 1);
    ctx.fillStyle = "#241c14";
    ctx.font = "600 18px IBM Plex Sans";
    ctx.fillText(`${Math.min(target, Math.floor(dist))} / ${target}`, 24, 36);
    ctx.fillText(`★ ${coins}`, 24, 60);
    requestAnimationFrame(loop);
  }
  reset();
  loop();
}

function runArena(cfg) {
  const target = Number(cfg.target) || 6;
  const sky = hex(cfg.sky, "#e07a3d");
  const floor = hex(cfg.ground, "#4a2c23");
  const enemyC = hex(cfg.enemyColor, "#7a4c7a");
  let p, enemies, cooldown, kills, hp, over;

  function reset() {
    p = { x: 480, y: 300, facing: 1 };
    enemies = [];
    cooldown = 0;
    kills = 0;
    hp = 3;
    over = false;
    for (let i = 0; i < 3; i++) spawn();
  }

  function spawn() {
    const side = Math.random() < 0.5 ? -40 : 1000;
    enemies.push({ x: side, y: 160 + Math.random() * 280, alive: true });
  }

  function resetOrEnd() {
    reset();
  }

  function loop() {
    if (!over) {
      const a = axis();
      p.x = Math.max(40, Math.min(920, p.x + a.x * 4.2));
      p.y = Math.max(120, Math.min(500, p.y + a.y * 4.2));
      if (a.x) p.facing = a.x > 0 ? 1 : -1;
      cooldown = Math.max(0, cooldown - 1);
      const attack = keys.has(" ") || tap.attack;
      tap.attack = false;
      let swing = false;
      if (attack && cooldown === 0) { swing = true; cooldown = 18; }
      if (enemies.length < 4 && Math.random() < 0.02) spawn();
      enemies.forEach((e) => {
        if (!e.alive) return;
        const dx = p.x - e.x, dy = p.y - e.y;
        const d = Math.hypot(dx, dy) || 1;
        e.x += (dx / d) * 1.6;
        e.y += (dy / d) * 1.6;
        if (d < 34) {
          hp -= 1;
          e.x -= (dx / d) * 40;
          if (hp <= 0) {
            over = true;
            endGame(cfg.loseText || "Almost.", "They got a hit in. Try again.", resetOrEnd);
          }
        }
        if (swing && d < 70) {
          e.alive = false;
          kills += 1;
        }
      });
      enemies = enemies.filter((e) => e.alive);
      if (kills >= target) {
        over = true;
        endGame(cfg.winText || "You did it!", `${kills} down. ${cfg.heroName} holds the floor.`, resetOrEnd);
      }
    }

    ctx.fillStyle = sky;
    ctx.fillRect(0, 0, 960, 540);
    ctx.fillStyle = floor;
    ctx.beginPath();
    ctx.ellipse(480, 310, 360, 180, 0, 0, Math.PI * 2);
    ctx.fill();
    enemies.forEach((e) => drawEnemy(e.x, e.y, 1, enemyC));
    if (cooldown > 10) {
      ctx.strokeStyle = hex(cfg.heroLight, "#fff");
      ctx.lineWidth = 6;
      ctx.beginPath();
      ctx.arc(p.x, p.y, 48, 0, Math.PI * 2);
      ctx.stroke();
    }
    drawHero(p.x, p.y, 1.2, cfg, p.facing);
    ctx.fillStyle = "#241c14";
    ctx.font = "600 18px IBM Plex Sans";
    ctx.fillText(`hits ${kills}/${target}   hp ${Math.max(0, hp)}`, 24, 36);
    requestAnimationFrame(loop);
  }
  reset();
  loop();
}

function runCollect(cfg) {
  const target = Number(cfg.target) || 8;
  const sky = hex(cfg.sky, "#f4c6d4");
  const floor = hex(cfg.ground, "#8fbf9a");
  const enemyC = hex(cfg.enemyColor, "#4a4a62");
  const itemC = hex(cfg.itemColor, "#e0b33a");
  let p, items, bats, got, time, over;

  function placeItems() {
    items = [];
    for (let i = 0; i < target; i++) {
      items.push({ x: 80 + Math.random() * 800, y: 80 + Math.random() * 380, taken: false });
    }
  }

  function reset() {
    p = { x: 480, y: 300 };
    bats = [{ x: 120, y: 120, vx: 2, vy: 1.4 }, { x: 800, y: 400, vx: -1.6, vy: 1.8 }];
    got = 0;
    time = 40;
    over = false;
    placeItems();
  }

  function loop(ts, last) {
    const dt = Math.min(0.05, (ts - last) / 1000 || 0.016);
    if (!over) {
      const a = axis();
      p.x = Math.max(30, Math.min(930, p.x + a.x * 220 * dt));
      p.y = Math.max(40, Math.min(510, p.y + a.y * 220 * dt));
      time -= dt;
      items.forEach((it) => {
        if (!it.taken && Math.hypot(it.x - p.x, it.y - p.y) < 28) {
          it.taken = true;
          got += 1;
        }
      });
      bats.forEach((b) => {
        b.x += b.vx;
        b.y += b.vy;
        if (b.x < 40 || b.x > 920) b.vx *= -1;
        if (b.y < 40 || b.y > 500) b.vy *= -1;
        if (Math.hypot(b.x - p.x, b.y - p.y) < 30) {
          over = true;
          endGame(cfg.loseText || "Almost.", "A bat clipped you.", reset);
        }
      });
      if (got >= target) {
        over = true;
        endGame(cfg.winText || "You did it!", `Every star. ${cfg.heroName} pockets them.`, reset);
      } else if (time <= 0) {
        over = true;
        endGame(cfg.loseText || "Almost.", "Time ran out.", reset);
      }
    }
    ctx.fillStyle = sky;
    ctx.fillRect(0, 0, 960, 540);
    ctx.fillStyle = floor;
    ctx.fillRect(30, 30, 900, 480);
    items.forEach((it) => {
      if (it.taken) return;
      ctx.fillStyle = itemC;
      ctx.beginPath();
      ctx.moveTo(it.x, it.y - 12);
      ctx.lineTo(it.x + 8, it.y);
      ctx.lineTo(it.x, it.y + 12);
      ctx.lineTo(it.x - 8, it.y);
      ctx.closePath();
      ctx.fill();
      ctx.strokeStyle = "#241c14";
      ctx.stroke();
    });
    bats.forEach((b) => drawEnemy(b.x, b.y, 0.85, enemyC));
    drawHero(p.x, p.y, 1.05, cfg, 1);
    ctx.fillStyle = "#241c14";
    ctx.font = "600 18px IBM Plex Sans";
    ctx.fillText(`stars ${got}/${target}   ${Math.max(0, time).toFixed(1)}s`, 48, 58);
    requestAnimationFrame((n) => loop(n, ts));
  }
  reset();
  requestAnimationFrame((t) => loop(t, t));
}

async function boot() {
  const res = await fetch(configUrl());
  if (!res.ok) throw new Error("missing config");
  const cfg = await res.json();
  document.getElementById("title").textContent = cfg.title || "Game";
  document.getElementById("sub").textContent = `${cfg.hint || ""} · ${cfg.subtitle || ""}`;
  document.title = (cfg.title || "Game") + " · Game Lab";
  bindTouch(cfg.genre || cfg.templateId);
  const g = cfg.genre || cfg.templateId;
  if (g === "runner") runRunner(cfg);
  else if (g === "arena") runArena(cfg);
  else runCollect(cfg);
}

boot().catch((err) => {
  document.getElementById("title").textContent = "Could not load game";
  document.getElementById("sub").textContent = String(err);
});
