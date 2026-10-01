/* Same-origin page images: no PDF download, font parsing or third-party request. */
(() => {
  const root=document.querySelector('[data-catalogue-reader]');
  if(!root)return;
  const book=root.querySelector('.reader-book');
  const status=root.querySelector('.reader-status');
  const previous=root.querySelector('[data-prev]');
  const next=root.querySelector('[data-next]');
  const cover=root.querySelector('.reader-cover-fallback');
  const magnifier=root.querySelector('.reader-magnifier');
  const prefix=root.dataset.pages;
  const count=Number(root.dataset.count);
  const source=n=>prefix+String(n+1).padStart(3,'0')+'.webp';
  const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
  let flip,ready=false,coverReady=false;
  const pages=[];
  let opened=false;
  const preload=n=>{
    if(n<0||n>=count)return;
    const image=pages[n]?.querySelector('img');
    if(image&&!image.getAttribute('src')){image.src=source(n);image.onerror=()=>{status.textContent='Page could not load. Refresh to try again.';};}
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
    if(!ready||flip.getState()!=='read')return;
    const n=flip.getCurrentPageIndex();
    const target=direction>0?(n===0?1:n+(flip.getOrientation()==='portrait'?1:2)):Math.max(0,n-(flip.getOrientation()==='portrait'?1:2));
    nearby(target);
    // Prepare both sides before beginning the physical turn; keep current spread visible.
    const images=[pages[target]?.querySelector('img'),pages[Math.min(target+1,count-1)]?.querySelector('img')].filter(Boolean);
    Promise.all(images.map(img=>img.decode().catch(()=>{}))).then(()=>{
      if(flip.getState()!=='read')return;
      if(direction>0&&!next.disabled)flip.flipNext('bottom');
      if(direction<0&&!previous.disabled)flip.flipPrev('bottom');
    });
  };
  const close=()=>{opened=false;root.classList.remove('is-open');document.body.classList.remove('catalogue-reading');if(document.fullscreenElement===root)document.exitFullscreen().catch(()=>{});};
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
    magnifier.querySelector('img').src=source(n);magnifier.hidden=false;magnifier.scrollTo(0,0);
  });
  addEventListener('keydown',event=>{
    if(!opened)return;
    if(event.key==='Escape'){if(!magnifier.hidden)closeZoom();else close();}
    if(!magnifier.hidden)return;
    if(event.key==='ArrowRight'){event.preventDefault();move(1);}
    if(event.key==='ArrowLeft'){event.preventDefault();move(-1);}
  });
  const initialize=()=>{
  if(flip){dispatchEvent(new Event('resize'));return;}
  try{
    const small=matchMedia('(max-width:640px)').matches;
    const ratio=Number(root.dataset.ratio);
    const height=Math.max(160,innerHeight-(small?34:38));
    const width=Math.min(height/ratio,(innerWidth-(small?24:96))/(small?1:2));
    flip=new St.PageFlip(book,{width:Math.floor(width),height:Math.floor(width*ratio),size:'stretch',
      minWidth:Math.min(320,Math.max(120,(innerWidth-24)*.8)),maxWidth:1800,minHeight:120,maxHeight:2500,usePortrait:true,
      autoSize:false,showCover:false,drawShadow:true,maxShadowOpacity:.65,
      flippingTime:reduced?1:850,mobileScrollSupport:false,swipeDistance:30,
      showPageCorners:!reduced,useMouseEvents:true,clickEventForward:false});
    for(let n=0;n<count;n++){
      const sheet=document.createElement('div');sheet.className='reader-page';sheet.dataset.density='soft';
      const image=document.createElement('img');image.alt='Catalogue page '+(n+1);image.decoding='async';
      if(n===0){image.src=source(n);image.fetchPriority='high';}
      sheet.appendChild(image);pages.push(sheet);book.appendChild(sheet);
    }
    flip.on('init',()=>{ready=true;update(0);book.focus({preventScroll:true});});
    flip.on('flip',event=>update(event.data));
    flip.on('changeOrientation',()=>{if(ready)update(flip.getCurrentPageIndex());});
    flip.loadFromHTML(book.querySelectorAll('.reader-page'));
    book.querySelector('img').decode().then(()=>{cover.hidden=true;coverReady=true;if('requestIdleCallback' in window)requestIdleCallback(()=>nearby(0),{timeout:1000});else setTimeout(()=>nearby(0),150);}).catch(()=>{status.textContent='Preparing catalogue…';});
    // Corners can be dragged directly; future spreads have already been prefetched.
  }catch(error){console.error(error);status.textContent='The reader could not load. Refresh to try again.';}
  };
  const open=()=>{
    opened=true;root.classList.add('is-open');document.body.classList.add('catalogue-reading');
    if(root.requestFullscreen){root.requestFullscreen().catch(()=>{}).finally(initialize);}else initialize();
  };
  document.querySelectorAll('a[href="#catalogue-reader"]').forEach(link=>link.addEventListener('click',event=>{event.preventDefault();open();}));
  document.addEventListener('fullscreenchange',()=>{if(!document.fullscreenElement&&opened)close();});
  if(location.hash==='#catalogue-reader'){opened=true;root.classList.add('is-open');document.body.classList.add('catalogue-reading');initialize();}
})();
