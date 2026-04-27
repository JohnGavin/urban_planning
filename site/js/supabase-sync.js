/**
 * SupabaseSync — syncs quiz progress to Supabase for cross-device access.
 * Falls back gracefully if offline or Supabase unavailable.
 *
 * Student ID is generated once and stored in localStorage.
 * Supabase anon key is public by design (RLS controls access).
 */
const SupabaseSync = (() => {
  const SUPABASE_URL = 'https://twodkhckmtweyxnsnftd.supabase.co';
  const SUPABASE_KEY = 'sb_publishable_MBLHzg2bxnYR2eccFL0D0w_QA89q6Lx';
  const STUDENT_ID_KEY = 'raumplanung_student_id';

  function getStudentId() {
    let id = localStorage.getItem(STUDENT_ID_KEY);
    if (!id) {
      id = 'stu_' + crypto.randomUUID().slice(0, 12);
      localStorage.setItem(STUDENT_ID_KEY, id);
    }
    return id;
  }

  function headers() {
    return {
      'apikey': SUPABASE_KEY,
      'Authorization': 'Bearer ' + SUPABASE_KEY,
      'Content-Type': 'application/json',
      'Prefer': 'return=minimal'
    };
  }

  async function saveAttempt(attempt) {
    try {
      const resp = await fetch(SUPABASE_URL + '/rest/v1/quiz_attempts', {
        method: 'POST',
        headers: headers(),
        body: JSON.stringify({
          student_id: getStudentId(),
          quiz_id: attempt.quizId,
          score: attempt.score,
          total: attempt.total,
          percentage: attempt.percentage,
          duration_sec: attempt.durationSec || 0
        })
      });
      if (!resp.ok) {
        console.warn('Supabase sync failed:', resp.status, await resp.text());
        return false;
      }
      return true;
    } catch (e) {
      console.warn('Supabase sync offline:', e.message);
      return false;
    }
  }

  async function getAttempts(quizId) {
    try {
      const studentId = getStudentId();
      let url = SUPABASE_URL + '/rest/v1/quiz_attempts?student_id=eq.' + studentId + '&order=created_at.desc';
      if (quizId && quizId !== 'all') {
        url += '&quiz_id=eq.' + quizId;
      }
      const resp = await fetch(url, { headers: headers() });
      if (!resp.ok) return null;
      return await resp.json();
    } catch (e) {
      console.warn('Supabase fetch offline:', e.message);
      return null;
    }
  }

  async function getStats() {
    const attempts = await getAttempts();
    if (!attempts || attempts.length === 0) return null;

    const byQuiz = {};
    attempts.forEach(a => {
      if (!byQuiz[a.quiz_id]) byQuiz[a.quiz_id] = [];
      byQuiz[a.quiz_id].push({
        quizId: a.quiz_id,
        score: a.score,
        total: a.total,
        percentage: a.percentage,
        durationSec: a.duration_sec,
        date: a.created_at
      });
    });

    const totalAttempts = attempts.length;
    const avgScore = Math.round(attempts.reduce((s, a) => s + a.percentage, 0) / totalAttempts);
    const bestScore = Math.max(...attempts.map(a => a.percentage));
    const quizzesTaken = Object.keys(byQuiz).length;

    return { totalAttempts, avgScore, quizzesTaken, bestScore, byQuiz };
  }

  async function saveMistake(mistake) {
    try {
      const resp = await fetch(SUPABASE_URL + '/rest/v1/mistakes', {
        method: 'POST',
        headers: headers(),
        body: JSON.stringify({
          student_id: getStudentId(),
          question_id: mistake.questionId,
          tags: mistake.tags || [],
          note: mistake.note || ''
        })
      });
      return resp.ok;
    } catch (e) {
      console.warn('Supabase mistake sync offline:', e.message);
      return false;
    }
  }

  async function getMistakes() {
    try {
      const url = SUPABASE_URL + '/rest/v1/mistakes?student_id=eq.' + getStudentId() + '&order=created_at.desc';
      const resp = await fetch(url, { headers: headers() });
      if (!resp.ok) return null;
      return await resp.json();
    } catch (e) { return null; }
  }

  return { getStudentId, saveAttempt, getAttempts, getStats, saveMistake, getMistakes };
})();
