'use strict';
// Declarations Of DOM elements:
const headerHTML = document.querySelector('.header');
const modal = document.querySelector('.modal');
const overlay = document.querySelector('.overlay');
const btnCloseModal = document.querySelector('.btn--close-modal');
const btnsOpenModal = document.querySelectorAll('.btn--show-modal');
// Learn More Button Scroll:
const btnScrollTo = document.querySelector('.btn--scroll-to');
const section1 = document.querySelector('#section--1');
// Smooth Scroll For All The Navigation Buttons:
const navLinkParent = document.querySelector('.nav__links');
// Tabbed Component:
const tabContainer = document.querySelector('.operations__tab-container');
const tabs = document.querySelectorAll('.operations__tab');
const tabsContent = document.querySelectorAll('.operations__content');
// Blur Effect On Nav Link:
const nav = document.querySelector('.nav');
// Reveal Sections:
const allSection = document.querySelectorAll('.section');
// Lazy Loading
const lazyImg = document.querySelectorAll('img[data-src]');
// Slider:
const slide = document.querySelectorAll('.slide');
const sliderBtnLeft = document.querySelector('.slider__btn--left');
const sliderBtnRight = document.querySelector('.slider__btn--right');
// Slider Dot:
const dotContainer = document.querySelector('.dots');
///////////////////////////////////////
// Modal window
const registerUrl = document.getElementById('url-container').getAttribute('data-register-url');
let modalState = false;
const openModal = function (e) {
  e.preventDefault();
  window.location.href = registerUrl;
  // modal.classList.remove('hidden');
  // overlay.classList.remove('hidden');
  // modalState = true;
};

const closeModal = function () {
  modal.classList.add('hidden');
  overlay.classList.add('hidden');
  modalState = false;
};

for (let i = 0; i < btnsOpenModal.length; i++)
  btnsOpenModal[i].addEventListener('click', openModal);

btnCloseModal.addEventListener('click', closeModal);
overlay.addEventListener('click', closeModal);

document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
    closeModal();
  }
});

// Cookie Message:
let cookieState = true;
const cookieMessage = document.createElement('div');
cookieMessage.classList.add('cookie-message');
cookieMessage.innerHTML =
  'We are eating cookies <button class="btn btn--close-cookie">Cool!</button>';
headerHTML.before(cookieMessage);

cookieMessage.addEventListener('click', function () {
  cookieMessage.remove();
  cookieState = false;
});

// Learn More Button Scroll:
btnScrollTo.addEventListener('click', function (e) {
  // Old Way Of Scrolling:
  // const s1coords = section1.getClientRects()[0];
  // window.scrollTo({
  //   top: s1coords.top + window.scrollY,
  //   left: s1coords.left + window.scrollX,
  //   behavior: 'smooth',
  // });
  // New Way Of Scrolling:
  section1.scrollIntoView({ behavior: 'smooth' });
});

// Smooth Scroll For All The Navigation Buttons:
// This will add Event Listener to each element which is not good
/*
document.querySelectorAll('.nav__link').forEach(function (ele) {
  ele.addEventListener('click', function (e) {
    e.preventDefault();
    const ID = this.getAttribute('href');
    document.querySelector(ID).scrollIntoView({ behavior: 'smooth' });
  });
});
*/
// We need to use Event Delegation. Meaning Add Event Listener to the parent. Then just check
// where the event occured using event.target.
navLinkParent.addEventListener('click', function (e) {
  if (
    e.target.classList.contains('nav__link') &&
    e.target.getAttribute('href') != '#'
  ) {
    e.preventDefault();
    const ID = e.target.getAttribute('href');
    document.querySelector(ID).scrollIntoView({ behavior: 'smooth' });
  }
});

// Tabbed Component:
tabContainer.addEventListener('click', function (e) {
  const clicked = e.target.closest('.operations__tab');
  if (!clicked) return;
  tabs.forEach(function (t) {
    t.classList.remove('operations__tab--active');
  });
  clicked.classList.add('operations__tab--active');
  // const index = Array.from(tabs).indexOf(clicked);
  const index = clicked.dataset.tab - 1;
  tabsContent.forEach(function (con) {
    con.classList.remove('operations__content--active');
  });
  tabsContent[index].classList.add('operations__content--active');
});

// Blur Effect On Nav Link:
const blurEffect = function (e) {
  if (e.target.classList.contains('nav__link')) {
    const hovered = e.target;
    const siblings = hovered.closest('.nav').querySelectorAll('.nav__link');
    const logo = hovered.closest('.nav').querySelector('img');
    siblings.forEach(sib => {
      if (sib != hovered) sib.style.opacity = this;
    });
    logo.style.opacity = this;
  }
};

nav.addEventListener('mouseover', blurEffect.bind(0.5));
nav.addEventListener('mouseout', blurEffect.bind(1));

// Sticky Navigation:
// The Old Way:
/*
window.addEventListener('scroll', function () {
  const s1coords = section1.getClientRects()[0].top + this.window.scrollY;
  if (this.window.scrollY >= s1coords) {
    cookieMessage.remove();
    nav.classList.add('sticky');
  } else {
    if (cookieState) headerHTML.before(cookieMessage);
    nav.classList.remove('sticky');
  }
});
*/
// New way. Use IntersectionObserverAPI
// const obsCallback = function (entries, observer) {
//   entries.forEach(entry => console.log(entry));
// };
// const obsOptions = {
//   root: null,
//   threshold: [0, 0.5],
// };
// const observer = new IntersectionObserver(obsCallback, obsOptions);
// observer.observe(section1);

