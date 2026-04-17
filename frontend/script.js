// Initialize Lucide Icons
document.addEventListener('DOMContentLoaded', () => {
  lucide.createIcons();

  // Password Toggle Logic
  const togglePasswordBtn = document.getElementById('togglePasswordBtn');
  const passwordInput = document.getElementById('password');
  const eyeIcon = document.getElementById('eyeIcon');

  if (togglePasswordBtn && passwordInput && eyeIcon) {
    togglePasswordBtn.addEventListener('click', () => {
      const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
      passwordInput.setAttribute('type', type);
      
      // Update Lucide icon
      const newIcon = type === 'password' ? 'eye' : 'eye-off';
      eyeIcon.setAttribute('data-lucide', newIcon);
      lucide.createIcons();
    });
  }

  // Simulated Login Logic
  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    loginForm.addEventListener('submit', (e) => {
      e.preventDefault();
      
      const submitBtn = document.getElementById('submitBtn');
      const btnText = document.getElementById('btnText');
      const btnIcon = document.getElementById('btnIcon');
      const role = loginForm.getAttribute('data-role');
      
      // Save original styling/content
      const originalText = btnText.textContent;
      
      // Set loading state
      submitBtn.disabled = true;
      btnIcon.style.display = 'none';
      
      // Render spinner
      const spinnerDiv = document.createElement('div');
      spinnerDiv.className = 'spinner';
      spinnerDiv.style.marginRight = '8px';
      btnText.parentNode.insertBefore(spinnerDiv, btnText);
      
      btnText.textContent = 'Signing In...';

      // Simulate API call delay
      setTimeout(() => {
        // Reset state
        submitBtn.disabled = false;
        spinnerDiv.remove();
        btnText.textContent = originalText;
        btnIcon.style.display = 'inline-block';
        
        alert(role + ' Login Successful');
      }, 1500);
    });
  }
});
