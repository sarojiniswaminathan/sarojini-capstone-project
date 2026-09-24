(function () {
  const sidebar = document.getElementById('sidebar');
  const toggle = document.getElementById('sidebar-toggle');
  if (!sidebar || !toggle) return;

  function setCollapsed(collapsed) {
    sidebar.classList.toggle('sidebar-collapsed', collapsed);
    toggle.setAttribute('aria-expanded', String(!collapsed));
  }

  toggle.addEventListener('click', () => {
    setCollapsed(!sidebar.classList.contains('sidebar-collapsed'));
  });

  document.addEventListener('keydown', (event) => {
    const isToggleShortcut = (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'b';
    if (!isToggleShortcut) return;
    event.preventDefault();
    setCollapsed(!sidebar.classList.contains('sidebar-collapsed'));
  });
})();
