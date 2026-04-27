/**
 * StudentDB — IndexedDB wrapper for storing quiz scores and study progress.
 * Decision D002 in docs/DECISIONS.md
 *
 * Stores:
 *  - quizAttempts: { id, quizId, date, score, total, percentage, answers, durationSec }
 *  - studyLog:     { id, date, topic, durationMin, notes }
 */

const StudentDB = (() => {
  const DB_NAME = 'raumplanung_student';
  const DB_VERSION = 1;
  let db = null;

  function open() {
    return new Promise((resolve, reject) => {
      if (db) { resolve(db); return; }
      const req = indexedDB.open(DB_NAME, DB_VERSION);
      req.onupgradeneeded = (e) => {
        const d = e.target.result;
        if (!d.objectStoreNames.contains('quizAttempts')) {
          const store = d.createObjectStore('quizAttempts', { keyPath: 'id', autoIncrement: true });
          store.createIndex('quizId', 'quizId', { unique: false });
          store.createIndex('date', 'date', { unique: false });
        }
        if (!d.objectStoreNames.contains('studyLog')) {
          const store2 = d.createObjectStore('studyLog', { keyPath: 'id', autoIncrement: true });
          store2.createIndex('date', 'date', { unique: false });
          store2.createIndex('topic', 'topic', { unique: false });
        }
      };
      req.onsuccess = (e) => { db = e.target.result; resolve(db); };
      req.onerror = (e) => reject(e.target.error);
    });
  }

  async function addQuizAttempt(attempt) {
    const d = await open();
    return new Promise((resolve, reject) => {
      const tx = d.transaction('quizAttempts', 'readwrite');
      const store = tx.objectStore('quizAttempts');
      const req = store.add({
        ...attempt,
        date: attempt.date || new Date().toISOString()
      });
      req.onsuccess = () => resolve(req.result);
      req.onerror = (e) => reject(e.target.error);
    });
  }

  async function getQuizAttempts(quizId) {
    const d = await open();
    return new Promise((resolve, reject) => {
      const tx = d.transaction('quizAttempts', 'readonly');
      const store = tx.objectStore('quizAttempts');
      const results = [];
      let req;
      if (quizId) {
        const idx = store.index('quizId');
        req = idx.openCursor(IDBKeyRange.only(quizId));
      } else {
        req = store.openCursor();
      }
      req.onsuccess = (e) => {
        const cursor = e.target.result;
        if (cursor) { results.push(cursor.value); cursor.continue(); }
        else { resolve(results); }
      };
      req.onerror = (e) => reject(e.target.error);
    });
  }

  async function getAllAttempts() {
    return getQuizAttempts(null);
  }

  async function getStats() {
    const attempts = await getAllAttempts();
    if (attempts.length === 0) {
      return { totalAttempts: 0, avgScore: 0, quizzesTaken: 0, bestScore: 0, recentTrend: [] };
    }
    const byQuiz = {};
    attempts.forEach(a => {
      if (!byQuiz[a.quizId]) byQuiz[a.quizId] = [];
      byQuiz[a.quizId].push(a);
    });
    const totalAttempts = attempts.length;
    const avgScore = Math.round(attempts.reduce((s, a) => s + a.percentage, 0) / totalAttempts);
    const bestScore = Math.max(...attempts.map(a => a.percentage));
    const quizzesTaken = Object.keys(byQuiz).length;
    // Last 10 attempts for trend
    const sorted = attempts.sort((a, b) => new Date(a.date) - new Date(b.date));
    const recentTrend = sorted.slice(-10).map(a => ({ date: a.date, score: a.percentage, quiz: a.quizId }));
    return { totalAttempts, avgScore, quizzesTaken, bestScore, recentTrend, byQuiz };
  }

  async function addStudyLog(entry) {
    const d = await open();
    return new Promise((resolve, reject) => {
      const tx = d.transaction('studyLog', 'readwrite');
      const store = tx.objectStore('studyLog');
      const req = store.add({ ...entry, date: entry.date || new Date().toISOString() });
      req.onsuccess = () => resolve(req.result);
      req.onerror = (e) => reject(e.target.error);
    });
  }

  async function getStudyLog() {
    const d = await open();
    return new Promise((resolve, reject) => {
      const tx = d.transaction('studyLog', 'readonly');
      const req = tx.objectStore('studyLog').getAll();
      req.onsuccess = () => resolve(req.result);
      req.onerror = (e) => reject(e.target.error);
    });
  }

  async function clearAll() {
    const d = await open();
    return new Promise((resolve, reject) => {
      const tx = d.transaction(['quizAttempts', 'studyLog'], 'readwrite');
      tx.objectStore('quizAttempts').clear();
      tx.objectStore('studyLog').clear();
      tx.oncomplete = () => resolve();
      tx.onerror = (e) => reject(e.target.error);
    });
  }

  return { open, addQuizAttempt, getQuizAttempts, getAllAttempts, getStats, addStudyLog, getStudyLog, clearAll };
})();
