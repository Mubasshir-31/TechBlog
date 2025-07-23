window.addEventListener('DOMContentLoaded', function() {
  document.body.classList.add('fade-in');
  const btn = document.getElementById('mobile-menu-button');
  const menu = document.getElementById('mobile-menu');
  if(btn && menu) btn.onclick = () => menu.classList.toggle('hidden');
  // Navbar background on scroll (transparent at top, .scrolled when scrolled)
  const navbar = document.getElementById('main-navbar');
  function handleNavBg() {
    if(window.scrollY > 10) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
  }
  window.addEventListener('scroll', handleNavBg);
  window.addEventListener('DOMContentLoaded', handleNavBg);
  // Contact form feedback for home page
  const form = document.getElementById('contactFormHome');
  const msg = document.getElementById('successMsgHome');
  if(form && msg) {
    form.onsubmit = function(e) {
      e.preventDefault();
      msg.classList.add('show');
      setTimeout(() => { msg.classList.remove('show'); form.reset(); }, 2500);
    };
  }
  // Scrollspy logic
  const links = document.querySelectorAll('.scrollspy-link');
  const sections = [
    document.getElementById('about-section'),
    document.getElementById('blog-section'),
    document.getElementById('contact-section')
  ];
  function onScroll() {
    let scrollPos = window.scrollY + 120;
    let activeIdx = 0;
    for(let i=0; i<sections.length; i++) {
      if(sections[i].offsetTop <= scrollPos) activeIdx = i;
    }
    links.forEach((l, i) => l.classList.toggle('bg-[#bae6fd]', i === activeIdx));
  }
  window.addEventListener('scroll', onScroll);
  onScroll();
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
// Mini contact form in footer
const footerForm = document.getElementById('footerContactForm');
const footerMsg = document.getElementById('footerContactMsg');
if(footerForm && footerMsg) {
  footerForm.onsubmit = function(e) {
    e.preventDefault();
    footerMsg.textContent = 'Thank you! Message sent.';
    footerMsg.classList.add('show');
    setTimeout(() => { footerMsg.classList.remove('show'); footerMsg.textContent = ''; footerForm.reset(); }, 2000);
  };
}
// Section fade-in on scroll
function fadeSections() {
  document.querySelectorAll('section').forEach(sec => {
    if(sec.classList.contains('section-fade')) {
      const rect = sec.getBoundingClientRect();
      if(rect.top < window.innerHeight - 60) {
        sec.classList.add('visible');
      }
    }
  });
}
window.addEventListener('scroll', fadeSections);
window.addEventListener('DOMContentLoaded', fadeSections);
// Smooth scroll for scrollspy nav
const scrollLinks = document.querySelectorAll('.scrollspy-link');
scrollLinks.forEach(link => {
  link.addEventListener('click', function(e) {
    const href = this.getAttribute('href');
    if(href && href.startsWith('#')) {
      e.preventDefault();
      const target = document.querySelector(href);
      if(target) {
        window.scrollTo({ top: target.offsetTop - 70, behavior: 'smooth' });
      }
    }
  });
});
// Scrollspy nav background on scroll
const scrollspyNav = document.getElementById('scrollspy-nav');
function handleScrollspyNavBg() {
  if(window.scrollY > 10) {
    scrollspyNav.classList.add('scrolled');
  } else {
    scrollspyNav.classList.remove('scrolled');
  }
}
window.addEventListener('scroll', handleScrollspyNavBg);
window.addEventListener('DOMContentLoaded', handleScrollspyNavBg); 