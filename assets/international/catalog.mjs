import {RETAILERS} from './retailers.mjs';
import {normalizeTurkish, searchBooks, score, detectMarket} from './search.mjs';
const $ = id => document.getElementById(id);
const escape = value => String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const base = new URL('.',import.meta.url);
const config = {advisorEndpoint: '', ...window.EPSILON_CATALOG_CONFIG};
let books = [], tab = 'books', limit = 24;
const countries = [...new Map(RETAILERS.map(r=>[r.countryCode,{code:r.countryCode,name:new Intl.DisplayNames(['en'],{type:'region'}).of(r.countryCode==='UK'?'GB':r.countryCode),flag:r.flag}])).values()].sort((a,b)=>a.name.localeCompare(b.name));
let market = 'ALL';
try { market = localStorage.getItem('epsilon.catalog.market') || detectMarket(Intl.DateTimeFormat().resolvedOptions().timeZone,navigator.language); } catch {}
if (market !== 'ALL' && !countries.some(c=>c.code===market)) market='ALL';
const params = new URLSearchParams(location.search);
let restoreMarket = params.get('market');
if (restoreMarket==='ALL'||countries.some(c=>c.code===restoreMarket)) market=restoreMarket;
const stores = () => market==='ALL' ? [] : RETAILERS.filter(r=>r.countryCode===market);
const link = (r,q,primary=false) => `<a class="ic-store-link${primary?' primary':''}" href="${escape(r.buildUrl(q))}" target="_blank" rel="noopener noreferrer" aria-label="Search ${escape(r.name)} for ${escape(q)} (opens a new tab)">${escape(r.name)} <span aria-hidden="true">↗</span></a>`;
const palette=['#123b31','#ad6d45','#424e64','#877444','#6b4142','#345e59'];
function cover(book){
 if(book.cover) return `<div class="ic-cover has-image"><img src="${new URL('../../'+book.cover,base)}" alt="${escape(book.title)} cover" loading="lazy" width="320" height="480"></div>`;
 const color=palette[Number(book.isbn.slice(-2))%palette.length];
 return `<div class="ic-cover" style="background:${color}" aria-label="${escape(book.title)} — typographic placeholder"><small>${escape(book.brand)}</small><strong lang="tr">${escape(book.title)}</strong><small>${escape(book.author)}</small><span class="ic-cover-label">Turkish edition · Cover unavailable</span></div>`;
}
function card(book){return `<article class="ic-card"><div class="ic-card-cover">${cover(book)}</div><div class="ic-meta"><span>${escape(book.brand)}</span><span>${book.turkish?'Turkish author':'Translated author'}</span></div><h3 lang="tr">${escape(book.title)}</h3><button class="ic-author" data-author="${escape(book.author)}">${escape(book.author)}</button><p class="ic-isbn">ISBN ${book.isbn}</p><div class="ic-stores">${stores().slice(0,3).map((r,i)=>link(r,book.isbn,i===0)).join('')}</div><div class="ic-card-actions"><button data-detail="${book.isbn}">${market==='ALL'?'Find a bookshop':'All destinations'} · ${RETAILERS.length} stores ↗</button><button data-analysis="${book.isbn}">About this book · AI</button></div></article>`;}
function filtered(){
 return searchBooks(books,$('search').value).filter(({book:b})=>(!$('brand').value||b.brand===$('brand').value)&&(!$('author').value||b.author===$('author').value)&&(!$('origin').value||b.turkish===($('origin').value==='tr'))).sort((a,b)=> {
 if($('search').value && a.score!==b.score) return b.score-a.score;
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
 const selected = market==='ALL'?RETAILERS:stores();
 const q=$('search').value.trim();
 const list=selected.filter(r=>!q||normalizeTurkish(`${r.name} ${r.countryName} ${countries.find(c=>c.code===r.countryCode).name}`).includes(normalizeTurkish(q)));
 return `<form id="isbn-test" class="ic-test"><label for="test-isbn">Try an ISBN across these bookshops</label><input id="test-isbn" inputmode="numeric" placeholder="13-digit ISBN" value="9786254143144" required pattern="[0-9]{13}" maxlength="13"><button class="btn btn-secondary">Create search links</button><p class="ic-fine">Links open retailer search results. A search result does not confirm availability.</p><div id="test-links" class="ic-stores"></div></form><div class="ic-directory">${list.map(r=>`<article><p class="eyebrow">${r.flag} ${escape(countries.find(c=>c.code===r.countryCode).name)}</p><h3>${escape(r.name)}</h3><p>${escape(r.region)}</p>${link(r,'Turkish books')}</article>`).join('')}</div>`;
}
function syncURL(){
 const next=new URLSearchParams();for(const id of ['search','brand','author','origin','sort']) if($(id).value && !(id==='sort'&&$(id).value==='title'))next.set(id,$(id).value);
 next.set('market',market);if(tab!=='books')next.set('view',tab);
 history.replaceState(null,'',location.pathname+'?'+next.toString()+location.hash);
}
function render(){
 const matches=filtered();
 $('filters').hidden=tab==='stores';
 $('fuzzy-note').hidden=tab==='stores'||!$('search').value||!matches.length||matches[0].score>=85;
 document.querySelectorAll('[data-tab]').forEach(b=>{if(b.dataset.tab===tab)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');});
 $('market-note').textContent=market==='ALL'?'Choose a country for local bookshop links.':'Suggested from your device or saved choice. You can change it.';
 $('results-status').textContent=tab==='books'?`${matches.length} books · ${market==='ALL'?'All destinations':countries.find(c=>c.code===market).name}`:tab==='stores'?`${market==='ALL'?RETAILERS.length:stores().length} bookshops · ISBN search`:`${new Set(matches.map(r=>r.book[tab==='authors'?'author':'brand'])).size} ${tab==='authors'?'author / contributor credits':'publishers'}`;
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
function openDetail(isbn){
 const b=books.find(b=>b.isbn===isbn);if(!b)return;
 $('detail-body').innerHTML=`<h2 id="detail-title" lang="tr">${escape(b.title)}</h2><p>${escape(b.author)} · ${escape(b.brand)}</p><p class="ic-isbn">ISBN ${b.isbn} <button class="ic-text-button" data-copy="${b.isbn}">Copy ISBN</button><span id="copy-status" role="status"></span></p><p class="ic-fine">Turkish-language edition. Links open an ISBN search. Check format, stock, price and delivery with the bookshop.</p><div class="ic-country-list">${countries.map(c=>`<section><h3>${c.flag} ${escape(c.name)}</h3><div class="ic-stores">${RETAILERS.filter(r=>r.countryCode===c.code).map(r=>link(r,b.isbn)).join('')}</div></section>`).join('')}</div>`;
 hideSuggestions();$('detail').showModal();
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
 if(el.dataset.close){$(el.dataset.close).close();if(aiController)aiController.abort();}
 if(el.dataset.tab){tab=el.dataset.tab;limit=24;hideSuggestions();render();}
 if(el.dataset.detail){if($('advisor').open)$('advisor').close();openDetail(el.dataset.detail);}
 if(el.dataset.analysis)showAdvisor(el.dataset.analysis);
 if(el.dataset.author||el.dataset.brand){const id=el.dataset.author?'author':'brand';$(id).value=el.dataset[id];$('search').value='';tab='books';limit=24;hideSuggestions();render();}
 if(el.dataset.copy){try{await navigator.clipboard.writeText(el.dataset.copy);$('copy-status').textContent='Copied';}catch{$('copy-status').textContent='Please select and copy the ISBN above.';}}
 if(el.id==='advisor-open')showAdvisor();
});
document.addEventListener('click',e=>{if(!e.target.closest('.ic-search-wrap'))hideSuggestions();});
$('search').addEventListener('keydown',e=>{if(e.key==='Escape')hideSuggestions();if(e.key==='ArrowDown'&&!$('suggestions').hidden){e.preventDefault();$('suggestions').querySelector('button,a')?.focus();}if(e.key==='Enter'){hideSuggestions();$('search').blur();}});
$('suggestions').addEventListener('keydown',e=>{if(e.key==='Escape'){hideSuggestions();$('search').focus();}if(['ArrowDown','ArrowUp'].includes(e.key)){e.preventDefault();const items=[...$('suggestions').querySelectorAll('button,a')];const i=items.indexOf(document.activeElement);items[(i+(e.key==='ArrowDown'?1:-1)+items.length)%items.length]?.focus();}});
$('search').addEventListener('input',()=>{limit=24;render();suggestions();});
$('search').addEventListener('focus',suggestions);
for(const id of ['brand','author','origin','sort'])$(id).addEventListener('change',()=>{limit=24;render();});
$('market').innerHTML='<option value="ALL">All destinations</option>'+countries.map(c=>`<option value="${c.code}">${c.flag} ${escape(c.name)}</option>`).join('');$('market').value=market;
$('market').addEventListener('change',()=>{market=$('market').value;try{localStorage.setItem('epsilon.catalog.market',market);}catch{}render();hideSuggestions();});
$('clear-search').addEventListener('click',()=>{$('search').value='';hideSuggestions();limit=24;render();$('search').focus();});
$('reset').addEventListener('click',()=>{for(const id of ['search','brand','author','origin'])$(id).value='';$('sort').value='title';limit=24;render();hideSuggestions();});
$('more').addEventListener('click',()=>{limit+=24;render();});
$('advisor-form').addEventListener('submit',e=>{e.preventDefault();askAI({mode:'recommend',query:$('advisor-query').value},$('advisor-response'));});
$('advisor').addEventListener('close',()=>{if(aiController)aiController.abort();});
document.addEventListener('submit',e=>{if(e.target.id==='isbn-test'){e.preventDefault();$('test-links').innerHTML=(market==='ALL'?RETAILERS:stores()).map(r=>link(r,$('test-isbn').value)).join('');}});
try{
 const response=await fetch(new URL('books.json',base));if(!response.ok)throw Error('Catalogue unavailable');books=await response.json();
 $('book-count').textContent=books.length;$('author-count').textContent=new Set(books.map(b=>b.author)).size;
 $('facts').innerHTML=[[books.length,'Turkish-language books'],[new Set(books.map(b=>b.brand)).size,'publishers'],[countries.length,'destinations'],[RETAILERS.length,'bookshops']].map(([n,l])=>`<span><b>${n}</b>${l}</span>`).join('');
 const hero=['9786254143144','9786258690309','9786054054206'].map(isbn=>books.find(b=>b.isbn===isbn));$('hero-books').innerHTML=hero.map(b=>'<div>'+cover(b)+'</div>').join('');
 for(const id of ['brand','author'])$(id).insertAdjacentHTML('beforeend',[...new Set(books.map(b=>b[id]))].sort((a,b)=>a.localeCompare(b,'tr')).map(v=>`<option value="${escape(v)}">${escape(v)}</option>`).join(''));
 for(const id of ['search','brand','author','origin','sort'])if(params.has(id))$(id).value=params.get(id);
 if(['authors','brands','stores'].includes(params.get('view')))tab=params.get('view');render();
}catch{$('results-status').textContent='The collection could not be loaded. Please refresh the page.';$('results').innerHTML='<p>Check your connection and try again.</p>';}
