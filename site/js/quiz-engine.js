/**
 * QuizEngine — loads questions from data/questions.json, renders MC quiz,
 * scores with partial credit (exam rule), saves to IndexedDB via StudentDB.
 *
 * Usage: QuizEngine.init('oerek-principles', 'quiz-container')
 *
 * Scoring rule (mirrors TU Wien Reihungstest Part A):
 *   For a question with k correct answers:
 *     +1/k  for each correct option ticked
 *     -1/k  for each incorrect option ticked
 *     floor at 0 (no negative per-question score)
 *   Total score = sum of per-question scores, expressed as %.
 */

const QuizEngine = (() => {

  // ── Helpers ────────────────────────────────────────────────────────────────

  function resolveDataUrl() {
    // Works from any subdirectory: find the root by going up from current page.
    const loc = window.location.href;
    // Strip filename, keep directory
    const dir = loc.substring(0, loc.lastIndexOf('/') + 1);
    // Walk up to site root (one level up from /quizzes/)
    const root = dir.endsWith('/quizzes/')
      ? dir.slice(0, -'quizzes/'.length)
      : dir;
    return root + 'data/questions.json';
  }

  function pad2(n) { return String(n).padStart(2, '0'); }

  function formatDuration(seconds) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return m > 0 ? `${m}m ${pad2(s)}s` : `${s}s`;
  }

  function scoreQuestion(question, selectedIndices) {
    const correct = question.correct;
    const k = correct.length;
    if (k === 0) return 0;

    let raw = 0;
    selectedIndices.forEach(idx => {
      if (correct.includes(idx)) {
        raw += 1 / k;
      } else {
        raw -= 1 / k;
      }
    });
    return Math.max(0, raw);
  }

  // ── Rendering ──────────────────────────────────────────────────────────────

  function countByDifficulty(questions) {
    const c = { easy: 0, medium: 0, hard: 0 };
    questions.forEach(q => { c[q.difficulty || 'medium']++; });
    return c;
  }

  function renderStartScreen(container, questions, quizId, currentTimedMode) {
    const counts = countByDifficulty(questions);
    const timerChecked = currentTimedMode ? 'checked' : '';
    const timerRowHtml = `
        <div style="margin:1.25rem 0">
          <label style="display:flex;align-items:center;gap:0.6rem;cursor:pointer;color:var(--tu-text-bright);font-weight:600">
            <input type="checkbox" id="qe-timed-toggle" ${timerChecked} style="width:1.1rem;height:1.1rem;cursor:pointer">
            &#9200; Zeitlimit: 1 Minute pro Frage
          </label>
        </div>`;
    container.innerHTML = `
      <div class="card">
        <div class="card-title">&#9654; Quiz bereit</div>
        <p class="text-muted" style="margin:0.5rem 0">Verfügbar: ${questions.length} Fragen (${counts.easy} leicht, ${counts.medium} mittel, ${counts.hard} schwer)</p>

        <div style="margin:1.25rem 0">
          <label style="color:var(--tu-text-bright);font-weight:600;display:block;margin-bottom:0.5rem">Anzahl Fragen</label>
          <div id="qe-count-select" style="display:flex;gap:0.25rem;flex-wrap:wrap">
            <button class="btn btn-outline qe-opt-btn" data-count="5" style="font-size:0.85rem">5</button>
            <button class="btn btn-primary qe-opt-btn" data-count="10" style="font-size:0.85rem">10</button>
            <button class="btn btn-outline qe-opt-btn" data-count="all" style="font-size:0.85rem">Alle (${questions.length})</button>
          </div>
        </div>

        <div style="margin:1.25rem 0">
          <label style="color:var(--tu-text-bright);font-weight:600;display:block;margin-bottom:0.5rem">Schwierigkeitsgrad</label>
          <div id="qe-diff-select" style="display:flex;gap:0.25rem;flex-wrap:wrap">
            <button class="btn btn-outline qe-opt-btn" data-diff="easy" style="font-size:0.85rem">Leicht (${counts.easy})</button>
            <button class="btn btn-outline qe-opt-btn" data-diff="medium" style="font-size:0.85rem">Mittel (${counts.medium})</button>
            <button class="btn btn-outline qe-opt-btn" data-diff="hard" style="font-size:0.85rem">Schwer (${counts.hard})</button>
            <button class="btn btn-primary qe-opt-btn" data-diff="mixed" style="font-size:0.85rem">Gemischt</button>
          </div>
        </div>

        ${timerRowHtml}

        <table style="margin:1rem 0;font-size:0.85rem">
          <tr><td style="color:var(--tu-text-muted)">Format</td><td>Multiple Choice (alle richtigen ankreuzen)</td></tr>
          <tr><td style="color:var(--tu-text-muted)">Bewertung</td><td>Teilpunkte; Abzug für falsche Kreuze (min. 0/Frage)</td></tr>
        </table>

        <div style="margin-top:1rem;display:flex;gap:0.75rem;align-items:center;flex-wrap:wrap">
          <button id="qe-start-btn" class="btn btn-primary" style="font-size:1rem;padding:0.75rem 2rem">
            &#9654; Quiz starten
          </button>
          <div id="qe-lang-toggle" style="display:flex;gap:0.25rem;background:var(--tu-surface);border-radius:var(--radius);padding:0.25rem">
            <button class="lang-btn active" data-lang="de" style="padding:0.4rem 0.8rem;border:none;border-radius:6px;background:var(--tu-blue);color:#fff;cursor:pointer;font-size:0.85rem">DE</button>
            <button class="lang-btn" data-lang="en" style="padding:0.4rem 0.8rem;border:none;border-radius:6px;background:transparent;color:var(--tu-text-muted);cursor:pointer;font-size:0.85rem">EN</button>
          </div>
        </div>
      </div>`;
  }

  // ── Visual Matrizen renderer ──────────────────────────────────────────────
  const SHAPE_MAP = {
    'Kreis': '&#9679;', 'kreis': '&#9679;', 'circle': '&#9679;',
    'Dreieck': '&#9650;', 'dreieck': '&#9650;', 'triangle': '&#9650;',
    'Quadrat': '&#9632;', 'quadrat': '&#9632;', 'square': '&#9632;',
    'Stern': '&#9733;', 'stern': '&#9733;', 'star': '&#9733;',
    'Herz': '&#9829;', 'herz': '&#9829;', 'heart': '&#9829;',
    'Pfeil': '&#10148;', 'pfeil': '&#10148;', 'arrow': '&#10148;',
    'Raute': '&#9670;', 'raute': '&#9670;', 'diamond': '&#9670;',
    'Sechseck': '&#11042;', 'sechseck': '&#11042;', 'hexagon': '&#11042;',
    'Punkt': '&#8226;', 'punkt': '&#8226;', 'dot': '&#8226;',
  };

  const COLOR_MAP = {
    'schwarz': 'shape-black', 'black': 'shape-black',
    'weiß': 'shape-white', 'weiss': 'shape-white', 'white': 'shape-white',
    'grau': 'shape-grey', 'grey': 'shape-grey', 'gray': 'shape-grey',
    'gestreift': 'shape-striped', 'striped': 'shape-striped',
    'horizontal gestreift': 'shape-striped', 'vertikal gestreift': 'shape-striped',
    'kariert': 'shape-striped', 'gepunktet': 'shape-striped',
  };

  const SIZE_MAP = {
    'groß': 'size-big', 'gross': 'size-big', 'big': 'size-big', 'large': 'size-big',
    'mittel': 'size-medium', 'medium': 'size-medium',
    'klein': 'size-small', 'small': 'size-small',
  };

  function parseMatrixCell(cellText) {
    cellText = cellText.replace(/[\[\]]/g, '').trim();
    if (cellText === '?' || cellText === '') return null; // empty cell

    let shape = '&#9679;', colorCls = 'shape-black', sizeCls = '';
    const parts = cellText.split(',').map(s => s.trim().toLowerCase());

    for (const p of parts) {
      // Check count prefix (e.g. "3 Dreiecke")
      const countMatch = p.match(/^(\d+)\s+(.+)/);
      if (countMatch) {
        const count = parseInt(countMatch[1]);
        const shapeName = countMatch[2].replace(/e$/, '').replace(/s$/, ''); // naive deplural
        const sym = SHAPE_MAP[shapeName] || SHAPE_MAP[shapeName.charAt(0).toUpperCase() + shapeName.slice(1)] || '&#9679;';
        shape = (sym + ' ').repeat(count).trim();
        continue;
      }
      // Check shapes
      for (const [key, sym] of Object.entries(SHAPE_MAP)) {
        if (p === key.toLowerCase() || p.endsWith(key.toLowerCase())) { shape = sym; break; }
      }
      // Check colors
      for (const [key, cls] of Object.entries(COLOR_MAP)) {
        if (p.includes(key)) { colorCls = cls; break; }
      }
      // Check sizes
      for (const [key, cls] of Object.entries(SIZE_MAP)) {
        if (p === key) { sizeCls = cls; break; }
      }
    }
    return { shape, colorCls, sizeCls };
  }

  function renderMatrixGrid(questionText) {
    const lines = questionText.split('\n');
    const cells = [];
    for (const line of lines) {
      const zeileMatch = line.match(/Zeile\s*\d+:\s*(.*)/i) || line.match(/Row\s*\d+:\s*(.*)/i);
      if (!zeileMatch) continue;
      const rowText = zeileMatch[1];
      const cellTexts = rowText.split(/\]\s*\[/).map(s => s.replace(/[\[\]]/g, '').trim());
      for (const ct of cellTexts) {
        if (ct === '?' || ct === '') {
          cells.push('<div class="matrix-cell empty"></div>');
        } else {
          const parsed = parseMatrixCell('[' + ct + ']');
          if (parsed) {
            cells.push(`<div class="matrix-cell ${parsed.sizeCls}"><span class="shape ${parsed.colorCls}">${parsed.shape}</span></div>`);
          } else {
            cells.push('<div class="matrix-cell empty"></div>');
          }
        }
      }
    }
    if (cells.length < 4) return null; // not enough cells to render a grid
    // Extract the question part (after the grid)
    const questionPart = lines.filter(l => !l.match(/Zeile|Row|Matrix|Muster|^$/i)).join('<br>');
    return `<div class="matrix-grid">${cells.join('')}</div><p style="margin-top:0.75rem">${questionPart}</p>`;
  }

  function renderQuestions(container, questions, lang, timedMode) {
    const html = questions.map((q, qi) => {
      const qText = lang === 'en' ? (q.question_en || q.question_de) : q.question_de;
      const opts  = lang === 'en' ? (q.options_en  || q.options_de)  : q.options_de;

      // Try visual matrix rendering for tagged questions
      const isMatrix = (q.tags || []).includes('matrizen');
      let displayText = qText.replace(/\n/g, '<br>');
      if (isMatrix) {
        const gridHtml = renderMatrixGrid(qText);
        if (gridHtml) displayText = gridHtml;
      }

      const optHtml = opts.map((opt, oi) => `
        <div class="quiz-option" data-qidx="${qi}" data-oidx="${oi}" role="checkbox" aria-checked="false" tabindex="0" style="cursor:pointer">
          <input type="checkbox" data-qidx="${qi}" data-oidx="${oi}" style="display:none">
          <span>${opt}</span>
        </div>`).join('');

      return `
        <div class="quiz-question" id="qe-q-${qi}">
          <div style="margin-bottom:0.5rem">
            <span class="badge badge-info">Frage ${qi + 1}</span>
          </div>
          <div class="quiz-question-text">${displayText}</div>
          <div class="qe-options">${optHtml}</div>
          <div class="quiz-explanation" id="qe-exp-${qi}">
            ${lang === 'en' ? (q.explanation_en || q.explanation_de) : q.explanation_de}
            <div style="font-size:0.78rem;color:var(--tu-text-dim);margin-top:0.4rem">Quelle: ${q.source || '—'}</div>
          </div>
        </div>`;
    }).join('');

    const timerLabel = timedMode ? '&#9200; Verbleibend: ' : '&#128336; Zeit: ';
    const cdMin = Math.floor(countdownSeconds / 60);
    const timerInitVal = timedMode ? `${cdMin}m 00s` : '0s';
    container.innerHTML = `
      <div id="qe-timer-bar" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;padding:0.75rem 1rem;background:var(--tu-surface);border-radius:var(--radius);border:1px solid var(--tu-border)">
        <span id="qe-timer-label" style="color:var(--tu-text-muted);font-size:0.9rem">${timerLabel}<span id="qe-elapsed">${timerInitVal}</span></span>
        <span style="color:var(--tu-text-muted);font-size:0.9rem">Fragen: ${questions.length}</span>
      </div>
      <div id="qe-questions">${html}</div>
      <div style="margin-top:2rem;display:flex;gap:1rem;flex-wrap:wrap">
        <button id="qe-submit-btn" class="btn btn-primary" style="font-size:1rem;padding:0.75rem 2rem">
          &#10003; Auswertung anzeigen
        </button>
        <button id="qe-reset-btn" class="btn btn-outline">
          &#8635; Neu starten
        </button>
      </div>`;
  }

  function renderResults(container, questions, userAnswers, scores, lang, durationSec) {
    const total = questions.length;
    const rawSum = scores.reduce((a, b) => a + b, 0);
    const maxScore = total; // max 1 point per question
    const percentage = Math.round((rawSum / maxScore) * 100);

    let grade, gradeClass;
    if (percentage >= 80) { grade = 'Sehr gut'; gradeClass = 'alert-success'; }
    else if (percentage >= 65) { grade = 'Gut'; gradeClass = 'alert-success'; }
    else if (percentage >= 50) { grade = 'Genügend'; gradeClass = 'alert-warning'; }
    else { grade = 'Nicht genügend'; gradeClass = 'alert-error'; }

    const summaryHtml = `
      <div class="card">
        <div class="card-title">&#127942; Ergebnis</div>
        <div class="stats-grid" style="margin:1rem 0">
          <div class="stat-card ${percentage >= 50 ? 'good' : 'urgent'}">
            <div class="stat-value">${percentage}%</div>
            <div class="stat-label">Gesamtergebnis</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">${rawSum.toFixed(1)} / ${maxScore}</div>
            <div class="stat-label">Punkte</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">${formatDuration(durationSec)}</div>
            <div class="stat-label">Zeit</div>
          </div>
          <div class="stat-card ${percentage >= 50 ? 'good' : 'urgent'}">
            <div class="stat-value">${grade}</div>
            <div class="stat-label">Bewertung</div>
          </div>
        </div>
        <div class="progress-bar"><div class="progress-fill" style="width:${percentage}%"></div></div>
        <div id="qe-db-msg" style="margin-top:0.75rem;font-size:0.85rem;color:var(--tu-text-muted)">Ergebnis wird gespeichert…</div>
      </div>`;

    const questionsHtml = questions.map((q, qi) => {
      const qText = lang === 'en' ? (q.question_en || q.question_de) : q.question_de;
      const opts  = lang === 'en' ? (q.options_en  || q.options_de)  : q.options_de;
      const expText = lang === 'en' ? (q.explanation_en || q.explanation_de) : q.explanation_de;
      const selected = userAnswers[qi] || [];
      const correct = q.correct;
      const qScore = scores[qi];

      let qHeaderClass = '';
      if (qScore >= 0.99) qHeaderClass = 'good';
      else if (qScore > 0) qHeaderClass = 'warning';
      else qHeaderClass = 'urgent';

      const optHtml = opts.map((opt, oi) => {
        const isSelected = selected.includes(oi);
        const isCorrect  = correct.includes(oi);
        let cls = 'quiz-option';
        if (isSelected && isCorrect)  cls += ' correct';
        else if (isSelected && !isCorrect) cls += ' incorrect';
        else if (!isSelected && isCorrect) cls += ' correct'; // missed correct
        const icon = isCorrect ? '&#10003;' : (isSelected ? '&#10007;' : '&#9675;');
        return `
          <div class="${cls}" style="cursor:default">
            <span style="margin-right:0.75rem;width:1rem;text-align:center">${icon}</span>
            <span>${opt}</span>
            ${isCorrect && !isSelected ? '<span style="margin-left:auto;font-size:0.75rem;color:var(--tu-success)">← vergessen</span>' : ''}
            ${isSelected && !isCorrect ? '<span style="margin-left:auto;font-size:0.75rem;color:var(--tu-error)">← falsch</span>' : ''}
          </div>`;
      }).join('');

      return `
        <div class="quiz-question" id="qe-res-${qi}">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem">
            <span class="badge badge-info">Frage ${qi + 1}</span>
            <span class="stat-value" style="font-size:1rem" class="${qHeaderClass}">${qScore.toFixed(2)} / 1.00 Pkt</span>
          </div>
          <div class="quiz-question-text">${qText}</div>
          <div class="qe-options">${optHtml}</div>
          <div class="quiz-explanation visible">
            ${expText}
            ${qScore < 0.99 && q.mistakes_de ? `<div style="margin-top:0.75rem;padding:0.75rem;background:rgba(244,67,54,0.08);border-radius:var(--radius);border-left:3px solid var(--tu-error)"><strong>Häufige Fehler:</strong> ${lang === 'en' ? (q.mistakes_en || q.mistakes_de) : q.mistakes_de}</div>` : ''}
            ${q.links && q.links.length > 0 ? `<div style="margin-top:0.5rem;font-size:0.8rem"><strong>Weiterlesen:</strong> ${q.links.map(l => '<a href="' + l.url + '" style="margin-right:0.75rem">' + l.label + '</a>').join('')}</div>` : ''}
            <div style="font-size:0.78rem;color:var(--tu-text-dim);margin-top:0.4rem">Quelle: ${q.source || '—'}</div>
            ${q.tags ? `<div style="margin-top:0.4rem;font-size:0.75rem;color:var(--tu-text-dim)">Tags: ${q.tags.map(t => '<code>' + t + '</code>').join(' ')}</div>` : ''}
          </div>
          ${qScore < 0.99 ? `
            <div style="margin-top:0.5rem">
              <button class="btn btn-outline qe-note-btn" data-qi="${qi}" style="font-size:0.75rem">&#9997; Meine Notiz / Lesson Learned</button>
              <div id="qe-note-area-${qi}" style="display:none;margin-top:0.5rem">
                <textarea id="qe-note-text-${qi}" placeholder="Was habe ich falsch verstanden? z.B. 'Ich habe kippen mit drehen verwechselt'" style="width:100%;min-height:60px;background:var(--tu-dark);color:var(--tu-text);border:1px solid var(--tu-border);border-radius:var(--radius);padding:0.5rem;font-size:0.85rem;resize:vertical"></textarea>
                <button class="btn btn-primary qe-note-save" data-qi="${qi}" style="font-size:0.75rem;margin-top:0.25rem">Notiz speichern</button>
              </div>
            </div>
          ` : ''}
        </div>`;
    }).join('');

    container.innerHTML = `
      ${summaryHtml}
      <div style="display:flex;gap:1rem;margin-bottom:1.5rem;flex-wrap:wrap">
        <button id="qe-retry-btn" class="btn btn-primary">&#8635; Nochmals versuchen</button>
        <button id="qe-retrain-btn" class="btn btn-primary" style="background:var(--tu-warning);color:#000">&#127919; Schwachstellen trainieren</button>
        <button id="qe-wrong-only-btn" class="btn btn-outline" style="border-color:var(--tu-error);color:var(--tu-error)">&#10007; Nur falsche wiederholen</button>
        <button id="qe-new-btn" class="btn btn-outline">&#8635; Neues Quiz</button>
      </div>
      <h2>Detailauswertung</h2>
      ${questionsHtml}`;
  }

  // ── Core init ──────────────────────────────────────────────────────────────

  async function init(quizId, containerId) {
    const container = document.getElementById(containerId);
    if (!container) {
      console.error(`QuizEngine: container #${containerId} not found`);
      return;
    }

    container.innerHTML = `<div class="alert alert-info">&#8987; Fragen werden geladen…</div>`;

    let allQuestions;
    try {
      const url = resolveDataUrl();
      const resp = await fetch(url);
      if (!resp.ok) throw new Error(`HTTP ${resp.status} fetching ${url}`);
      allQuestions = await resp.json();
    } catch (err) {
      container.innerHTML = `
        <div class="alert alert-error">
          <strong>Fehler beim Laden der Fragen.</strong><br>
          ${err.message}<br>
          <small>Stellen Sie sicher, dass data/questions.json erreichbar ist.</small>
        </div>`;
      return;
    }

    const questions = quizId === 'all'
      ? allQuestions
      : allQuestions.filter(q => q.quizId === quizId);
    if (questions.length === 0) {
      container.innerHTML = `
        <div class="alert alert-error">
          Keine Fragen für Quiz-ID <code>${quizId}</code> gefunden.
          Verfügbare IDs: ${[...new Set(allQuestions.map(q => q.quizId))].join(', ')}
        </div>`;
      return;
    }

    let lang = 'de';
    let startTime = null;
    let timerInterval = null;
    let selectedCount = 10;
    let selectedDiff = 'mixed';
    let activeQuestions = [];
    let timedMode = (quizId === 'all'); // default on for full mock exam
    let countdownSeconds = 600; // calculated per quiz: 1 min per question

    function buildActiveQuestions() {
      let pool = [...questions];
      // Filter by difficulty
      if (selectedDiff !== 'mixed') {
        pool = pool.filter(q => (q.difficulty || 'medium') === selectedDiff);
      }
      // Shuffle
      pool.sort(() => Math.random() - 0.5);
      // Limit count
      if (selectedCount !== 'all' && pool.length > selectedCount) {
        pool = pool.slice(0, selectedCount);
      }
      return pool;
    }

    function wireOptButtons(groupId, valueAttr, currentValue, onSelect) {
      container.querySelectorAll(`#${groupId} .qe-opt-btn`).forEach(btn => {
        btn.addEventListener('click', () => {
          container.querySelectorAll(`#${groupId} .qe-opt-btn`).forEach(b => {
            b.className = 'btn btn-outline qe-opt-btn';
          });
          btn.className = 'btn btn-primary qe-opt-btn';
          const val = btn.dataset[valueAttr];
          onSelect(val === 'all' ? 'all' : (isNaN(val) ? val : parseInt(val)));
        });
      });
    }

    // ── Start screen ───────────────────────────────────────────────────────

    function showStartScreen() {
      if (timerInterval) { clearInterval(timerInterval); timerInterval = null; }
      selectedCount = 10;
      selectedDiff = 'mixed';
      renderStartScreen(container, questions, quizId, timedMode);

      wireOptButtons('qe-count-select', 'count', 10, v => { selectedCount = v; });
      wireOptButtons('qe-diff-select', 'diff', 'mixed', v => { selectedDiff = v; });

      // Wire timed mode toggle (only present for quizId === 'all')
      const timedToggle = container.querySelector('#qe-timed-toggle');
      if (timedToggle) {
        timedToggle.addEventListener('change', () => { timedMode = timedToggle.checked; });
      }

      container.querySelector('#qe-start-btn').addEventListener('click', () => {
        activeQuestions = buildActiveQuestions();
        if (activeQuestions.length === 0) {
          alert('Keine Fragen für diese Auswahl verfügbar. Versuchen Sie eine andere Kombination.');
          return;
        }
        startTime = Date.now();
        showQuizScreen();
      });

      container.querySelectorAll('#qe-lang-toggle .lang-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          lang = btn.dataset.lang;
          container.querySelectorAll('#qe-lang-toggle .lang-btn').forEach(b => {
            b.style.background = 'transparent';
            b.style.color = 'var(--tu-text-muted)';
          });
          btn.style.background = 'var(--tu-blue)';
          btn.style.color = '#fff';
        });
      });
    }

    // ── Quiz screen ────────────────────────────────────────────────────────

    function showQuizScreen() {
      // 1 minute per question
      countdownSeconds = activeQuestions.length * 60;
      renderQuestions(container, activeQuestions, lang, timedMode);
      startTimer();
      wireQuizInteractions();
    }

    function startTimer() {
      const elapsedEl = document.getElementById('qe-elapsed');
      const labelEl   = document.getElementById('qe-timer-label');
      timerInterval = setInterval(() => {
        if (!elapsedEl) { clearInterval(timerInterval); return; }
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        if (timedMode) {
          const remaining = Math.max(0, countdownSeconds - elapsed);
          const h = Math.floor(remaining / 3600);
          const m = Math.floor((remaining % 3600) / 60);
          const s = remaining % 60;
          elapsedEl.textContent = `${h}h ${pad2(m)}m ${pad2(s)}s`;
          // Colour warnings
          if (remaining <= 300) {
            if (labelEl) labelEl.style.color = 'var(--tu-error, #f44336)';
          } else if (remaining <= 900) {
            if (labelEl) labelEl.style.color = 'var(--tu-warning, #ff9800)';
          }
          // Auto-submit when time runs out
          if (remaining === 0) {
            clearInterval(timerInterval);
            const submitBtn = document.getElementById('qe-submit-btn');
            if (submitBtn) submitBtn.click();
          }
        } else {
          elapsedEl.textContent = formatDuration(elapsed);
        }
      }, 1000);
    }

    function wireQuizInteractions() {
      // Option click toggles selection — whole row is clickable
      container.querySelectorAll('.quiz-option').forEach(el => {
        el.addEventListener('click', () => {
          const cb = el.querySelector('input[type="checkbox"]');
          cb.checked = !cb.checked;
          el.classList.toggle('selected', cb.checked);
          el.setAttribute('aria-checked', String(cb.checked));
        });
        el.addEventListener('keydown', (e) => {
          if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); el.click(); }
        });
      });

      container.querySelector('#qe-submit-btn').addEventListener('click', () => {
        clearInterval(timerInterval);
        const durationSec = Math.floor((Date.now() - startTime) / 1000);
        const userAnswers = collectAnswers();
        const scores = activeQuestions.map((q, qi) => scoreQuestion(q, userAnswers[qi]));
        showResultsScreen(userAnswers, scores, durationSec);
      });

      container.querySelector('#qe-reset-btn').addEventListener('click', () => {
        clearInterval(timerInterval);
        showStartScreen();
      });
    }

    function collectAnswers() {
      return activeQuestions.map((_, qi) => {
        const checked = [];
        container.querySelectorAll(`input[type="checkbox"][data-qidx="${qi}"]`).forEach(cb => {
          if (cb.checked) checked.push(Number(cb.dataset.oidx));
        });
        return checked;
      });
    }

    // ── Results screen ─────────────────────────────────────────────────────

    function showResultsScreen(userAnswers, scores, durationSec) {
      const rawSum = scores.reduce((a, b) => a + b, 0);
      const total = activeQuestions.length;
      const percentage = Math.round((rawSum / total) * 100);

      renderResults(container, activeQuestions, userAnswers, scores, lang, durationSec);

      // Save to IndexedDB
      if (typeof StudentDB !== 'undefined') {
        StudentDB.addQuizAttempt({
          quizId,
          score: rawSum,
          total,
          percentage,
          answers: userAnswers,
          durationSec
        }).then(() => {
          const msg = document.getElementById('qe-db-msg');
          if (msg) msg.textContent = 'Lokal gespeichert.';
        }).catch(() => {});
      }

      // Sync to Supabase (non-blocking)
      if (typeof SupabaseSync !== 'undefined') {
        SupabaseSync.saveAttempt({ quizId, score: rawSum, total, percentage, durationSec }).then(ok => {
          const msg = document.getElementById('qe-db-msg');
          if (msg) msg.textContent = ok ? 'Gespeichert (lokal + cloud).' : 'Lokal gespeichert (cloud offline).';
        });
      }

      // Record mistakes for wrong answers
      activeQuestions.forEach((q, qi) => {
        if (scores[qi] < 0.99) {
          const mistakeData = {
            questionId: q.id,
            questionText: (q.question_de || '').slice(0, 120),
            tags: q.tags || [],
            selectedAnswers: userAnswers[qi],
            correctAnswers: q.correct,
            note: ''
          };
          if (typeof StudentDB !== 'undefined') {
            StudentDB.addMistake(mistakeData).catch(() => {});
          }
          if (typeof SupabaseSync !== 'undefined') {
            SupabaseSync.saveMistake(mistakeData).catch(() => {});
          }
        }
      });

      // Wire "Note my mistake" inputs
      container.querySelectorAll('.qe-note-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const qi = Number(btn.dataset.qi);
          const noteArea = document.getElementById('qe-note-area-' + qi);
          if (noteArea) noteArea.style.display = noteArea.style.display === 'none' ? 'block' : 'none';
        });
      });

      container.querySelectorAll('.qe-note-save').forEach(btn => {
        btn.addEventListener('click', () => {
          const qi = Number(btn.dataset.qi);
          const textarea = document.getElementById('qe-note-text-' + qi);
          if (!textarea || !textarea.value.trim()) return;
          const q = activeQuestions[qi];
          const noteData = { questionId: q.id, questionText: (q.question_de || '').slice(0, 120), tags: q.tags || [], note: textarea.value.trim() };
          if (typeof StudentDB !== 'undefined') StudentDB.addMistake(noteData).catch(() => {});
          if (typeof SupabaseSync !== 'undefined') SupabaseSync.saveMistake(noteData).catch(() => {});
          btn.textContent = 'Gespeichert!';
          btn.disabled = true;
          textarea.disabled = true;
        });
      });

      // Wire retry / new / retrain buttons
      const retryBtn = document.getElementById('qe-retry-btn');
      if (retryBtn) retryBtn.addEventListener('click', () => {
        startTime = Date.now();
        showQuizScreen();
      });

      const newBtn = document.getElementById('qe-new-btn');
      if (newBtn) newBtn.addEventListener('click', showStartScreen);

      // Review wrong only
      const wrongBtn = document.getElementById('qe-wrong-only-btn');
      if (wrongBtn) wrongBtn.addEventListener('click', () => {
        const wrongQs = activeQuestions.filter((q, qi) => scores[qi] < 0.99);
        if (wrongQs.length === 0) {
          alert('Alle Fragen richtig! Nichts zu wiederholen.');
          return;
        }
        activeQuestions = wrongQs;
        startTime = Date.now();
        showQuizScreen();
      });

      const retrainBtn = document.getElementById('qe-retrain-btn');
      if (retrainBtn) retrainBtn.addEventListener('click', async () => {
        // Build quiz from weak tags
        let weakTags = [];
        if (typeof StudentDB !== 'undefined') {
          weakTags = await StudentDB.getWeakTags(10);
        }
        if (weakTags.length === 0) {
          alert('Keine Fehlerdaten vorhanden. Machen Sie zuerst ein Quiz.');
          return;
        }
        const weakTagNames = weakTags.map(t => t.tag);
        activeQuestions = questions
          .filter(q => (q.tags || []).some(t => weakTagNames.includes(t)))
          .sort(() => Math.random() - 0.5)
          .slice(0, selectedCount === 'all' ? 999 : selectedCount);
        if (activeQuestions.length === 0) {
          alert('Keine passenden Fragen gefunden.');
          return;
        }
        startTime = Date.now();
        showQuizScreen();
      });
    }

    // ── Boot ───────────────────────────────────────────────────────────────
    showStartScreen();
  }

  return { init };

})();
