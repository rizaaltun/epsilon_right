import {RETAILERS} from './retailers.mjs';
import {normalizeTurkish, searchBooks, score, detectMarket} from './search.mjs';
import {REGIONS,countryName,chooseMarket,isMarket,primaryRetailers,scopedRetailers,marketLabel,regionFor} from './market.mjs';
const $ = id => document.getElementById(id);
const escape = value => String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const base = new URL('.',import.meta.url);
const config = {advisorEndpoint: '', ...window.EPSILON_CATALOG_CONFIG};
let books = [], tab = 'books', limit = 24;
const countries = [...new Map(RETAILERS.map(r=>[r.countryCode,{code:r.countryCode,name:new Intl.DisplayNames(['en'],{type:'region'}).of(r.countryCode==='UK'?'GB':r.countryCode),flag:r.flag}])).values()].sort((a,b)=>a.name.localeCompare(b.name));
const params = new URLSearchParams(location.search);
let savedMarket;try{savedMarket=localStorage.getItem('epsilon.catalog.destination.v2');}catch{}
let deviceMarket='ALL';try{deviceMarket=detectMarket(Intl.DateTimeFormat().resolvedOptions().timeZone,navigator.language);}catch{}
let destination=chooseMarket({shared:params.get('market'),saved:savedMarket,device:deviceMarket});
let market=destination.market,geoData=null,manualRevision=0,filtersOpen=false;
const stores=()=>primaryRetailers(RETAILERS,market);
const scope=()=>scopedRetailers(RETAILERS,market);
const destinationName=()=>marketLabel(destination);
const link = (r,q,primary=false) => `<a class="ic-store-link${primary?' primary':''}" href="${escape(r.buildUrl(q))}" target="_blank" rel="noopener noreferrer" aria-label="Search ${escape(r.name)} for ${escape(q)} (opens a new tab)">${escape(r.name)} <span aria-hidden="true">↗</span></a>`;
const palette=['#123b31','#ad6d45','#424e64','#877444','#6b4142','#345e59'];
function cover(book){
 if(book.cover) return `<div class="ic-cover has-image"><img src="${new URL('../../'+book.cover,base)}" alt="${escape(book.title)} cover" loading="lazy" width="320" height="480"></div>`;
 const color=palette[Number(book.isbn.slice(-2))%palette.length];
 return `<div class="ic-cover" style="background:${color}" aria-label="${escape(book.title)} — typographic placeholder"><small>${escape(book.brand)}</small><strong lang="tr">${escape(book.title)}</strong><small>${escape(book.author)}</small><span class="ic-cover-label">Turkish edition · Cover unavailable</span></div>`;
}
function card(book){
 const primary=stores();
 return `<article class="ic-card"><div class="ic-card-cover">${cover(book)}</div><div class="ic-meta"><span>${escape(book.brand)}</span></div><h3 lang="tr">${escape(book.title)}</h3><button class="ic-author" data-author="${escape(book.author)}">${escape(book.author)}</button><div class="ic-stores">${primary.slice(0,3).map((r,i)=>link(r,book.isbn,i===0)).join('')}</div><div class="ic-card-actions"><button data-detail="${book.isbn}" class="${primary.length?'':'ic-find-store'}">${primary.length?'More destinations →':market==='ALL'?'Find a bookshop →':'Bookshops in '+escape(destinationName())+' →'}</button>${config.advisorEndpoint?`<button data-analysis="${book.isbn}">About this book · AI</button>`:''}</div></article>`;
}
function filtered(){
 return searchBooks(books,$('search').value).filter(({book:b})=>(!$('brand').value||b.brand===$('brand').value)&&(!$('author').value||b.author===$('author').value)&&(!$('origin').value||b.turkish===($('origin').value==='tr'))).sort((a,b)=> {
 if($('search').value && a.score!==b.score) return b.score-a.score;
 if($('sort').value==='collection')return Number(Boolean(b.book.cover))-Number(Boolean(a.book.cover)) || books.indexOf(a.book)-books.indexOf(b.book);
 return a.book[$('sort').value].localeCompare(b.book[$('sort').value],'tr');
 });
}
function directory(type){
 const groups=type==='authors' ? [...new Set(books.map(b=>b.author))] : [...new Set(books.map(b=>b.brand))];
 const found = new Set(filtered().map(r=>r.book[type==='authors'?'author':'brand']));
 return '<div class="ic-directory">'+groups.filter(g=>found.has(g)).sort((a,b)=>a.localeCompare(b,'tr')).map(g=>{
 const set=books.filter(b=>b[type==='authors'?'author':'brand']===g);
 return `<article><p class="eyebrow">${type==='authors'?'Author / contributor credit':'Publishing family'}</p><h3>${escape(g)}</h3><p>${set.length} ${set.length===1?'book':'books'} in the collection</p><button class="ic-text-button" data-${type==='authors'?'author':'brand'}="${escape(g)}">View books →</button><div class="ic-stores">${stores().map(r=>link(r,g)).join('')}</div><details><summary>Search all ${RETAILERS.length} bookshops</summary><div class="ic-stores">${RETAILERS.map(r=>link(r,g)).join('')}</div></details></article>`;
 }).join('')+'</div>';
}
function retailerDirectory(){
 const selected = scope();
 const q=$('search').value.trim();
 const list=selected.filter(r=>!q||normalizeTurkish(`${r.name} ${r.countryName} ${countries.find(c=>c.code===r.countryCode).name}`).includes(normalizeTurkish(q)));
 return `<p class="ic-directory-intro">${market==='ALL'?'Explore the international network. Choose a destination to narrow the list.':'Bookshops for '+escape(destinationName())+'. Search a book in the Books tab to open its ISBN at these stores.'}</p><div class="ic-directory">${list.map(r=>`<article><p class="eyebrow">${r.flag} ${escape(countries.find(c=>c.code===r.countryCode).name)}</p><h3>${escape(r.name)}</h3><p>${escape(regionFor(r.countryCode)?.name||'International')}</p>${link(r,'Turkish books')}</article>`).join('')}</div>`;

}
function syncURL(){
 const next=new URLSearchParams();for(const id of ['search','brand','author','origin','sort']) if($(id).value && !(id==='sort'&&$(id).value==='collection'))next.set(id,$(id).value);
 if(['manual','shared','saved'].includes(destination.source))next.set('market',market);if(tab!=='books')next.set('view',tab);
 history.replaceState(null,'',location.pathname+'?'+next.toString()+location.hash);
}
function render(){
 const matches=filtered();
 $('filters').hidden=tab==='stores'||!filtersOpen;
 $('filter-toggle').hidden=tab==='stores';
 $('filter-toggle').setAttribute('aria-expanded',String(filtersOpen));
 const active=['brand','author','origin'].filter(id=>$(id).value).length;$('active-filters').textContent=active?`(${active})`:'';
 $('fuzzy-note').hidden=tab==='stores'||!$('search').value||!matches.length||matches[0].score>=85;
 document.querySelectorAll('[data-tab]').forEach(b=>{if(b.dataset.tab===tab)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');});
 updateLocation();
 $('results-status').textContent=tab==='books'?`${matches.length} books · ${escape(destinationName())}`:tab==='stores'?`${scope().length} bookshops · ISBN search`:`${new Set(matches.map(r=>r.book[tab==='authors'?'author':'brand'])).size} ${tab==='authors'?'author / contributor credits':'publishers'}`;
 $('more').hidden=tab!=='books'||matches.length<=limit;
 $('results').innerHTML=tab==='stores'?retailerDirectory():!matches.length?'<div class="ic-empty"><h2>No matches this time.</h2><p>Try a shorter title or reset the filters.</p></div>':tab==='books'?`<div class="ic-grid">${matches.slice(0,limit).map(r=>card(r.book)).join('')}</div>`:directory(tab);
 syncURL();
}
function suggestions(){
 const q=$('search').value.trim(), box=$('suggestions');
 if(q.length<2){box.hidden=true;$('search').setAttribute('aria-expanded','false');return;}
 const authors=[...new Set(books.map(b=>b.author))].filter(a=>score(q,a)>0).sort((a,b)=>score(q,b)-score(q,a)).slice(0,3);
 const brands=[...new Set(books.map(b=>b.brand))].filter(a=>score(q,a)>0).sort((a,b)=>score(q,b)-score(q,a)).slice(0,3);
 const found=searchBooks(books,q).slice(0,5);
 box.innerHTML=(authors.length?'<h3>Authors</h3>'+authors.map(a=>`<button data-author="${escape(a)}">${escape(a)}</button>`).join(''):'')+(brands.length?'<h3>Publishers</h3>'+brands.map(a=>`<button data-brand="${escape(a)}">${escape(a)}</button>`).join(''):'')+(found.length?'<h3>Books</h3>'+found.map(({book:b})=>`<div class="ic-suggest-book"><button data-detail="${b.isbn}">${escape(b.title)}<small>${escape(b.author)}</small></button>${stores()[0]?link(stores()[0],b.isbn):''}</div>`).join(''):'');
 if(!found.length&&!authors.length&&!brands.length)box.textContent='No suggestions. Try a different spelling.';
 box.hidden=false;$('search').setAttribute('aria-expanded','true');
}
function hideSuggestions(){ $('suggestions').hidden=true;$('search').setAttribute('aria-expanded','false'); }
function countrySection(code,isbn){
 const c=countries.find(c=>c.code===code);if(!c)return '';
 return `<section><h3>${c.flag} ${escape(c.name)}</h3><div class="ic-stores">${RETAILERS.filter(r=>r.countryCode===code).map(r=>link(r,isbn)).join('')}</div></section>`;
}
function openDetail(isbn){
 const b=books.find(b=>b.isbn===isbn);if(!b)return;
 const primary=stores(),region=regionFor(market)||REGIONS.find(r=>r.id===market);
 const regional=countries.filter(c=>region?.countries.includes(c.code)&&c.code!==market);
 $('detail-body').innerHTML=`<h2 id="detail-title" lang="tr">${escape(b.title)}</h2><p>${escape(b.author)} · ${escape(b.brand)}</p><p class="ic-isbn">ISBN ${b.isbn} <button class="ic-text-button" data-copy="${b.isbn}">Copy ISBN</button><span id="copy-status" role="status"></span></p><section class="ic-local-stores"><p class="eyebrow">${primary.length?'Your destination':'Explore bookshops'}</p><h3>${escape(destinationName())}</h3>${primary.length?`<div class="ic-stores">${primary.map((r,i)=>link(r,b.isbn,i===0)).join('')}</div>`:`<p>Choose a country below to check this title with a bookshop.</p>`}</section><p class="ic-fine">This opens a retailer’s ISBN search, not a confirmed stock listing. Check the Turkish edition, price and delivery at the bookshop.</p>${regional.length?`<h3 class="ic-detail-region">Other bookshops in ${escape(region.name)}</h3><div class="ic-country-list">${regional.map(c=>countrySection(c.code,b.isbn)).join('')}</div>`:''}<details class="ic-world-stores" ${market==='ALL'?'open':''}><summary>All ${countries.length} destinations · ${RETAILERS.length} bookshops</summary><div class="ic-country-list">${countries.map(c=>countrySection(c.code,b.isbn)).join('')}</div></details>`;
 hideSuggestions();$('detail').showModal();
}
function updateLocation(){
 $('location-label').textContent=destinationName();
 const unsupported=destination.country&&destination.country!==market&&!countries.some(c=>c.code===destination.country);
 $('market-note').textContent=unsupported?`No listed partner in ${countryName(destination.country)} yet. Explore ${REGIONS.find(r=>r.id===market)?.name||'other destinations'} and check delivery with the bookshop.`:destination.source==='network'?`Suggested from your connection. ${stores().length?`Local bookshops shown first.`:'Choose a country for local bookshops.'} You can change this anytime.`:destination.source==='device'?'Suggested from your device settings. Change it if you are shopping elsewhere.':['manual','saved','shared'].includes(destination.source)?`Your ${destination.source==='saved'?'saved ':''}shopping destination. ${stores().length?'Local bookshops shown first.':'Choose a country to narrow the bookshops.'}`:'We couldn’t suggest your country. Choose a destination to see local bookshops.';
}
function destinationOptions(){
 $('destination-options').innerHTML=REGIONS.map(r=>`<section class="ic-destination-region"><div><h3>${r.name}</h3><button data-market="${r.id}" aria-pressed="${market===r.id}">Explore region →</button></div><div class="ic-country-choices">${countries.filter(c=>r.countries.includes(c.code)).map(c=>`<button data-market="${c.code}" aria-pressed="${market===c.code}"><span>${c.flag} ${escape(c.name)}</span><small>${RETAILERS.filter(r=>r.countryCode===c.code).length} ${RETAILERS.filter(r=>r.countryCode===c.code).length===1?'bookshop':'bookshops'}${market===c.code?' · Selected':''}</small></button>`).join('')}</div></section>`).join('')+`<button data-market="ALL" class="ic-text-button">Explore all destinations →</button>`;
}
function selectMarket(value){
 if(!isMarket(value))return;manualRevision++;destination={market:value,source:'manual'};market=value;
 try{localStorage.setItem('epsilon.catalog.destination.v2',value);}catch{}
 $('destination').close();render();hideSuggestions();
}
async function locate(force=false){
 const revision=manualRevision;
 if(!force&&['saved','shared'].includes(destination.source))return;
 $('geo-status').textContent='Looking up your approximate country…';
 try{
  const response=await fetch(config.locationEndpoint||new URL('/api/location',location.origin),{cache:'no-store',signal:AbortSignal.timeout(2500)});
  if(!response.ok)throw Error();geoData=await response.json();
 }catch{geoData=null;}
 if(revision!==manualRevision)return;
 const selected=chooseMarket({geo:geoData,device:deviceMarket});
 if(force){manualRevision++;try{localStorage.removeItem('epsilon.catalog.destination.v2');}catch{}params.delete('market');}
 destination=selected;market=selected.market;render();destinationOptions();
 $('geo-status').textContent=selected.source==='network'?`Suggested destination: ${destinationName()}.`:selected.source==='device'?`Connection lookup unavailable. Suggested from device: ${destinationName()}.`:'Your country could not be suggested. Please choose below.';
 if(force&&selected.source!=='unknown')$('destination').close();
}
let aiController;
async function askAI(payload,output){
 if(!config.advisorEndpoint){output.textContent='The reading adviser is not enabled in this preview. Catalogue search and bookshop links are ready to use.';return;}
 if(aiController)aiController.abort();aiController=new AbortController();const controller=aiController;
 output.textContent='Preparing a reading suggestion…';
 const timer=setTimeout(()=>controller.abort(),25000);
 try{
 const response=await fetch(config.advisorEndpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),signal:controller.signal});
 if(!response.ok)throw Error(response.status===429?'The adviser is busy. Please try again shortly.':'The adviser is temporarily unavailable. Please use catalogue search.');
 const data=await response.json();if(aiController!==controller)return;output.replaceChildren();
 const text=document.createElement('p');text.className='ic-ai-text';text.textContent=data.text;output.append(text);
 for(const isbn of data.isbns||[]){const b=books.find(b=>b.isbn===isbn);if(!b)continue;const button=document.createElement('button');button.className='ic-text-button';button.dataset.detail=isbn;button.textContent=b.title+' →';output.append(button);}
 }catch(error){if(aiController!==controller)return;output.textContent=error.name==='AbortError'?'The request timed out or was cancelled. Please try again.':error.message;}finally{clearTimeout(timer);}
}
function showAdvisor(isbn){
 if($('detail').open)$('detail').close();
 $('advisor-response').textContent=config.advisorEndpoint?'':'The reading adviser is not enabled in this preview. You can use catalogue search to explore all 430 books.';
 if(!$('advisor').open)$('advisor').showModal();
 if(isbn){const b=books.find(b=>b.isbn===isbn);$('advisor-query').value=`Tell me about ${b.title} by ${b.author}`;askAI({mode:'analysis',isbn},$('advisor-response'));}
}
document.addEventListener('click',async event=>{
 const el=event.target.closest('button');if(!el)return;
 if(el.dataset.market)selectMarket(el.dataset.market);
 if(el.id==='location-open'){destinationOptions();$('destination').showModal();}
 if(el.id==='detect-again')locate(true);
 if(el.id==='filter-toggle'){filtersOpen=!filtersOpen;render();}
 if(el.dataset.close){$(el.dataset.close).close();if(aiController)aiController.abort();}
 if(el.dataset.tab){tab=el.dataset.tab;limit=24;hideSuggestions();render();}
 if(el.dataset.detail){if($('advisor').open)$('advisor').close();openDetail(el.dataset.detail);}
 if(el.dataset.analysis)showAdvisor(el.dataset.analysis);
 if(el.dataset.author||el.dataset.brand){const id=el.dataset.author?'author':'brand';$(id).value=el.dataset[id];$('search').value='';tab='books';limit=24;hideSuggestions();render();}
 if(el.dataset.copy){try{await navigator.clipboard.writeText(el.dataset.copy);$('copy-status').textContent='Copied';}catch{$('copy-status').textContent='Please select and copy the ISBN above.';}}
 if(el.id==='advisor-open')showAdvisor();
});
document.addEventListener('click',e=>{if(!e.target.closest('.ic-search-wrap'))hideSuggestions();});
$('search').addEventListener('keydown',e=>{if(e.key==='Escape'){e.preventDefault();hideSuggestions();}if(e.key==='ArrowDown'&&!$('suggestions').hidden){e.preventDefault();$('suggestions').querySelector('button,a')?.focus();}if(e.key==='Enter'){hideSuggestions();$('search').blur();}});
$('suggestions').addEventListener('keydown',e=>{if(e.key==='Escape'){hideSuggestions();$('search').focus();}if(['ArrowDown','ArrowUp'].includes(e.key)){e.preventDefault();const items=[...$('suggestions').querySelectorAll('button,a')];const i=items.indexOf(document.activeElement);items[(i+(e.key==='ArrowDown'?1:-1)+items.length)%items.length]?.focus();}});
$('search').addEventListener('input',()=>{limit=24;render();suggestions();});
$('search').addEventListener('focus',suggestions);
for(const id of ['brand','author','origin','sort'])$(id).addEventListener('change',()=>{limit=24;render();});
$('clear-search').addEventListener('click',()=>{$('search').value='';hideSuggestions();limit=24;render();$('search').focus();});
$('reset').addEventListener('click',()=>{for(const id of ['search','brand','author','origin'])$(id).value='';$('sort').value='collection';limit=24;render();hideSuggestions();});
$('more').addEventListener('click',()=>{limit+=24;render();});
$('advisor-form').addEventListener('submit',e=>{e.preventDefault();askAI({mode:'recommend',query:$('advisor-query').value},$('advisor-response'));});
$('advisor').addEventListener('close',()=>{if(aiController)aiController.abort();});
document.addEventListener('submit',e=>{if(e.target.id==='isbn-test'){e.preventDefault();$('test-links').innerHTML=scope().map(r=>link(r,$('test-isbn').value)).join('');}});
try{
 const response=await fetch(new URL('books.json',base));if(!response.ok)throw Error('Catalogue unavailable');books=await response.json();
 $('book-count').textContent=books.length;$('author-count').textContent=new Set(books.map(b=>b.author)).size;
 /* Removed summary stats from the primary shopping path. */
 const hero=['9786254143144','9786258690309','9786054054206'].map(isbn=>books.find(b=>b.isbn===isbn));$('hero-books').innerHTML=hero.map(b=>'<div>'+cover(b)+'</div>').join('');
 for(const id of ['brand','author'])$(id).insertAdjacentHTML('beforeend',[...new Set(books.map(b=>b[id]))].sort((a,b)=>a.localeCompare(b,'tr')).map(v=>`<option value="${escape(v)}">${escape(v)}</option>`).join(''));
 for(const id of ['search','brand','author','origin','sort'])if(params.has(id)&&($(id).tagName!=='SELECT'||[...$(id).options].some(o=>o.value===params.get(id))))$(id).value=params.get(id);
 if(['authors','brands','stores'].includes(params.get('view')))tab=params.get('view');
 filtersOpen=['brand','author','origin'].some(id=>$(id).value);$('advisor-open').hidden=!config.advisorEndpoint;render();locate();
}catch{$('results-status').textContent='The collection could not be loaded. Please refresh the page.';$('results').innerHTML='<p>Check your connection and try again.</p>';}
