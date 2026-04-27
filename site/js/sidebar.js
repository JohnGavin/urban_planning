/**
 * Sidebar toggle — adds a hamburger button to show/hide the sidebar.
 * Auto-injects the toggle button into the page.
 */
document.addEventListener('DOMContentLoaded', () => {
  // Create toggle button
  const btn = document.createElement('button');
  btn.className = 'sidebar-toggle';
  btn.innerHTML = '&#9776;'; // hamburger icon
  btn.setAttribute('aria-label', 'Toggle sidebar');
  btn.title = 'Toggle sidebar';
  document.body.appendChild(btn);

  // Check saved preference
  const wrapper = document.querySelector('.page-wrapper');
  const saved = localStorage.getItem('sidebar-collapsed');
  if (saved === 'true') {
    wrapper.classList.add('sidebar-collapsed');
  }

  btn.addEventListener('click', () => {
    wrapper.classList.toggle('sidebar-collapsed');
    const isCollapsed = wrapper.classList.contains('sidebar-collapsed');
    localStorage.setItem('sidebar-collapsed', isCollapsed);
  });
});
