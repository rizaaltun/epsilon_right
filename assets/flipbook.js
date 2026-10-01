/* Only visible pages are rendered; original PDFs remain available to download. */
const CDN = 'https://cdn.jsdelivr.net/npm/pdfjs-dist@6.3.289/';
let library;
const loadLibrary = () => library ||= import(CDN + 'build/pdf.mjs').then(lib => {
  lib.GlobalWorkerOptions.workerSrc = CDN + 'build/pdf.worker.mjs';
  return lib;
});

class CatalogueReader {
  constructor(root) {
    this.root = root;
    this.book = root.querySelector('.reader-book');
    this.stage = root.querySelector('.reader-stage');
    this.status = root.querySelector('.reader-status');
    this.input = root.querySelector('input');
    this.prev = root.querySelector('[data-prev]');
    this.next = root.querySelector('[data-next]');
    this.page = 1;
    this.zoom = 1;
    this.busy = false;
    this.cache = new Map();
    this.small = matchMedia('(max-width: 640px)');
    this.reduced = matchMedia('(prefers-reduced-motion: reduce)');
    this.prev.addEventListener('click', () => this.move(-1));
    this.next.addEventListener('click', () => this.move(1));
    root.querySelector('[data-jump]').addEventListener('submit', e => {
      e.preventDefault();
      if (!this.pdf || !this.input.reportValidity()) return;
      this.show(Number(this.input.value));
    });
    root.querySelector('[data-zoom]').addEventListener('click', e => {
      if (!this.pdf || this.busy) return;
      this.zoom = this.zoom === 1 ? 1.65 : 1;
      this.stage.classList.toggle('zoomed', this.zoom !== 1);
      e.currentTarget.textContent = this.zoom === 1 ? 'Zoom in' : 'Fit pages';
      e.currentTarget.setAttribute('aria-pressed', String(this.zoom !== 1));
      this.show(this.page);
    });
    const fullscreen = root.querySelector('[data-fullscreen]');
    if (!root.requestFullscreen) fullscreen.hidden = true;
    fullscreen.addEventListener('click', async () => {
      try { if (document.fullscreenElement) await document.exitFullscreen(); else await root.requestFullscreen(); }
      catch { this.status.textContent = 'Full screen is unavailable. You can still zoom in.'; }
    });
    root.addEventListener('keydown', e => {
      if (e.target.matches('input,a')) return;
      if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
        e.preventDefault(); this.move(e.key === 'ArrowRight' ? 1 : -1);
      }
    });
    let touch;
    this.stage.addEventListener('pointerdown', e => {
      if (e.pointerType === 'touch' && this.zoom === 1) touch = {x:e.clientX,y:e.clientY};
    });
    this.stage.addEventListener('pointerup', e => {
      if (!touch) return;
      const dx=e.clientX-touch.x, dy=e.clientY-touch.y; touch=null;
      if (Math.abs(dx)>55 && Math.abs(dx)>Math.abs(dy)*1.5) this.move(dx<0?1:-1);
    });
    this.stage.addEventListener('pointercancel', () => touch=null);
    let timer;
    this.resize = () => { clearTimeout(timer); timer=setTimeout(()=>this.pdf && !this.busy && this.show(this.page),160); };
    window.addEventListener('resize',this.resize);
    document.addEventListener('fullscreenchange',this.resize);
    this.small.addEventListener('change',this.resize);
    this.observer = new IntersectionObserver(entries => {
      if (entries.some(e=>e.isIntersecting)) { this.observer.disconnect(); this.load(); }
    }, {rootMargin:'200px'});
    this.observer.observe(root);
  }

  async load() {
    this.status.textContent = 'Loading catalogue…';
    try {
      const lib = await loadLibrary();
      this.pdf = await lib.getDocument({url:this.root.dataset.pdf,
        cMapUrl:CDN+'cmaps/',cMapPacked:true,standardFontDataUrl:CDN+'standard_fonts/',
        wasmUrl:CDN+'wasm/',isEvalSupported:false}).promise;
      this.input.max = this.pdf.numPages;
      this.root.querySelector('[data-total]').textContent = this.pdf.numPages;
      await this.show(1);
    } catch (error) {
      console.error('Catalogue reader:',error);
      this.status.textContent = 'The reader could not load. Use “Open PDF” or “Download PDF” above.';
    }
  }

  numbers(n) {
    if (this.small.matches || n===1) return [n];
    const left = n % 2 === 0 ? n : n-1;
    return left < this.pdf.numPages ? [left,left+1] : [left];
  }

  async canvas(n,width) {
    const key = n+':'+width;
    if (this.cache.has(key)) return this.cache.get(key);
    const page = await this.pdf.getPage(n);
    const initial = page.getViewport({scale:1});
    const viewport = page.getViewport({scale:width/initial.width*Math.min(devicePixelRatio||1,2)});
    const canvas=document.createElement('canvas');
    canvas.width=Math.ceil(viewport.width); canvas.height=Math.ceil(viewport.height);
    canvas.setAttribute('role','img'); canvas.setAttribute('aria-label','Catalogue page '+n);
    await page.render({canvasContext:canvas.getContext('2d'),viewport}).promise;
    this.cache.set(key,canvas);
    // Bound memory even in the 70-page catalogue.
    while(this.cache.size>6) this.cache.delete(this.cache.keys().next().value);
    return canvas;
  }

  async show(number,direction=0) {
    if (!this.pdf || this.busy) return;
    this.busy=true; this.prev.disabled=true; this.next.disabled=true;
    this.root.setAttribute('aria-busy','true');
    const numbers=this.numbers(Math.max(1,Math.min(this.pdf.numPages,number)));
    try {
      const first=await this.pdf.getPage(numbers[0]);
      const view=first.getViewport({scale:1});
      const ratio=view.height/view.width;
      const maxHeight=document.fullscreenElement===this.root?innerHeight*.68:Math.min(650,innerHeight*.61);
      const width=Math.floor(Math.max(110,Math.min((this.stage.clientWidth-40)/(this.small.matches?1:2),maxHeight/ratio))*this.zoom);
      const canvases=await Promise.all(numbers.map(n=>this.canvas(n,width)));
      const old=this.book.querySelector(direction>0?'.reader-sheet:last-child canvas':'.reader-sheet:first-child canvas');
      let turn;
      if (old && direction && !this.reduced.matches) {
        turn=document.createElement('div');turn.className='reader-turn '+(direction>0?'forward':'backward');
        const copy=document.createElement('canvas');copy.width=old.width;copy.height=old.height;
        copy.getContext('2d').drawImage(old,0,0);turn.appendChild(copy);
        turn.style.width=width+'px';turn.style.height=width*ratio+'px';turn.setAttribute('aria-hidden','true');
      }
      this.book.replaceChildren(); this.book.classList.toggle('spread',numbers.length===2);
      this.book.style.width=width*numbers.length+'px';this.book.style.maxWidth=this.zoom>1?'none':'100%';
      for (const canvas of canvases) {
        const sheet=document.createElement('div');sheet.className='reader-sheet';sheet.style.width=width+'px';sheet.style.height=width*ratio+'px';sheet.appendChild(canvas);this.book.appendChild(sheet);
      }
      this.page=numbers[0];this.input.value=this.page;
      this.status.textContent=(numbers.length===2?'Pages '+numbers.join('–'):'Page '+this.page)+' of '+this.pdf.numPages;
      if (turn) {
        this.book.appendChild(turn);
        await turn.animate([{transform:'rotateY(0deg)',filter:'brightness(1)'},{transform:'rotateY('+(direction>0?'-':'')+'170deg)',filter:'brightness(.75)'}],{duration:540,easing:'cubic-bezier(.35,.05,.2,1)',fill:'forwards'}).finished;
        turn.remove();
      }
    } catch(error) {
      console.error(error); this.status.textContent='This page could not load. Try again or open the PDF.';
    } finally {
      this.busy=false;this.root.setAttribute('aria-busy','false');
      this.prev.disabled=this.page===1;
      this.next.disabled=this.numbers(this.page).at(-1)>=this.pdf.numPages;
    }
  }

  move(direction) {
    if(!this.pdf || this.busy) return;
    const numbers=this.numbers(this.page);
    const next=direction>0?numbers.at(-1)+1:(this.small.matches?this.page-1:(this.page<=2?1:this.page-2));
    if(next>=1 && next<=this.pdf.numPages) this.show(next,direction);
  }
}

document.querySelectorAll('[data-catalogue-reader]').forEach(root=>new CatalogueReader(root));
