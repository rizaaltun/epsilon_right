/* English samples on book pages: the catalogue reader (catalogue-reader-v3.js) for one
   or more previews per page. Sheets: the cover alone (image 001), a blank inside cover
   when the book opens on a single right-hand page (data-blank), the sample pages
   (images 002…), then a closing page. */
(() => {
  const roots=[...document.querySelectorAll('[data-sample-reader]')];
  if(!roots.length)return;
  const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
  let active=null;

  const setup=root=>{
    const book=root.querySelector('.reader-book');
    const status=root.querySelector('.reader-status');
    const previous=root.querySelector('[data-prev]');
    const next=root.querySelector('[data-next]');
    const cover=root.querySelector('.reader-cover-fallback');
    const magnifier=root.querySelector('.reader-magnifier');
    const prefix=root.dataset.pages;
    const images=Number(root.dataset.count);
    // One entry per sheet: an image number, 0 for the blank inside cover, -1 for the closing page.
    const plan=[1,...(root.hasAttribute('data-blank')?[0]:[]),...Array.from({length:images-1},(_,i)=>i+2),-1];
    const count=plan.length;
    const imageOf=n=>plan[n]>0?plan[n]:0;
    const source=k=>prefix+String(k).padStart(3,'0')+'.webp';
    let flip,ready=false,coverReady=false,opened=false;
    const pages=[];
    const fit=()=>{
      if(!opened)return;
      const w=window.innerWidth,h=window.innerHeight,small=w<=640;
      root.style.width=w+'px';root.style.height=h+'px';
      book.style.width=Math.max(1,w-(small?24:96))+'px';
      book.style.height=Math.max(160,h-(small?34:38))+'px';
    };
    addEventListener('resize',fit);
    const preload=n=>{
      if(n<0||n>=count||!imageOf(n))return;
      const image=pages[n]?.querySelector('img');
      if(image&&!image.getAttribute('src')){image.src=source(imageOf(n));image.onerror=()=>{status.textContent='Page could not load. Refresh to try again.';};}
    };
    const nearby=n=>{for(let i=Math.max(0,n-2);i<Math.min(count,n+5);i++)preload(i);};
    const update=n=>{
      if(coverReady)nearby(n);previous.disabled=n===0;
      const portrait=flip.getOrientation()==='portrait';
      const end=portrait||n===0?n:Math.min(count-1,n+1);
      next.disabled=end>=count-1;
      status.textContent=(end===n?String(n+1):`${n+1}–${end+1}`)+' / '+count;
      root.setAttribute('aria-label',root.dataset.title+', '+status.textContent);
    };
    const move=direction=>{
      if(!opened||!ready||flip.getState()!=='read')return;
      const n=flip.getCurrentPageIndex();
      const step=flip.getOrientation()==='portrait'?1:2;
      const target=direction>0?n+step:Math.max(0,n-step);
      nearby(target);
      const shown=[pages[target]?.querySelector('img'),pages[Math.min(target+1,count-1)]?.querySelector('img')].filter(img=>img&&img.getAttribute('src'));
      Promise.all(shown.map(img=>img.decode().catch(()=>{}))).then(()=>{
        if(flip.getState()!=='read')return;
        if(direction>0&&!next.disabled)flip.flipNext('bottom');
        if(direction<0&&!previous.disabled)flip.flipPrev('bottom');
      });
    };
    const close=()=>{magnifier.hidden=true;opened=false;active=null;root.classList.remove('is-open');document.body.classList.remove('catalogue-reading');if(document.fullscreenElement===root)document.exitFullscreen().catch(()=>{});};
    previous.addEventListener('click',()=>move(-1));next.addEventListener('click',()=>move(1));
    root.querySelector('.reader-exit').addEventListener('click',close);
    const closeZoom=()=>{magnifier.hidden=true;magnifier.querySelector('img').removeAttribute('src');book.focus();};
    magnifier.querySelector('button').addEventListener('click',closeZoom);
    magnifier.addEventListener('dblclick',closeZoom);
    book.addEventListener('dblclick',event=>{
      if(!ready)return;
      const rect=book.getBoundingClientRect();
      let n=flip.getCurrentPageIndex();
      if(flip.getOrientation()==='landscape'&&n>0&&event.clientX>rect.left+rect.width/2)n=Math.min(count-1,n+1);
      if(!imageOf(n))return;
      magnifier.querySelector('img').src=source(imageOf(n));magnifier.hidden=false;magnifier.scrollTo(0,0);
    });
    const keys=event=>{
      if(event.key==='Escape'){if(!magnifier.hidden)closeZoom();else close();}
      if(!magnifier.hidden)return;
      if(event.key==='ArrowRight'){event.preventDefault();move(1);}
      if(event.key==='ArrowLeft'){event.preventDefault();move(-1);}
    };
    const sheet=(kind,content)=>{
      const page=document.createElement('div');page.className='reader-page '+kind;
      page.dataset.density=kind==='sample-cover'||kind==='sample-back'?'hard':'soft';
      if(content)page.appendChild(content);
      pages.push(page);book.appendChild(page);
    };
    const picture=label=>{const image=document.createElement('img');image.alt=label;image.decoding='async';return image;};
    const initialize=()=>{
      fit();
      if(flip){dispatchEvent(new Event('resize'));return;}
      try{
        const small=matchMedia('(max-width:640px)').matches;
        const ratio=Number(root.dataset.ratio);
        const height=Math.max(160,innerHeight-(small?34:38));
        const width=Math.min(height/ratio,(innerWidth-(small?24:96))/(small?1:2));
        flip=new St.PageFlip(book,{width:Math.floor(width),height:Math.floor(width*ratio),size:'stretch',
          minWidth:Math.min(320,Math.max(120,(innerWidth-24)*.8)),maxWidth:1800,minHeight:120,maxHeight:2500,usePortrait:true,
          autoSize:false,showCover:true,drawShadow:true,maxShadowOpacity:.65,
          flippingTime:reduced?1:850,mobileScrollSupport:false,swipeDistance:30,
          showPageCorners:!reduced,useMouseEvents:true,clickEventForward:true});
        const first=picture('Cover');first.src=source(1);first.fetchPriority='high';
        for(const k of plan){
          if(k===1)sheet('sample-cover',first);
          else if(k===0)sheet('sample-blank');
          else if(k>0)sheet('',picture('Sample page '+(k-1)));
          else sheet('sample-back',root.querySelector('template[data-end]').content.firstElementChild.cloneNode(true));
        }
        flip.on('init',()=>{ready=true;update(0);book.focus({preventScroll:true});});
        flip.on('flip',event=>update(event.data));
        flip.on('changeOrientation',()=>{if(ready)update(flip.getCurrentPageIndex());});
        flip.loadFromHTML(book.querySelectorAll('.reader-page'));
        first.decode().then(()=>{cover.hidden=true;coverReady=true;if('requestIdleCallback' in window)requestIdleCallback(()=>nearby(0),{timeout:1000});else setTimeout(()=>nearby(0),150);}).catch(()=>{status.textContent='Preparing the sample…';});
      }catch(error){console.error(error);status.textContent='The reader could not load. Refresh to try again.';}
    };
    const open=(fullscreen=true)=>{
      opened=true;active={keys,close,root};root.classList.add('is-open');document.body.classList.add('catalogue-reading');fit();
      // Some browsers leave the fullscreen request pending (a permission prompt); open in the window meanwhile.
      if(fullscreen&&root.requestFullscreen){root.requestFullscreen().catch(()=>{}).finally(initialize);setTimeout(()=>{if(opened&&!flip)initialize();},800);}else initialize();
    };
    document.querySelectorAll(`a[href="#${root.id}"]`).forEach(link=>link.addEventListener('click',event=>{event.preventDefault();open();}));
    if(location.hash==='#'+root.id)open(false);
  };

  roots.forEach(setup);
  addEventListener('keydown',event=>{if(active)active.keys(event);});
  document.addEventListener('fullscreenchange',()=>{
    if(!active)return;
    if(!document.fullscreenElement)active.close();else dispatchEvent(new Event('resize'));
  });
})();
