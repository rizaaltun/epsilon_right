(() => {
  document.querySelectorAll('[data-news-carousel]').forEach(carousel => {
    const track = carousel.querySelector('.news-track');
    const prev = carousel.querySelector('[data-news-prev]');
    const next = carousel.querySelector('[data-news-next]');
    const update = () => {
      prev.disabled = track.scrollLeft <= 2;
      next.disabled = track.scrollLeft + track.clientWidth >= track.scrollWidth - 2;
    };
    const move = direction => {
      const card = track.querySelector('.news-card');
      const step = card.getBoundingClientRect().width + parseFloat(getComputedStyle(track).gap);
      track.scrollBy({left: direction * step, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'});
    };
    prev.addEventListener('click', () => move(-1));
    next.addEventListener('click', () => move(1));
    track.addEventListener('scroll', update, {passive:true});
    track.addEventListener('keydown', e => {
      if(e.target !== track || !['ArrowLeft','ArrowRight'].includes(e.key)) return;
      e.preventDefault(); move(e.key === 'ArrowRight' ? 1 : -1);
    });
    new ResizeObserver(update).observe(track);
    update();
  });
})();
