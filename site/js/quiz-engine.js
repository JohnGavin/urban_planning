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
    const timerBtnStyle = currentTimedMode
      ? 'background:var(--tu-blue);color:#fff;border-color:var(--tu-blue)'
      : 'background:transparent;color:var(--tu-text-muted);border-color:var(--tu-border)';
    const timerRowHtml = `
        <div style="margin:1.25rem 0">
          <input type="checkbox" id="qe-timed-toggle" ${timerChecked} style="display:none">
          <button type="button" id="qe-timed-btn" class="btn" style="font-size:0.9rem;padding:0.6rem 1.2rem;border:2px solid;border-radius:var(--radius);cursor:pointer;transition:all 0.2s;${timerBtnStyle}">
            &#9200; Zeitlimit: 1 Minute pro Frage
          </button>
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

        ${quizId === 'cognitive' || quizId === 'all' ? `
        <div style="margin:1.25rem 0">
          <label style="color:var(--tu-text-bright);font-weight:600;display:block;margin-bottom:0.5rem">Thema (nur kognitiv)</label>
          <div id="qe-tag-select" style="display:flex;gap:0.25rem;flex-wrap:wrap">
            <button class="btn btn-primary qe-opt-btn" data-tag="all" style="font-size:0.85rem">Alle Themen</button>
            <button class="btn btn-outline qe-opt-btn" data-tag="wuerfel" style="font-size:0.85rem">Würfel</button>
            <button class="btn btn-outline qe-opt-btn" data-tag="matrizen" style="font-size:0.85rem">Matrizen</button>
            <button class="btn btn-outline qe-opt-btn" data-tag="zahlenfolge" style="font-size:0.85rem">Zahlenfolgen</button>
            <button class="btn btn-outline qe-opt-btn" data-tag="logik" style="font-size:0.85rem">Logik</button>
            <button class="btn btn-outline qe-opt-btn" data-tag="rechenoperationen" style="font-size:0.85rem">Rechenop.</button>
            <button class="btn btn-outline qe-opt-btn" data-tag="analogie" style="font-size:0.85rem">Analogien</button>
          </div>
        </div>` : ''}

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
  // SVG shapes with size support + dot overlays for cross-browser rendering
  const SVG_SIZES = { 'groß': 44, 'gross': 44, 'big': 44, 'mittel': 30, 'medium': 30, 'klein': 18, 'small': 18 };
  // Colour mapping: schwarz=filled, weiß=outline only, grau=half-filled
  // On dark background: schwarz=bright white, weiß=outline, grau=medium
  const SVG_COLORS = { 'schwarz': '#ffffff', 'black': '#ffffff', 'weiß': '#16213e', 'weiss': '#16213e', 'white': '#16213e', 'grau': '#888888', 'grey': '#888888', 'gray': '#888888' };
  const SVG_STROKES = { 'schwarz': 'none', 'black': 'none', 'weiß': '#cccccc', 'weiss': '#cccccc', 'white': '#cccccc', 'grau': 'none', 'grey': 'none', 'gray': 'none' };

  function svgShape(name, fill, size, stroke) {
    const c = fill || '#fff';
    const stk = stroke || 'none';
    const stkAttr = stk !== 'none' ? ` stroke="${stk}" stroke-width="2"` : '';
    const s = size || 28;
    const cx = s/2, cy = s/2, r = s*0.4;
    const shapes = {
      'kreis':    `<circle cx="${cx}" cy="${cy}" r="${r}" fill="${c}"${stkAttr}/>`,
      'dreieck':  `<polygon points="${cx},${s*0.07} ${s*0.93},${s*0.93} ${s*0.07},${s*0.93}" fill="${c}"${stkAttr}/>`,
      'quadrat':  `<rect x="${s*0.1}" y="${s*0.1}" width="${s*0.8}" height="${s*0.8}" fill="${c}"${stkAttr}/>`,
      'stern':    `<polygon points="${cx},${s*0.07} ${s*0.61},${s*0.36} ${s*0.93},${s*0.36} ${s*0.68},${s*0.57} ${s*0.79},${s*0.89} ${cx},${s*0.71} ${s*0.21},${s*0.89} ${s*0.32},${s*0.57} ${s*0.07},${s*0.36} ${s*0.39},${s*0.36}" fill="${c}"${stkAttr}/>`,
      'herz':     `<path d="M${cx} ${s*0.89} C${s*0.21} ${s*0.64} ${s*0.04} ${s*0.43} ${s*0.04} ${s*0.29} ${s*0.04} ${s*0.14} ${s*0.14} ${s*0.04} ${s*0.29} ${s*0.04} ${s*0.39} ${s*0.04} ${s*0.46} ${s*0.11} ${cx} ${s*0.18} ${s*0.54} ${s*0.11} ${s*0.61} ${s*0.04} ${s*0.71} ${s*0.04} ${s*0.86} ${s*0.04} ${s*0.96} ${s*0.14} ${s*0.96} ${s*0.29} ${s*0.96} ${s*0.43} ${s*0.79} ${s*0.64} ${cx} ${s*0.89}Z" fill="${c}"${stkAttr}/>`,
      'raute':    `<polygon points="${cx},${s*0.07} ${s*0.93},${cy} ${cx},${s*0.93} ${s*0.07},${cy}" fill="${c}"${stkAttr}/>`,
      'sechseck': `<polygon points="${s*0.25},${s*0.1} ${s*0.75},${s*0.1} ${s*0.96},${cy} ${s*0.75},${s*0.9} ${s*0.25},${s*0.9} ${s*0.04},${cy}" fill="${c}"${stkAttr}/>`,
      'pfeil':    `<polygon points="${s*0.14},${s*0.43} ${s*0.71},${s*0.43} ${s*0.71},${s*0.21} ${s*0.96},${cy} ${s*0.71},${s*0.79} ${s*0.71},${s*0.57} ${s*0.14},${s*0.57}" fill="${c}"${stkAttr}/>`,
      'punkt':    `<circle cx="${cx}" cy="${cy}" r="${s*0.18}" fill="${c}"${stkAttr}/>`,
    };
    const inner = shapes[name] || `<text x="${cx}" y="${cy}" text-anchor="middle" dominant-baseline="central" fill="${c}" font-size="${s*0.6}">${name}</text>`;
    return `<svg width="${s}" height="${s}" viewBox="0 0 ${s} ${s}">${inner}</svg>`;
  }

  function svgDots(count, fill, cellSize) {
    // Render N dots arranged in a row within the cell
    const c = fill || '#fff';
    const s = cellSize || 28;
    const dotR = Math.max(2, s * 0.08);
    const spacing = s / (count + 1);
    let dots = '';
    for (let i = 0; i < count; i++) {
      dots += `<circle cx="${spacing * (i + 1)}" cy="${s * 0.75}" r="${dotR}" fill="${c}"/>`;
    }
    return dots; // raw SVG elements to embed inside a parent SVG
  }

  const ARROW_SVGS = {
    '↑': (c, s) => `<svg width="${s||28}" height="${s||28}" viewBox="0 0 28 28"><polygon points="14,2 24,18 18,18 18,26 10,26 10,18 4,18" fill="${c}"/></svg>`,
    '↓': (c, s) => `<svg width="${s||28}" height="${s||28}" viewBox="0 0 28 28"><polygon points="14,26 24,10 18,10 18,2 10,2 10,10 4,10" fill="${c}"/></svg>`,
    '→': (c, s) => `<svg width="${s||28}" height="${s||28}" viewBox="0 0 28 28"><polygon points="26,14 10,4 10,10 2,10 2,18 10,18 10,24" fill="${c}"/></svg>`,
    '←': (c, s) => `<svg width="${s||28}" height="${s||28}" viewBox="0 0 28 28"><polygon points="2,14 18,4 18,10 26,10 26,18 18,18 18,24" fill="${c}"/></svg>`,
  };

  // Keep text fallback map for non-visual contexts
  const SHAPE_MAP = {
    'kreis': '\u25CF', 'circle': '\u25CF',
    'dreieck': '\u25B2', 'triangle': '\u25B2',
    'quadrat': '\u25A0', 'square': '\u25A0',
    'stern': '\u2605', 'star': '\u2605',
    'herz': '\u2665', 'heart': '\u2665',
    'pfeil': '\u279C', 'arrow': '\u279C',
    'raute': '\u25C6', 'diamond': '\u25C6',
    'sechseck': '\u2B22', 'hexagon': '\u2B22',
    'punkt': '\u2022', 'dot': '\u2022',
    'r': 'R',
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

  function findShape(text) {
    text = text.toLowerCase().trim();
    for (const [key, sym] of Object.entries(SHAPE_MAP)) {
      if (text === key || text.includes(key)) return sym;
    }
    // Try depluralized
    const deplural = text.replace(/en$/, '').replace(/e$/, '').replace(/s$/, '');
    for (const [key, sym] of Object.entries(SHAPE_MAP)) {
      if (deplural === key || deplural.includes(key)) return sym;
    }
    return null;
  }

  function findShapeName(text) {
    text = text.toLowerCase().trim();
    const names = ['kreis','dreieck','quadrat','stern','herz','pfeil','raute','sechseck','punkt'];
    for (const n of names) { if (text === n || text.includes(n)) return n; }
    const deplural = text.replace(/en$/, '').replace(/e$/, '').replace(/s$/, '');
    for (const n of names) { if (deplural === n || deplural.includes(n)) return n; }
    return null;
  }

  function parseMatrixCell(cellText) {
    cellText = cellText.replace(/[\[\]]/g, '').trim();
    if (cellText === '?' || cellText === '') return null;

    let shapeName = 'kreis', colorName = 'schwarz', sizeName = '', count = 1, dotCount = 0, arrowDir = null;

    // Handle "X + Y" combinations
    if (cellText.includes('+')) {
      const comboParts = cellText.split('+').map(s => s.trim());
      const names = comboParts.map(cp => findShapeName(cp) || 'punkt');
      return { shapeName: names, colorName: 'schwarz', sizeName: '', sizePixels: 28, count: 1, dotCount: 0, combo: true };
    }

    const parts = cellText.split(',').map(s => s.trim().toLowerCase());

    for (const p of parts) {
      // "Shape mit N Punkt(en)" pattern (e.g., "Quadrat mit 2 Punkten")
      const mitMatch = p.match(/(.+?)\s+mit\s+(\d+)\s+punkt/);
      if (mitMatch) {
        const sn = findShapeName(mitMatch[1]);
        if (sn) shapeName = sn;
        dotCount = parseInt(mitMatch[2]);
        continue;
      }
      // "N Punkt/Punkte" as a PROPERTY (dots on a shape)
      const dotMatch = p.match(/^(\d+)\s+punkt/);
      if (dotMatch) {
        dotCount = parseInt(dotMatch[1]);
        continue;
      }
      // "N Shapes" as COUNT (multiple shapes)
      const countMatch = p.match(/^(\d+)\s+(.+)/);
      if (countMatch) {
        const sn = findShapeName(countMatch[2]);
        if (sn) {
          count = Math.min(parseInt(countMatch[1]), 6);
          shapeName = sn;
        } else {
          dotCount = parseInt(countMatch[1]);
        }
        continue;
      }
      // Check shapes
      const sn = findShapeName(p);
      if (sn) shapeName = sn;
      // Check colors
      for (const key of Object.keys(SVG_COLORS)) { if (p.includes(key)) { colorName = key; break; } }
      // Check sizes
      for (const key of Object.keys(SVG_SIZES)) { if (p.includes(key)) { sizeName = key; break; } }
    }

    // Arrow directions
    const lt = cellText.toLowerCase();
    if (lt.includes('↑') || (lt.includes('oben') && lt.includes('pfeil'))) arrowDir = '↑';
    else if (lt.includes('↓') || (lt.includes('unten') && lt.includes('pfeil'))) arrowDir = '↓';
    else if (lt.includes('→') || (lt.includes('rechts') && lt.includes('pfeil'))) arrowDir = '→';
    else if (lt.includes('←') || (lt.includes('links') && lt.includes('pfeil'))) arrowDir = '←';

    // Calculate pixel size
    const sizePixels = SVG_SIZES[sizeName] || 28;

    return { shapeName, colorName, sizeName, sizePixels, count, dotCount, arrowDir, combo: false };
  }

  function renderCellSVG(parsed) {
    if (!parsed) return '';
    const fill = SVG_COLORS[parsed.colorName] || '#fff';
    const stroke = SVG_STROKES[parsed.colorName] || 'none';
    const sizeVal = parsed.sizePixels || 28;

    // Arrow with direction
    if (parsed.arrowDir && ARROW_SVGS[parsed.arrowDir]) {
      return ARROW_SVGS[parsed.arrowDir](fill, sizeVal);
    }

    // Combination (X + Y)
    if (parsed.combo && Array.isArray(parsed.shapeName)) {
      return parsed.shapeName.map(n => svgShape(n, fill, 20, stroke)).join('<span style="font-size:0.6rem;color:var(--tu-text-dim)">+</span>');
    }

    // Count-only (e.g., "3 Punkte" or "2 Kreise") — render N small shapes in a row
    if (parsed.count > 1) {
      const smallSize = Math.max(12, Math.floor(50 / parsed.count));
      return Array.from({length: parsed.count}, () => svgShape(parsed.shapeName, fill, smallSize, stroke)).join('');
    }

    // Shape with dots (e.g., "Stern, groß, 2 Punkte") — shape + dots below
    if (parsed.dotCount && parsed.dotCount > 0) {
      const shapeSize = Math.min(sizeVal, 36); // cap shape size to leave room for dots
      const shapeSvgInner = svgShape(parsed.shapeName, fill, shapeSize, stroke);
      // Render dots in a compact grid that fits inside 70px width
      const maxDotsPerRow = 5;
      const dotR = 3;
      const dotSpacing = 9;
      const rows = Math.ceil(parsed.dotCount / maxDotsPerRow);
      const svgH = rows * dotSpacing + 2;
      const svgW = 70;
      let dotsSvg = `<svg width="${svgW}" height="${svgH}" viewBox="0 0 ${svgW} ${svgH}">`;
      for (let i = 0; i < parsed.dotCount; i++) {
        const row = Math.floor(i / maxDotsPerRow);
        const col = i % maxDotsPerRow;
        const dotsInThisRow = Math.min(maxDotsPerRow, parsed.dotCount - row * maxDotsPerRow);
        const rowStartX = (svgW - dotsInThisRow * dotSpacing) / 2 + dotSpacing / 2;
        dotsSvg += `<circle cx="${rowStartX + col * dotSpacing}" cy="${row * dotSpacing + dotR + 1}" r="${dotR}" fill="${fill}"/>`;
      }
      dotsSvg += '</svg>';
      return `<div style="display:flex;flex-direction:column;align-items:center;gap:0px;line-height:1">${shapeSvgInner}${dotsSvg}</div>`;
    }

    return svgShape(parsed.shapeName, fill, sizeVal, stroke);
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
            const svgContent = renderCellSVG(parsed);
            cells.push(`<div class="matrix-cell ${parsed.sizeCls || ''}">${svgContent}</div>`);
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

  function renderQuestions(container, questions, lang, timedMode, countdownSeconds) {
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

      // Visual matrix rendering in results too
      const isMatrix = (q.tags || []).includes('matrizen');
      let displayText = qText.replace(/\n/g, '<br>');
      if (isMatrix) {
        const gridHtml = renderMatrixGrid(qText);
        if (gridHtml) displayText = gridHtml;
      }

      return `
        <div class="quiz-question" id="qe-res-${qi}">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem">
            <span class="badge badge-info">Frage ${qi + 1}</span>
            <span class="stat-value" style="font-size:1rem" class="${qHeaderClass}">${qScore.toFixed(2)} / 1.00 Pkt</span>
          </div>
          <div class="quiz-question-text">${displayText}</div>
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
    let selectedTag = 'all';
    let activeQuestions = [];
    let timedMode = (quizId === 'all'); // default on for full mock exam
    let countdownSeconds = 600; // calculated per quiz: 1 min per question

    function buildActiveQuestions() {
      let pool = [...questions];
      // Filter by difficulty
      if (selectedDiff !== 'mixed') {
        pool = pool.filter(q => (q.difficulty || 'medium') === selectedDiff);
      }
      // Filter by cognitive sub-type tag
      if (selectedTag !== 'all') {
        pool = pool.filter(q => (q.tags || []).includes(selectedTag));
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
      selectedTag = 'all';
      renderStartScreen(container, questions, quizId, timedMode);

      wireOptButtons('qe-count-select', 'count', 10, v => { selectedCount = v; });
      wireOptButtons('qe-diff-select', 'diff', 'mixed', v => { selectedDiff = v; });
      wireOptButtons('qe-tag-select', 'tag', 'all', v => { selectedTag = v; });

      // Wire timed mode button
      const timedToggle = container.querySelector('#qe-timed-toggle');
      const timedBtn = container.querySelector('#qe-timed-btn');
      if (timedBtn && timedToggle) {
        timedBtn.addEventListener('click', () => {
          timedToggle.checked = !timedToggle.checked;
          timedMode = timedToggle.checked;
          if (timedMode) {
            timedBtn.style.background = 'var(--tu-blue)';
            timedBtn.style.color = '#fff';
            timedBtn.style.borderColor = 'var(--tu-blue)';
          } else {
            timedBtn.style.background = 'transparent';
            timedBtn.style.color = 'var(--tu-text-muted)';
            timedBtn.style.borderColor = 'var(--tu-border)';
          }
        });
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
      renderQuestions(container, activeQuestions, lang, timedMode, countdownSeconds);
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
