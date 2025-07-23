window.addEventListener('DOMContentLoaded', function() {
  document.body.classList.add('fade-in');
  const btn = document.getElementById('mobile-menu-button');
  const menu = document.getElementById('mobile-menu');
  if(btn && menu) btn.onclick = () => menu.classList.toggle('hidden');
  // Navbar background on scroll
  const navbar = document.getElementById('main-navbar');
  function handleNavBg() {
    if(window.scrollY > 10) {
      navbar.classList.add('bg-[#1E293B]');
    } else {
      navbar.classList.remove('bg-[#1E293B]');
    }
  }
  window.addEventListener('scroll', handleNavBg);
  handleNavBg();
  // Contact form feedback
  const form = document.getElementById('contactForm');
  const msg = document.getElementById('successMsg');
  if(form && msg) {
    form.onsubmit = function(e) {
      e.preventDefault();
      msg.classList.add('show');
      setTimeout(() => { msg.classList.remove('show'); form.reset(); }, 2500);
    };
  }
});
const scrollBtn = document.getElementById('scrollTopBtn');
window.addEventListener('scroll', function() {
  if(window.scrollY > 200) {
    scrollBtn.classList.add('show');
  } else {
    scrollBtn.classList.remove('show');
  }
});
scrollBtn.onclick = function() {
  window.scrollTo({ top: 0, behavior: 'smooth' });
}; 