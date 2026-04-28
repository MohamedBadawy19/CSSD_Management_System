// ============================================================
//  CSSD Management System — App Script (Frontend Branch)
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
  lucide.createIcons();

  // ── Password toggle ──────────────────────────────────────
  const togglePasswordBtn = document.getElementById('togglePasswordBtn');
  const passwordInput     = document.getElementById('password') || document.querySelector('input[type="password"]');
  const eyeIcon           = document.getElementById('eyeIcon');

  if (togglePasswordBtn && passwordInput && eyeIcon) {
    togglePasswordBtn.addEventListener('click', () => {
      const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
      passwordInput.setAttribute('type', type);
      eyeIcon.setAttribute('data-lucide', type === 'password' ? 'eye' : 'eye-off');
      lucide.createIcons();
    });
  }

  // ── Login form ───────────────────────────────────────────
  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    loginForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const submitBtn = document.getElementById('submitBtn');
      const btnText   = document.getElementById('btnText');
      const btnIcon   = document.getElementById('btnIcon');
      const role      = loginForm.getAttribute('data-role') || 'Staff';
      const originalText = btnText.textContent;

      submitBtn.disabled = true;
      if (btnIcon) btnIcon.style.display = 'none';

      const spinner = document.createElement('div');
      spinner.className = 'spinner';
      spinner.style.marginRight = '8px';
      btnText.parentNode.insertBefore(spinner, btnText);
      btnText.textContent = 'Signing In…';

      setTimeout(() => {
        spinner.remove();
        submitBtn.disabled = false;
        btnText.textContent = originalText;
        if (btnIcon) btnIcon.style.display = 'inline-block';

        // Route to dashboard based on role
        const dest = role === 'Nurse' ? '../pages/nurse-dashboard.html' : '../pages/cssd-dashboard.html';
        window.location.href = dest;
      }, 1200);
    });
  }

  // ── Live search on CSSD dashboard ───────────────────────
  const searchInput = document.querySelector('.search-input');
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      const q = searchInput.value.toLowerCase();
      document.querySelectorAll('.cssd-list-item').forEach(item => {
        item.style.display = item.textContent.toLowerCase().includes(q) ? '' : 'none';
      });
    });
  }

  // ── Status badge colours ─────────────────────────────────
  document.querySelectorAll('[data-status]').forEach(el => {
    el.classList.add('pill', `pill-outline-${el.dataset.status.toLowerCase()}`);
  });

  // ── Notification bell badge ──────────────────────────────
  if (typeof MOCK !== 'undefined') {
    const unread = MOCK.notifications.filter(n => !n.is_read).length;
    const badge  = document.getElementById('notif-badge');
    if (badge) badge.textContent = unread || '';
  }

  lucide.createIcons();
});

// ── Utility: format date string ──────────────────────────
function fmtDate(str) {
  const d = new Date(str);
  return isNaN(d) ? str : d.toLocaleString('en-GB', { dateStyle: 'short', timeStyle: 'short' });
}

// ── Utility: status pill class ───────────────────────────
function statusClass(s) {
  return { Requested:'orange', Collected:'blue', Cleaned:'blue',
           Sterilized:'indigo', Packed:'purple', Delivered:'green' }[s] || 'gray';
}
