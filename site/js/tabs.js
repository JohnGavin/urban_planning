/**
 * Simple tab switcher. Works with .tab-btn[data-tab] and .tab-content[data-tab].
 * Usage: add onclick="Tabs.show(event, 'tabId')" or call Tabs.init() for auto-wiring.
 */
const Tabs = (() => {
  function show(evt, tabId) {
    // Find the parent tab-container
    const container = evt ? evt.target.closest('.tab-container') : document.querySelector('.tab-container');
    if (!container) return;
    container.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    container.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    container.querySelector(`.tab-btn[data-tab="${tabId}"]`)?.classList.add('active');
    container.querySelector(`.tab-content[data-tab="${tabId}"]`)?.classList.add('active');
    if (evt) evt.target.classList.add('active');
  }

  function init() {
    document.querySelectorAll('.tab-btn[data-tab]').forEach(btn => {
      btn.addEventListener('click', (e) => show(e, btn.dataset.tab));
    });
  }

  return { show, init };
})();

document.addEventListener('DOMContentLoaded', Tabs.init);