const obsCallback = function (entries, observer) {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      if (cookieState) headerHTML.before(cookieMessage);
      nav.classList.remove('sticky');
    } else {
      cookieMessage.remove();
      nav.classList.add('sticky');
    }
  });
};
const navHeight = nav.getBoundingClientRect().height;
const obsOptions = {
  root: null,
  threshold: [0],
  rootMargin: `-${navHeight}px`,
};
const headerObserver = new IntersectionObserver(obsCallback, obsOptions);
headerObserver.observe(headerHTML);

// Reveal Sections:

const revealSection = function (entries, observer) {
  const [entry] = entries;
  if (!entry.isIntersecting) return;
  entry.target.classList.remove('section--hidden');
  observer.unobserve(entry.target);
};
const secObserve = new IntersectionObserver(revealSection, {
  root: null,
  threshold: 0.15,
});
allSection.forEach(function (sec) {
  sec.classList.add('section--hidden');
  secObserve.observe(sec);
});
// Lazy Loading

const loadImg = function (entries, observer) {
  const [entry] = entries;
  if (!entry.isIntersecting) return;
  entry.target.src = entry.target.dataset.src;
  entry.target.addEventListener('load', function () {
    entry.target.classList.remove('lazy-img');
  });
  observer.unobserve(entry.target);
};

const imgObserver = new IntersectionObserver(loadImg, {
  root: null,
  threshold: 0.15,
  rootMargin: '100px',
});

lazyImg.forEach(I => imgObserver.observe(I));

// Slider:
// Creating Dots:
const slider_container = function () {
  const createDots = function () {
    slide.forEach(function (_, i) {
      dotContainer.insertAdjacentHTML(
        'beforeend',
        `<button class=dots__dot data-slide=${i}></button>`
      );
    });
  };
  createDots();
  const doDots = document.querySelectorAll('.dots__dot');
  const deactivateDot = function () {
    doDots.forEach(dot => dot.classList.remove('dots__dot--active'));
  };
  const activateDot = dot => {
    deactivateDot();
    dot.classList.add('dots__dot--active');
  };
  doDots[0].classList.add('dots__dot--active');
  // Slide Movement:
  let currentSlide = 0;
  slide.forEach(function (s, i) {
    s.style.overflow = 'hidden';
  });

  const moveSlide = function (curSlide) {
    slide.forEach(function (s, i) {
      s.style.transform = `translateX(${(i - curSlide) * 100}%)`;
    });
    activateDot(doDots[curSlide]);
  };
  moveSlide(0);

  const nextSlide = function () {
    if (currentSlide === slide.length - 1) {
      currentSlide = 0;
    } else {
      currentSlide++;
    }
    moveSlide(currentSlide);
  };

  const preSlide = function () {
    if (currentSlide === 0) {
      currentSlide = slide.length - 1;
    } else {
      currentSlide--;
    }
    moveSlide(currentSlide);
  };

  sliderBtnRight.addEventListener('click', nextSlide);
  sliderBtnLeft.addEventListener('click', preSlide);
  document.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowRight' || e.key === 'd' || e.key === 'l') {
      nextSlide();
    }
    if (e.key === 'ArrowLeft' || e.key === 'a' || e.key === 'h') {
      preSlide();
    }
  });
  // Slider Dot:
  dotContainer.addEventListener('click', function (e) {
    if (e.target.classList.contains('dots__dot')) {
      const slideNumber = Number(e.target.dataset.slide);
      moveSlide(slideNumber);
      currentSlide = slideNumber;
    }
  });
};
slider_container();

// DOM Events Life Cycle:

document.addEventListener('DOMContentLoaded', function (e) {
  console.log('HTML parsed and HTML built!', e);
});

window.addEventListener('load', function (e) {
  console.log('Page Fully Loaded!', e);
});

// window.addEventListener('beforeunload',function(e){
//   e.preventDefault();
//   alert("unload event detected!")
// })

// VIM Binding:
const scrollSpeed = 400;
document.addEventListener('keydown', function (event) {
  if (modalState) return;
  switch (event.key) {
    case 'j': // Scroll down
      window.scrollBy({
        top: scrollSpeed, // Adjust the scroll distance to your preference
        left: 0,
        behavior: 'smooth',
      });
      break;

    case 'k': // Scroll up
      window.scrollBy({
        top: -scrollSpeed,
        left: 0,
        behavior: 'smooth',
      });
      break;

    case 'h': // Scroll left
      window.scrollBy({
        top: 0,
        left: -scrollSpeed,
        behavior: 'smooth',
      });
      break;

    case 'l': // Scroll right
      window.scrollBy({
        top: 0,
        left: scrollSpeed,
        behavior: 'smooth',
      });
      break;

    case 'g': // Scroll to top (gg in VIM)
      if (event.repeat) return; // Avoid triggering repeatedly
      if (event.key === 'g' && !event.ctrlKey) {
        window.scrollTo({
          top: 0,
          behavior: 'smooth',
        });
      }
      break;

    case 'G': // Scroll to bottom (G in VIM)
      window.scrollTo({
        top: document.body.scrollHeight,
        behavior: 'smooth',
      });
      break;

    default:
      break;
  }
});
