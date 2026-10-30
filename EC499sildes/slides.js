/**
 * EC499 Master Presentation Engine
 * Features:
 * - 32-Slide Navigation & Transitions
 * - Interactive Canvas Network Topology Simulator (Real Packet Flow + Jamming Relief)
 * - Interactive D3QN Neural Architecture Visualizer (Pulsing Forward Pass)
 * - Interactive 3-Controller HA Failover Simulator (Crash Injection + 0.003ms Role Promotion)
 * - Dynamic Metric Counter Animations
 * - Presenter Mode with Stopwatch, Next Slide Preview & Speaker Notes
 * - Grid Overview Mode with Instant Search
 * - Laser Pointer & Dark/Light Theme Switcher
 */

document.addEventListener('DOMContentLoaded', () => {
  // DOM References
  const slides = Array.from(document.querySelectorAll('.slide'));
  const totalSlides = slides.length;
  let currentSlide = 0;
  
  const progressBar = document.getElementById('progress-bar');
  const slideCounter = document.getElementById('slide-counter');
  const btnPrev = document.getElementById('btn-prev');
  const btnNext = document.getElementById('btn-next');
  
  // Modals & Panels
  const presenterModal = document.getElementById('presenter-modal');
  const presenterCurrent = document.getElementById('presenter-current');
  const presenterNext = document.getElementById('presenter-next');
  const presenterNotes = document.getElementById('presenter-notes');
  const presenterTimer = document.getElementById('presenter-timer');
  
  const overviewModal = document.getElementById('overview-modal');
  const overviewGrid = document.getElementById('overview-grid');
  
  const laserPointer = document.getElementById('laser-pointer');
  let isLaserActive = false;
  let isAutoPlay = false;
  let autoPlayInterval = null;
  
  // Timer State
  let startTime = Date.now();
  let timerInterval = null;

  // 1. Navigation Functions
  function updateSlide(index) {
    if (index < 0) index = 0;
    if (index >= totalSlides) index = totalSlides - 1;
    
    slides.forEach((s, idx) => {
      s.classList.toggle('active', idx === index);
    });
    
    currentSlide = index;
    const progressPct = ((index + 1) / totalSlides) * 100;
    if (progressBar) progressBar.style.width = `${progressPct}%`;
    if (slideCounter) slideCounter.textContent = `${index + 1} / ${totalSlides}`;
    
    // Trigger slide-specific animations
    onSlideEnter(index);
    updatePresenterNotes();
    updateOverviewCards();
  }

  function nextSlide() {
    if (currentSlide < totalSlides - 1) {
      updateSlide(currentSlide + 1);
    }
  }

  function prevSlide() {
    if (currentSlide > 0) {
      updateSlide(currentSlide - 1);
    }
  }

  // 2. Keyboard & Touch Navigation
  document.addEventListener('keydown', (e) => {
    // If overview modal active and Escape pressed, close it
    if ((e.key === 'Escape' || e.key === 'o' || e.key === 'O') && overviewModal && overviewModal.classList.contains('active')) {
      toggleOverview(false);
      return;
    }
    
    switch (e.key) {
      case 'ArrowRight':
      case 'PageDown':
      case ' ':
        e.preventDefault();
        nextSlide();
        break;
      case 'ArrowLeft':
      case 'PageUp':
        e.preventDefault();
        prevSlide();
        break;
      case 'Home':
        e.preventDefault();
        updateSlide(0);
        break;
      case 'End':
        e.preventDefault();
        updateSlide(totalSlides - 1);
        break;
      case 'p':
      case 'P':
        togglePresenterMode();
        break;
      case 'o':
      case 'O':
        toggleOverview();
        break;
      case 'm':
      case 'M':
        toggleTheme();
        break;
      case 'l':
      case 'L':
        toggleLaser();
        break;
      case 'a':
      case 'A':
        toggleAutoPlay();
        break;
      case 'f':
      case 'F':
        toggleFullscreen();
        break;
    }
  });

  if (btnPrev) btnPrev.addEventListener('click', prevSlide);
  if (btnNext) btnNext.addEventListener('click', nextSlide);

  // 3. Theme Toggle
  function toggleTheme() {
    document.body.classList.toggle('theme-light');
  }
  const btnTheme = document.getElementById('btn-theme');
  if (btnTheme) btnTheme.addEventListener('click', toggleTheme);

  // 4. Laser Pointer
  function toggleLaser() {
    isLaserActive = !isLaserActive;
    if (laserPointer) {
      laserPointer.style.display = isLaserActive ? 'block' : 'none';
    }
  }
  const btnLaser = document.getElementById('btn-laser');
  if (btnLaser) btnLaser.addEventListener('click', toggleLaser);

  document.addEventListener('mousemove', (e) => {
    if (isLaserActive && laserPointer) {
      laserPointer.style.left = `${e.clientX}px`;
      laserPointer.style.top = `${e.clientY}px`;
    }
  });

  // 5. Presenter Mode & Timer
  function togglePresenterMode() {
    if (!presenterModal) return;
    const isActive = presenterModal.classList.toggle('active');
    if (isActive) {
      startTimer();
      updatePresenterNotes();
    }
  }
  const btnPresenter = document.getElementById('btn-presenter');
  if (btnPresenter) btnPresenter.addEventListener('click', togglePresenterMode);

  const btnClosePresenter = document.getElementById('btn-close-presenter');
  if (btnClosePresenter) btnClosePresenter.addEventListener('click', () => presenterModal.classList.remove('active'));

  function startTimer() {
    if (timerInterval) return;
    startTime = Date.now();
    timerInterval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      const m = String(Math.floor(elapsed / 60)).padStart(2, '0');
      const s = String(elapsed % 60).padStart(2, '0');
      if (presenterTimer) presenterTimer.textContent = `⏱️ ${m}:${s}`;
    }, 1000);
  }

  function updatePresenterNotes() {
    if (!presenterNotes) return;
    const activeSlide = slides[currentSlide];
    const notesEl = activeSlide ? activeSlide.querySelector('.speaker-notes') : null;
    const headingEl = activeSlide ? activeSlide.querySelector('.slide-heading') : null;
    
    const heading = headingEl ? headingEl.textContent.trim() : `Slide ${currentSlide + 1}`;
    const notes = notesEl ? notesEl.innerHTML : `<p><em>No speaker notes provided for this slide.</em></p>`;
    
    presenterNotes.innerHTML = `
      <div style="margin-bottom:14px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:8px;">
        <span style="font-size:12px; color:var(--accent-cyan); text-transform:uppercase; font-weight:700;">Slide ${currentSlide + 1} of ${totalSlides}</span>
        <h3 style="font-size:18px; margin-top:4px; color:#fff;">${heading}</h3>
      </div>
      <div>${notes}</div>
    `;

    if (presenterCurrent) {
      presenterCurrent.innerHTML = `<h4 style="color:var(--text-muted); font-size:12px; margin-bottom:8px;">CURRENT SLIDE</h4>` + activeSlide.outerHTML;
    }
    if (presenterNext) {
      const nextS = slides[currentSlide + 1];
      presenterNext.innerHTML = nextS 
        ? `<h4 style="color:var(--text-muted); font-size:12px; margin-bottom:8px;">NEXT SLIDE</h4>` + nextS.outerHTML 
        : `<h4 style="color:var(--text-muted); font-size:12px; margin-bottom:8px;">NEXT SLIDE</h4><p style="color:var(--text-muted); padding:20px;">[End of Presentation]</p>`;
    }
  }

  // 6. Overview Grid Mode
  function toggleOverview(forceState) {
    if (!overviewModal) return;
    const shouldOpen = forceState !== undefined ? forceState : !overviewModal.classList.contains('active');
    overviewModal.classList.toggle('active', shouldOpen);
    if (shouldOpen) buildOverviewGrid();
  }
  const btnOverview = document.getElementById('btn-overview');
  if (btnOverview) btnOverview.addEventListener('click', () => toggleOverview());

  const btnCloseOverview = document.getElementById('btn-close-overview');
  if (btnCloseOverview) btnCloseOverview.addEventListener('click', () => toggleOverview(false));

  function buildOverviewGrid() {
    if (!overviewGrid) return;
    overviewGrid.innerHTML = '';
    slides.forEach((s, idx) => {
      const heading = s.querySelector('.slide-heading');
      const cat = s.querySelector('.category-pill');
      const card = document.createElement('div');
      card.className = `overview-card ${idx === currentSlide ? 'current' : ''}`;
      card.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <span class="overview-num">SLIDE ${idx + 1}</span>
          <span style="font-size:10px; color:var(--accent-cyan);">${cat ? cat.textContent.trim() : ''}</span>
        </div>
        <div class="overview-title">${heading ? heading.textContent.trim() : `Slide ${idx + 1}`}</div>
      `;
      card.addEventListener('click', () => {
        updateSlide(idx);
        toggleOverview(false);
      });
      overviewGrid.appendChild(card);
    });
  }

  function updateOverviewCards() {
    const cards = document.querySelectorAll('.overview-card');
    cards.forEach((c, idx) => {
      c.classList.toggle('current', idx === currentSlide);
    });
  }

  // 7. Fullscreen Toggle
  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
    } else {
      if (document.exitFullscreen) document.exitFullscreen();
    }
  }
  const btnFullscreen = document.getElementById('btn-fullscreen');
  if (btnFullscreen) btnFullscreen.addEventListener('click', toggleFullscreen);

  // 8. Auto-Play Mode
  function toggleAutoPlay() {
    isAutoPlay = !isAutoPlay;
    if (isAutoPlay) {
      autoPlayInterval = setInterval(() => {
        if (currentSlide < totalSlides - 1) nextSlide();
        else updateSlide(0);
      }, 12000);
      alert('▶ Auto-play enabled (12s per slide). Press A to stop.');
    } else {
      clearInterval(autoPlayInterval);
      alert('⏸ Auto-play paused.');
    }
  }

  // ============================================================================
  // Canvas 0: Background Particle Constellation
  // ============================================================================
  const bgCanvas = document.getElementById('bg-canvas');
  if (bgCanvas) {
    const ctx = bgCanvas.getContext('2d');
    let width = bgCanvas.width = window.innerWidth;
    let height = bgCanvas.height = window.innerHeight;

    window.addEventListener('resize', () => {
      width = bgCanvas.width = window.innerWidth;
      height = bgCanvas.height = window.innerHeight;
    });

    const particles = [];
    const count = 45;
    for (let i = 0; i < count; i++) {
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        radius: Math.random() * 2 + 1,
      });
    }

    function renderBg() {
      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = '#06b6d4';
      ctx.strokeStyle = 'rgba(6, 182, 212, 0.08)';
      ctx.lineWidth = 1;

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x = width;
        if (p.x > width) p.x = 0;
        if (p.y < 0) p.y = height;
        if (p.y > height) p.y = 0;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fill();

        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const dist = Math.hypot(p.x - p2.x, p.y - p2.y);
          if (dist < 150) {
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
          }
        }
      }
      requestAnimationFrame(renderBg);
    }
    renderBg();
  }

  // ============================================================================
  // Canvas 1: Live Interactive Network Topology Flow Simulator (Slide 7 & 18)
  // ============================================================================
  let topoCanvas = document.getElementById('topo-sim-canvas');
  let topoSimRunning = false;
  let topoAnimId = null;
  let isCoreJammed = false;

  function drawTopoFrame(ctx, w, h, beat = 0) {
    ctx.clearRect(0, 0, w, h);
    const nodes = [
      { id: 0, x: w * 0.12, y: h * 0.50, label: "Src (H1)" },
      { id: 1, x: w * 0.35, y: h * 0.22, label: "Switch 1" },
      { id: 2, x: w * 0.35, y: h * 0.78, label: "Switch 2" },
      { id: 3, x: w * 0.65, y: h * 0.22, label: "Core Trunk" },
      { id: 4, x: w * 0.65, y: h * 0.78, label: "Agile Trunk" },
      { id: 5, x: w * 0.88, y: h * 0.50, label: "Dst (H2)" },
    ];

    const links = [
      { u: 0, v: 1, baseUtil: 0.40 },
      { u: 0, v: 2, baseUtil: 0.15 },
      { u: 1, v: 3, baseUtil: 0.45 },
      { u: 2, v: 4, baseUtil: 0.20 },
      { u: 3, v: 5, baseUtil: 0.40 },
      { u: 4, v: 5, baseUtil: 0.20 },
      { u: 1, v: 4, baseUtil: 0.10 },
      { u: 2, v: 3, baseUtil: 0.10 },
    ];

    // Draw Links
    links.forEach(l => {
      const n1 = nodes[l.u];
      const n2 = nodes[l.v];
      const isJammedLink = isCoreJammed && ((l.u === 1 && l.v === 3) || (l.u === 3 && l.v === 5));

      ctx.beginPath();
      ctx.moveTo(n1.x, n1.y);
      ctx.lineTo(n2.x, n2.y);
      ctx.lineWidth = isJammedLink ? 6 : 3.5;
      ctx.strokeStyle = isJammedLink ? '#ef4444' : (isCoreJammed ? '#10b981' : '#38bdf8');
      ctx.stroke();

      // Label link load
      const mx = (n1.x + n2.x) / 2;
      const my = (n1.y + n2.y) / 2;
      ctx.fillStyle = isJammedLink ? '#ef4444' : '#94a3b8';
      ctx.font = 'bold 12px Fira Code';
      const utilText = isJammedLink ? '98.5% [JAMMED]' : (isCoreJammed && (l.u === 2 || l.u === 4) ? '42.0% [D3QN]' : '28.0%');
      ctx.fillText(utilText, mx - 25, my - 8);
    });

    // Packets
    let pathNodes = isCoreJammed
      ? [nodes[0], nodes[2], nodes[4], nodes[5]]
      : [nodes[0], nodes[1], nodes[3], nodes[5]];
    const totalSegments = pathNodes.length - 1;
    for (let i = 0; i < 8; i++) {
      const prog = (beat * 0.15 + i / 8) % 1;
      const segIdx = Math.min(Math.floor(prog * totalSegments), totalSegments - 1);
      const segProgress = (prog * totalSegments) - segIdx;
      const na = pathNodes[segIdx];
      const nb = pathNodes[segIdx + 1];
      const px = na.x + (nb.x - na.x) * segProgress;
      const py = na.y + (nb.y - na.y) * segProgress;
      ctx.beginPath();
      ctx.arc(px, py, 6, 0, Math.PI * 2);
      ctx.fillStyle = isCoreJammed ? '#10b981' : '#38bdf8';
      ctx.shadowColor = ctx.fillStyle;
      ctx.shadowBlur = 10;
      ctx.fill();
      ctx.shadowBlur = 0;
    }

    // Draw Nodes
    nodes.forEach(n => {
      ctx.beginPath();
      ctx.arc(n.x, n.y, 22, 0, Math.PI * 2);
      ctx.fillStyle = '#1e293b';
      ctx.strokeStyle = '#38bdf8';
      ctx.lineWidth = 3;
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = '#f8fafc';
      ctx.font = 'bold 14px Outfit';
      ctx.textAlign = 'center';
      ctx.fillText(n.id, n.x, n.y + 5);

      ctx.font = '12px Inter';
      ctx.fillStyle = '#94a3b8';
      ctx.fillText(n.label, n.x, n.y + 36);
    });
  }

  function paintTopoStatic() {
    topoCanvas = document.getElementById('topo-sim-canvas');
    if (!topoCanvas) return;
    const w = topoCanvas.width = 960;
    const h = topoCanvas.height = 540;
    const ctx = topoCanvas.getContext('2d');
    drawTopoFrame(ctx, w, h, 0);
  }

  function initTopoSimulation() {
    topoCanvas = document.getElementById('topo-sim-canvas');
    if (!topoCanvas) return;
    const w = topoCanvas.width = 960;
    const h = topoCanvas.height = 540;
    const ctx = topoCanvas.getContext('2d');
    let beat = 0;

    function renderTopo() {
      if (!topoSimRunning) return;
      beat += 0.03;
      drawTopoFrame(ctx, w, h, beat);
      topoAnimId = requestAnimationFrame(renderTopo);
    }

    if (topoAnimId) cancelAnimationFrame(topoAnimId);
    topoSimRunning = true;
    renderTopo();
  }

  // Hook toolbar buttons
  window.triggerCoreJamming = function() {
    isCoreJammed = true;
    const statusEl = document.getElementById('topo-status-text');
    if (statusEl) {
      statusEl.innerHTML = `<span style="color:#ef4444; font-weight:700;">🚨 CORE JAMMED!</span> D3QN autonomously rerouting traffic to lower parallel path [0-2-4-5] (Latency: 68ms, Loss: 0.0%)`;
    }
    paintTopoStatic();
  };

  window.resetCoreJamming = function() {
    isCoreJammed = false;
    const statusEl = document.getElementById('topo-status-text');
    if (statusEl) {
      statusEl.innerHTML = `<span style="color:#10b981; font-weight:700;">● NOMINAL:</span> Primary shortest path active [0-1-3-5] (All trunks healthy)`;
    }
    paintTopoStatic();
  };

  // ============================================================================
  // Canvas 2: Live D3QN Neural Network Architecture Visualizer (Slide 11)
  // ============================================================================
  let neuralCanvas = document.getElementById('neural-sim-canvas');
  let neuralSimRunning = false;
  let neuralAnimId = null;

  function drawNeuralFrame(ctx, w, h, pulseStep = 0) {
    ctx.clearRect(0, 0, w, h);
    const layers = [
      { name: "Input (10D)", count: 7, x: w * 0.12, color: "#38bdf8" },
      { name: "Dense (128)", count: 6, x: w * 0.35, color: "#818cf8" },
      { name: "Value V(s)", count: 2, x: w * 0.65, yOffset: -h * 0.20, color: "#f59e0b" },
      { name: "Adv A(s,a)", count: 4, x: w * 0.65, yOffset: h * 0.20, color: "#10b981" },
      { name: "Q(s,a) Output", count: 4, x: w * 0.88, color: "#a855f7" }
    ];

    // Draw Synapses
    ctx.lineWidth = 1.2;
    ctx.strokeStyle = "rgba(148, 163, 184, 0.18)";
    for (let l = 0; l < layers.length - 1; l++) {
      const l1 = layers[l];
      const l2 = layers[l + 1];
      for (let i = 0; i < l1.count; i++) {
        const y1 = (h / (l1.count + 1)) * (i + 1) + (l1.yOffset || 0);
        for (let j = 0; j < l2.count; j++) {
          const y2 = (h / (l2.count + 1)) * (j + 1) + (l2.yOffset || 0);
          ctx.beginPath();
          ctx.moveTo(l1.x, y1);
          ctx.lineTo(l2.x, y2);
          ctx.stroke();

          // Synaptic pulse
          const pulsePhase = (pulseStep + (i * 0.2 + j * 0.3)) % 1;
          const px = l1.x + (l2.x - l1.x) * pulsePhase;
          const py = y1 + (y2 - y1) * pulsePhase;
          ctx.fillStyle = l2.color;
          ctx.beginPath();
          ctx.arc(px, py, 3, 0, Math.PI * 2);
          ctx.fill();
        }
      }
    }

    // Draw Neurons
    layers.forEach(layer => {
      for (let i = 0; i < layer.count; i++) {
        const ny = (h / (layer.count + 1)) * (i + 1) + (layer.yOffset || 0);
        ctx.beginPath();
        ctx.arc(layer.x, ny, 11, 0, Math.PI * 2);
        ctx.fillStyle = "#0f172a";
        ctx.strokeStyle = layer.color;
        ctx.lineWidth = 2.5;
        ctx.fill();
        ctx.stroke();
      }

      // Layer Name
      ctx.fillStyle = layer.color;
      ctx.font = "bold 13px Outfit";
      ctx.textAlign = "center";
      const labelY = (layer.yOffset ? (layer.yOffset < 0 ? 32 : h - 18) : h - 18);
      ctx.fillText(layer.name, layer.x, labelY);
    });
  }

  function paintNeuralStatic() {
    neuralCanvas = document.getElementById('neural-sim-canvas');
    if (!neuralCanvas) return;
    const w = neuralCanvas.width = 960;
    const h = neuralCanvas.height = 540;
    const ctx = neuralCanvas.getContext('2d');
    drawNeuralFrame(ctx, w, h, 0);
  }

  function initNeuralSimulation() {
    neuralCanvas = document.getElementById('neural-sim-canvas');
    if (!neuralCanvas) return;
    const w = neuralCanvas.width = 960;
    const h = neuralCanvas.height = 540;
    const ctx = neuralCanvas.getContext('2d');
    let pulseStep = 0;

    function renderNeural() {
      if (!neuralSimRunning) return;
      pulseStep += 0.04;
      drawNeuralFrame(ctx, w, h, pulseStep);
      neuralAnimId = requestAnimationFrame(renderNeural);
    }

    if (neuralAnimId) cancelAnimationFrame(neuralAnimId);
    neuralSimRunning = true;
    renderNeural();
  }

  // ============================================================================
  // Canvas 3: Live 3-Node HA Controller Failover Simulator (Slide 25)
  // ============================================================================
  let haCanvas = document.getElementById('ha-sim-canvas');
  let haSimRunning = false;
  let haAnimId = null;

  let haCluster = {
    primary: { id: "primary", name: "Primary Master", port: 6633, isAlive: true },
    backup1: { id: "backup1", name: "Backup 1", port: 6634, isAlive: true },
    backup2: { id: "backup2", name: "Backup 2", port: 6635, isAlive: true }
  };

  function getActiveHaLeader() {
    if (haCluster.primary.isAlive) return "primary";
    if (haCluster.backup1.isAlive) return "backup1";
    if (haCluster.backup2.isAlive) return "backup2";
    return "none";
  }

  function drawHaFrame(ctx, w, h, beat = 0) {
    ctx.clearRect(0, 0, w, h);
    const activeLeader = getActiveHaLeader();
    const isTotalOutage = (activeLeader === "none");

    const controllerNodes = [
      { id: "primary", name: "Primary Master", port: 6633, x: w * 0.20, y: h * 0.28 },
      { id: "backup1", name: "Backup 1 (Hot)", port: 6634, x: w * 0.50, y: h * 0.28 },
      { id: "backup2", name: "Backup 2 (Hot)", port: 6635, x: w * 0.80, y: h * 0.28 }
    ];

    const switches = [
      { id: "s1", x: w * 0.25, y: h * 0.76 },
      { id: "s2", x: w * 0.50, y: h * 0.76 },
      { id: "s3", x: w * 0.75, y: h * 0.76 }
    ];

    // Draw Data Plane Inter-Switch Links
    ctx.beginPath();
    ctx.moveTo(switches[0].x, switches[0].y);
    ctx.lineTo(switches[1].x, switches[1].y);
    ctx.lineTo(switches[2].x, switches[2].y);
    ctx.lineWidth = isTotalOutage ? 5 : 3;
    ctx.strokeStyle = isTotalOutage ? "#38bdf8" : "rgba(56, 189, 248, 0.4)";
    ctx.stroke();

    // If Total Outage, show Fail-Secure autonomous data plane forwarding
    if (isTotalOutage) {
      ctx.fillStyle = "#38bdf8";
      ctx.font = "bold 14px Outfit";
      ctx.textAlign = "center";
      ctx.fillText("⚡ FAIL-SECURE ACTIVE: KERNEL CACHED FORWARDING AT LINE RATE ⚡", w * 0.50, h * 0.54);

      // Animated data packet between switches
      const sp = (beat * 0.5) % 1;
      const spx = switches[0].x + (switches[2].x - switches[0].x) * sp;
      ctx.beginPath();
      ctx.arc(spx, switches[1].y, 6, 0, Math.PI * 2);
      ctx.fillStyle = "#38bdf8";
      ctx.shadowColor = "#38bdf8";
      ctx.shadowBlur = 10;
      ctx.fill();
      ctx.shadowBlur = 0;
    }

    // Draw Switch to Controller OpenFlow Channels
    switches.forEach(sw => {
      controllerNodes.forEach(c => {
        const isAlive = haCluster[c.id].isAlive;
        const isMaster = (c.id === activeLeader);

        ctx.beginPath();
        ctx.moveTo(sw.x, sw.y);
        ctx.lineTo(c.x, c.y);
        ctx.lineWidth = isMaster ? 3.5 : 1.5;
        ctx.strokeStyle = !isAlive
          ? "rgba(239, 68, 68, 0.18)"
          : (isMaster ? "#10b981" : "rgba(148, 163, 184, 0.22)");
        ctx.stroke();

        // Draw active OpenFlow communication packet
        if (isMaster && isAlive) {
          const p = (beat * 0.4) % 1;
          const px = sw.x + (c.x - sw.x) * p;
          const py = sw.y + (c.y - sw.y) * p;
          ctx.beginPath();
          ctx.arc(px, py, 5, 0, Math.PI * 2);
          ctx.fillStyle = "#10b981";
          ctx.fill();
        }
      });
    });

    // Draw Controllers
    controllerNodes.forEach(c => {
      const isAlive = haCluster[c.id].isAlive;
      const isMaster = (c.id === activeLeader);

      ctx.beginPath();
      ctx.arc(c.x, c.y, 34, 0, Math.PI * 2);
      ctx.fillStyle = !isAlive ? "#ef4444" : (isMaster ? "#059669" : "#1e293b");
      ctx.strokeStyle = isMaster ? "#10b981" : (!isAlive ? "#dc2626" : "#38bdf8");
      ctx.lineWidth = 3.5;
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = "#fff";
      ctx.font = "bold 12px Outfit";
      ctx.textAlign = "center";
      ctx.fillText(isMaster ? "MASTER" : (!isAlive ? "DEAD" : "STANDBY"), c.x, c.y + 4);

      ctx.font = "12px Inter";
      ctx.fillStyle = "#94a3b8";
      ctx.fillText(`Port :${c.port}`, c.x, c.y + 52);
    });

    // Draw Switches
    switches.forEach(sw => {
      ctx.beginPath();
      ctx.arc(sw.x, sw.y, 20, 0, Math.PI * 2);
      ctx.fillStyle = "#0f172a";
      ctx.strokeStyle = isTotalOutage ? "#10b981" : "#38bdf8";
      ctx.lineWidth = 2.5;
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = "#f8fafc";
      ctx.font = "bold 12px Fira Code";
      ctx.textAlign = "center";
      ctx.fillText(sw.id.toUpperCase(), sw.x, sw.y + 4);
    });
  }

  function paintHaStatic() {
    haCanvas = document.getElementById('ha-sim-canvas');
    if (!haCanvas) return;
    const w = haCanvas.width = 960;
    const h = haCanvas.height = 540;
    const ctx = haCanvas.getContext('2d');
    drawHaFrame(ctx, w, h, 0);
  }

  function initHaSimulation() {
    haCanvas = document.getElementById('ha-sim-canvas');
    if (!haCanvas) return;
    const w = haCanvas.width = 960;
    const h = haCanvas.height = 540;
    const ctx = haCanvas.getContext('2d');
    let beat = 0;

    function renderHA() {
      if (!haSimRunning) return;
      beat += 0.05;
      drawHaFrame(ctx, w, h, beat);
      haAnimId = requestAnimationFrame(renderHA);
    }

    if (haAnimId) cancelAnimationFrame(haAnimId);
    haSimRunning = true;
    renderHA();
  }

  window.triggerPrimaryCrash = function() {
    haCluster.primary.isAlive = false;
    const leader = getActiveHaLeader();
    const haText = document.getElementById('ha-status-text');
    if (haText) {
      if (leader !== "none") {
        haText.innerHTML = `
          <span style="color:#ef4444; font-weight:700;">💥 PRIMARY CRASH INJECTED!</span><br>
          • Instantaneous failover promoted <strong>${haCluster[leader].name} (Port :${haCluster[leader].port})</strong> in <strong>0.003 ms</strong> (Promotion) / <strong>38.2 ms</strong> (HTTP Transparent Retry).<br>
          • Closed-loop D3QN routing operational. <strong>Zero packet loss!</strong>
        `;
      } else {
        triggerKillAllOutage();
      }
    }
  };

  window.triggerBackup1Crash = function() {
    haCluster.backup1.isAlive = false;
    const leader = getActiveHaLeader();
    const haText = document.getElementById('ha-status-text');
    if (haText) {
      if (leader !== "none") {
        haText.innerHTML = `
          <span style="color:#f59e0b; font-weight:700;">⚠️ BACKUP 1 CRASHED!</span><br>
          • Cascaded failover to <strong>${haCluster[leader].name} (Port :${haCluster[leader].port})</strong> in <strong>38.68 ms</strong>.<br>
          • Double-fault cascade survived seamlessly.
        `;
      } else {
        triggerKillAllOutage();
      }
    }
  };

  window.triggerKillAllOutage = function() {
    haCluster.primary.isAlive = false;
    haCluster.backup1.isAlive = false;
    haCluster.backup2.isAlive = false;
    const haText = document.getElementById('ha-status-text');
    if (haText) {
      haText.innerHTML = `
        <span style="color:#ef4444; font-weight:800;">🚨 TOTAL CONTROLLER OUTAGE: ALL 3 CONTROLLERS DEAD!</span><br>
        • Open vSwitch datapaths entered <strong>Fail-Secure Autonomous Survival Mode</strong>.<br>
        • <strong>Existing TCAM flow tables remain active in kernel!</strong> Packets forwarded at full wire speed.<br>
        • D3QN dynamic route updates paused until self-healing watchdog restores controller quorum.
      `;
    }
  };

  window.restorePrimaryCluster = function() {
    haCluster.primary.isAlive = true;
    haCluster.backup1.isAlive = true;
    haCluster.backup2.isAlive = true;
    const haText = document.getElementById('ha-status-text');
    if (haText) {
      haText.innerHTML = `
        <span style="color:#10b981; font-weight:700;">🛡️ CLUSTER NOMINAL:</span> All 3 Controllers Online & Synchronized. Primary Master active on port 6633. D3QN closed-loop routing active.
      `;
    }
  };

  // ============================================================================
  // Slide Enter Handler (Activates Canvases & Metric Counters)
  // ============================================================================
  function onSlideEnter(index) {
    // Slide 7 or 18: Topology Sim
    if (index === 6 || index === 17) {
      setTimeout(initTopoSimulation, 100);
    }
    // Slide 11: Neural Network Sim
    if (index === 10) {
      setTimeout(initNeuralSimulation, 100);
    }
    // Slide 25: HA Cluster Sim
    if (index === 24) {
      setTimeout(initHaSimulation, 100);
    }
    // Slide 15: Animated Counter Dials
    if (index === 14) {
      animateCounters();
    }
  }

  function animateCounters() {
    const counters = [
      { id: "counter-relief", target: 23.07, prefix: "+", suffix: "%", decimals: 2 },
      { id: "counter-latency", target: 42.80, prefix: "-", suffix: "%", decimals: 2 },
      { id: "counter-loss", target: 0.00, prefix: "", suffix: "%", decimals: 2 },
      { id: "counter-infer", target: 0.04, prefix: "", suffix: " ms", decimals: 2 }
    ];

    counters.forEach(c => {
      const el = document.getElementById(c.id);
      if (!el) return;
      let start = 0;
      const duration = 1200;
      const t0 = performance.now();

      function updateCounter(now) {
        const p = Math.min((now - t0) / duration, 1);
        const ease = 1 - Math.pow(1 - p, 3);
        const val = (c.target * ease).toFixed(c.decimals);
        el.textContent = `${c.prefix}${val}${c.suffix}`;
        if (p < 1) requestAnimationFrame(updateCounter);
      }
      requestAnimationFrame(updateCounter);
    });
  }

  function paintAllCanvasesStatic() {
    paintTopoStatic();
    paintNeuralStatic();
    paintHaStatic();
  }

  // Expose global presentation and simulation controls
  window.updateSlide = updateSlide;
  window.goToSlide = updateSlide;
  window.nextSlide = nextSlide;
  window.prevSlide = prevSlide;
  window.initTopoSimulation = initTopoSimulation;
  window.initNeuralSimulation = initNeuralSimulation;
  window.initHaSimulation = initHaSimulation;
  window.paintTopoStatic = paintTopoStatic;
  window.paintNeuralStatic = paintNeuralStatic;
  window.paintHaStatic = paintHaStatic;
  window.paintAllCanvasesStatic = paintAllCanvasesStatic;

  window.addEventListener('beforeprint', paintAllCanvasesStatic);

  // Paint all static canvas frames immediately so PDF and background tabs have complete visuals
  paintAllCanvasesStatic();

  // Initialize presentation
  updateSlide(0);
});
