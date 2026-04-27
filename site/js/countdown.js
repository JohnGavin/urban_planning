/**
 * Countdown timer to exam day: 10 July 2026
 * Updates every second when the page is visible.
 */

const ExamCountdown = (() => {
  // Exam date: 10 July 2026, assume 09:00 Vienna time (arrive 1h early = 08:00)
  const EXAM_DATE = new Date('2026-07-10T09:00:00+02:00');

  function getTimeRemaining() {
    const now = new Date();
    const diff = EXAM_DATE - now;
    if (diff <= 0) return { total: 0, days: 0, hours: 0, minutes: 0, seconds: 0, passed: true };
    return {
      total: diff,
      days: Math.floor(diff / (1000 * 60 * 60 * 24)),
      hours: Math.floor((diff / (1000 * 60 * 60)) % 24),
      minutes: Math.floor((diff / (1000 * 60)) % 60),
      seconds: Math.floor((diff / 1000) % 60),
      passed: false,
      weeks: Math.floor(diff / (1000 * 60 * 60 * 24 * 7))
    };
  }

  function render(containerId) {
    const el = document.getElementById(containerId);
    if (!el) return;

    function update() {
      const t = getTimeRemaining();
      if (t.passed) {
        el.innerHTML = '<div class="stat-card good"><div class="stat-value">Exam day has arrived!</div></div>';
        return;
      }
      el.innerHTML = `
        <div class="countdown-unit ${t.days < 14 ? 'urgent' : ''}">
          <div class="countdown-number">${t.days}</div>
          <div class="countdown-label">Days</div>
        </div>
        <div class="countdown-unit">
          <div class="countdown-number">${String(t.hours).padStart(2, '0')}</div>
          <div class="countdown-label">Hours</div>
        </div>
        <div class="countdown-unit">
          <div class="countdown-number">${String(t.minutes).padStart(2, '0')}</div>
          <div class="countdown-label">Minutes</div>
        </div>
        <div class="countdown-unit">
          <div class="countdown-number">${String(t.seconds).padStart(2, '0')}</div>
          <div class="countdown-label">Seconds</div>
        </div>
      `;
    }

    update();
    setInterval(update, 1000);
  }

  function getStudyWeeks() {
    const t = getTimeRemaining();
    return t.weeks;
  }

  return { getTimeRemaining, render, getStudyWeeks, EXAM_DATE };
})();
