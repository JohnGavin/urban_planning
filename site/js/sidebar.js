/**
 * Sidebar: hamburger toggle + collapsible nav sections.
 * Sections default closed except the one containing the active link.
 * State persisted in localStorage.
 */
document.addEventListener('DOMContentLoaded', () => {
  // ── Hamburger toggle ──────────────────────────────────────────────────
  const btn = document.createElement('button');
  btn.className = 'sidebar-toggle';
  btn.innerHTML = '&#9776;';
  btn.setAttribute('aria-label', 'Toggle sidebar');
  btn.title = 'Toggle sidebar';
  document.body.appendChild(btn);

  const wrapper = document.querySelector('.page-wrapper');
  if (localStorage.getItem('sidebar-collapsed') === 'true') {
    wrapper.classList.add('sidebar-collapsed');
  }
  btn.addEventListener('click', () => {
    wrapper.classList.toggle('sidebar-collapsed');
    localStorage.setItem('sidebar-collapsed', wrapper.classList.contains('sidebar-collapsed'));
  });

  // ── Collapsible nav sections ──────────────────────────────────────────
  const sidebar = document.querySelector('.sidebar');
  if (!sidebar) return;

  // Group nav-links under their preceding nav-section
  const sections = sidebar.querySelectorAll('.nav-section');
  sections.forEach((section, idx) => {
    const title = section.querySelector('.nav-section-title');
    if (!title) return;

    // Collect all sibling .nav-link elements until the next .nav-section
    const links = [];
    let el = section.nextElementSibling;
    while (el && !el.classList.contains('nav-section')) {
      if (el.classList.contains('nav-link')) {
        links.push(el);
      }
      el = el.nextElementSibling;
    }

    if (links.length === 0) return;

    // Wrap links in a container div
    const container = document.createElement('div');
    container.className = 'nav-section-links';
    // Insert container after the section div
    section.after(container);
    links.forEach(link => container.appendChild(link));

    // Auto-open section containing the active link, or Dashboard (first section)
    const hasActive = container.querySelector('.nav-link.active');
    const sectionKey = 'nav-section-' + idx;
    const savedState = localStorage.getItem(sectionKey);

    let isOpen;
    if (savedState !== null) {
      isOpen = savedState === 'open';
    } else {
      // Default: open if contains active link or is first section (Dashboard)
      isOpen = hasActive || idx === 0;
    }

    if (isOpen) {
      title.classList.add('open');
      container.classList.add('open');
    }

    // Click handler
    title.addEventListener('click', () => {
      const nowOpen = !container.classList.contains('open');
      title.classList.toggle('open', nowOpen);
      container.classList.toggle('open', nowOpen);
      localStorage.setItem(sectionKey, nowOpen ? 'open' : 'closed');
    });
  });
});
