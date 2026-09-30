/**
 * ExamParts — the ONE place that knows how quizzes map to the three exam parts
 * and how much each part counts (Reihungstest Raumplanung: A 40% / B 20% / C 40%).
 *
 * Everything else (quiz engine, dashboard, home page) asks this module; nothing
 * else may hard-code the quizId -> part mapping or the weights.
 *
 * 'coursework' is a page-level quiz mode (quiz-coursework.html = all of Teil A);
 * it is never the quizId of a question. 'all' is the mixed mock exam.
 */

const ExamParts = (() => {
  const PARTS = [
    { id: 'A', name_de: 'Teil A – Fachwissen', name_en: 'Part A – Subject knowledge', short_de: 'Teil A',
      weight: 0.4, link: 'quiz-coursework.html',
      quizIds: ['oerek-principles', 'oerek-megatrends', 'oerek-actions', 'studienplan'] },
    { id: 'B', name_de: 'Teil B – Textverständnis', name_en: 'Part B – Text comprehension', short_de: 'Teil B',
      weight: 0.2, link: 'quiz-text-comprehension.html',
      quizIds: ['text-comprehension'] },
    { id: 'C', name_de: 'Teil C – Kognitive Fähigkeiten', name_en: 'Part C – Cognitive abilities', short_de: 'Teil C',
      weight: 0.4, link: 'quiz-cognitive.html',
      quizIds: ['cognitive'] }
  ];

  // Page-level modes that cover exactly one part (their attempts are stored under the mode id).
  const PART_MODES = { coursework: 'A' };
  const MIXED_MODE = 'all';

  function parts() { return PARTS.slice(); }
  function getPart(id) { return PARTS.find(p => p.id === id) || null; }

  /** quizId (question topic or part-mode id) -> 'A'|'B'|'C', or null (mixed mode / unknown). */
  function partOf(quizId) {
    if (Object.prototype.hasOwnProperty.call(PART_MODES, quizId)) return PART_MODES[quizId];
    const p = PARTS.find(pt => pt.quizIds.includes(quizId));
    return p ? p.id : null;
  }

  function isPartMode(quizId) { return Object.prototype.hasOwnProperty.call(PART_MODES, quizId); }
  function isMixedMode(quizId) { return quizId === MIXED_MODE; }

  // ── Balanced sample ──────────────────────────────────────────────────────

  const EPS = 1e-9;

  /** Largest-remainder apportionment of `total` over the part weights. */
  function apportion(total) {
    const exact = PARTS.map(p => total * p.weight);
    const counts = exact.map(Math.floor);
    let left = total - counts.reduce((a, b) => a + b, 0);
    const order = exact.map((x, i) => ({ i, r: x - Math.floor(x) }))
      .sort((a, b) => (b.r - a.r) || (a.i - b.i));
    for (let k = 0; left > 0; k = (k + 1) % order.length, left--) counts[order[k].i]++;
    const out = {};
    PARTS.forEach((p, i) => { out[p.id] = counts[i]; });
    return out;
  }

  function isExactRatio(total) {
    return PARTS.every(p => Math.abs(total * p.weight - Math.round(total * p.weight)) < EPS);
  }

  /**
   * Plan how many questions per part.
   * @param total  number of questions wanted, or 'all' (= largest total with the exact ratio)
   * @param avail  {A:n, B:n, C:n} questions available per part (after filters)
   * @returns {counts:{A,B,C}, total, shortages:[{part, wanted, got}]}
   */
  function plan(total, avail) {
    let counts;
    if (total === 'all') {
      const cap = PARTS.reduce((s, p) => s + (avail[p.id] || 0), 0);
      let n = cap;
      for (; n > 0; n--) {
        if (!isExactRatio(n)) continue;
        const c = apportion(n);
        if (PARTS.every(p => c[p.id] <= (avail[p.id] || 0))) break;
      }
      counts = apportion(Math.max(0, n));
    } else {
      counts = apportion(total);
    }
    const shortages = [];
    const out = {};
    PARTS.forEach(p => {
      const have = avail[p.id] || 0;
      if (counts[p.id] > have) shortages.push({ part: p.id, wanted: counts[p.id], got: have });
      out[p.id] = Math.min(counts[p.id], have);
    });
    return { counts: out, total: PARTS.reduce((s, p) => s + out[p.id], 0), shortages };
  }

  function shuffle(arr, rng) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor((rng || Math.random)() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  function availableByPart(questions) {
    const avail = {};
    PARTS.forEach(p => { avail[p.id] = 0; });
    questions.forEach(q => { const p = partOf(q.quizId); if (p) avail[p]++; });
    return avail;
  }

  /**
   * Balanced, shuffled sample of `questions` (each has .quizId) following the part weights.
   * @returns {questions:[...], plan:{counts,total,shortages}}
   */
  function sample(questions, total, rng) {
    const pl = plan(total, availableByPart(questions));
    let picked = [];
    PARTS.forEach(p => {
      const pool = shuffle(questions.filter(q => partOf(q.quizId) === p.id), rng);
      picked = picked.concat(pool.slice(0, pl.counts[p.id]));
    });
    return { questions: shuffle(picked, rng), plan: pl };
  }

  // ── Scores by part ───────────────────────────────────────────────────────

  /**
   * Weighted exam estimate in % from {A:pct, B:pct, C:pct}; parts with no value are left out
   * and the remaining weights are normalised. Returns null if no part has a value.
   */
  function weightedEstimate(pctByPart) {
    let sum = 0, wsum = 0;
    PARTS.forEach(p => {
      const v = pctByPart[p.id];
      if (typeof v === 'number' && !isNaN(v)) { sum += p.weight * v; wsum += p.weight; }
    });
    return wsum > 0 ? sum / wsum : null;
  }

  /**
   * Group attempts by exam part.
   * Single-part attempts count for partOf(quizId); mixed attempts contribute their stored
   * byPart {A:{score,total},...}. Mixed attempts without byPart are skipped.
   * @param byQuiz {quizId: [attempt, ...]} as returned by StudentDB/SupabaseSync getStats()
   * @returns {A:{n, avg, last, pcts}, B:{...}, C:{...}}  (avg/last null when n = 0)
   */
  function aggregate(byQuiz) {
    const rows = {};
    PARTS.forEach(p => { rows[p.id] = []; });
    Object.entries(byQuiz || {}).forEach(([qid, attempts]) => {
      attempts.forEach(a => {
        if (a.byPart) {
          PARTS.forEach(p => {
            const b = a.byPart[p.id];
            if (b && b.total > 0) rows[p.id].push({ date: a.date, pct: 100 * b.score / b.total });
          });
        } else {
          const pid = partOf(qid);
          if (pid) rows[pid].push({ date: a.date, pct: a.percentage });
        }
      });
    });
    const out = {};
    PARTS.forEach(p => {
      const r = rows[p.id].sort((x, y) => new Date(x.date) - new Date(y.date));
      out[p.id] = {
        n: r.length,
        avg: r.length ? r.reduce((s, x) => s + x.pct, 0) / r.length : null,
        last: r.length ? r[r.length - 1].pct : null,
        pcts: r.map(x => x.pct)
      };
    });
    return out;
  }

  return { parts, getPart, partOf, isPartMode, isMixedMode, plan, sample, availableByPart,
           weightedEstimate, aggregate, MIXED_MODE };
})();
