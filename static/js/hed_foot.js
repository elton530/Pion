document.addEventListener('DOMContentLoaded', () => {
  // ────────────────────────────────────────────────
  // 1. Mobile Menu
  // ────────────────────────────────────────────────
  const menuToggle    = document.querySelector('.menu-toggle');
  const menuClose     = document.querySelector('.menu-close');
  const mobileMenu    = document.getElementById('mobileMenu');
  const mobileOverlay = document.querySelector('.mobile-menu-overlay');

  const openMobileMenu = () => {
    mobileMenu.style.display = 'block';
    mobileOverlay.style.display = 'block';
    menuToggle.setAttribute('aria-expanded', 'true');
    setTimeout(() => {
      mobileMenu.setAttribute('aria-hidden', 'false');
      mobileMenu.querySelector('a, button')?.focus();
    }, 80);
  };

  const closeMobileMenu = () => {
    menuToggle.setAttribute('aria-expanded', 'false');
    mobileMenu.setAttribute('aria-hidden', 'true');
    setTimeout(() => {
      mobileMenu.style.display = 'none';
      mobileOverlay.style.display = 'none';
      menuToggle.focus();
    }, 320);
  };

  menuToggle?.addEventListener('click', openMobileMenu);
  menuClose?.addEventListener('click', closeMobileMenu);
  mobileOverlay?.addEventListener('click', closeMobileMenu);

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && mobileMenu?.getAttribute('aria-hidden') === 'false') {
      closeMobileMenu();
    }
  });

  // ────────────────────────────────────────────────
  // 2. User Dropdown
  // ────────────────────────────────────────────────
  const userToggle   = document.querySelector('.user-menu-toggle');
  const userDropdown = document.querySelector('.user-dropdown');

  if (userToggle && userDropdown) {
    const toggle = () => {
      const isOpen = userToggle.getAttribute('aria-expanded') === 'true';
      userToggle.setAttribute('aria-expanded', !isOpen);
      userDropdown.hidden = isOpen;

      if (!isOpen) {
        userDropdown.querySelector('a')?.focus();
      } else {
        userToggle.focus();
      }
    };

    userToggle.addEventListener('click', e => {
      e.stopPropagation();
      toggle();
    });

    document.addEventListener('click', e => {
      if (!userToggle.contains(e.target) && !userDropdown.contains(e.target)) {
        userToggle.setAttribute('aria-expanded', 'false');
        userDropdown.hidden = true;
      }
    });

    userDropdown.addEventListener('keydown', e => {
      if (e.key === 'Escape') toggle();
    });
  }

  // ────────────────────────────────────────────────
  // 3. Newsletter form (me validim bazë)
  // ────────────────────────────────────────────────
  document.getElementById('footerNewsletterForm')?.addEventListener('submit', e => {
    e.preventDefault();
    const input = e.target.querySelector('input[type="email"]');
    const email = input?.value.trim();

    if (!email) {
      alert('Shkruaj email-in tënd!');
      input?.focus();
      return;
    }
    if (!email.includes('@') || email.length < 6) {
      alert('Email jo i saktë – provo përsëri.');
      input?.focus();
      return;
    }

    alert(`Faleminderit! Regjistruam: ${email}`);
    input.value = '';
    input.focus();
  });

  // ────────────────────────────────────────────────
  // 4. Theme toggle + system preference
  // ────────────────────────────────────────────────
  const themeToggle = document.querySelector('#themeToggle');
  const html = document.documentElement;

  const setTheme = theme => {
    html.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    if (themeToggle) {
      themeToggle.setAttribute('aria-label', `Ndrysho në ${theme === 'dark' ? 'dritë' : 'errësirë'}`);
      themeToggle.innerHTML = theme === 'dark' 
        ? '<i class="fas fa-sun"></i>' 
        : '<i class="fas fa-moon"></i>';
    }
  };

  const saved = localStorage.getItem('theme');
  if (saved) {
    setTheme(saved);
  } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    setTheme('dark');
  } else {
    setTheme('light');
  }

  themeToggle?.addEventListener('click', () => {
    const current = html.getAttribute('data-theme') || 'light';
    setTheme(current === 'dark' ? 'light' : 'dark');
  });
});