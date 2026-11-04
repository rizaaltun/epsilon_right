import test from 'node:test';
import assert from 'node:assert/strict';
import books from '../assets/international/books.json' with {type:'json'};
import {normalizeTurkish,searchBooks,detectMarket} from '../assets/international/search.mjs';
import {RETAILERS} from '../assets/international/retailers.mjs';
import {handle} from '../integration/catalog-advisor/worker.mjs';

test('catalogue preserves counts and unique valid ISBNs',()=>{
 assert.equal(books.length,430);assert.equal(new Set(books.map(b=>b.isbn)).size,430);
 assert.equal(new Set(books.map(b=>b.author)).size,178);assert.equal(new Set(books.map(b=>b.brand)).size,10);
 assert.equal(books.filter(b=>b.turkish).length,156);
 for(const b of books){assert.match(b.isbn,/^97[89]\d{10}$/);let sum=0;for(let i=0;i<12;i++)sum+=Number(b.isbn[i])*(i%2?3:1);assert.equal((10-sum%10)%10,Number(b.isbn[12]),b.isbn);}
});
test('Turkish normalization and misspellings find expected books',()=>{
 assert.equal(normalizeTurkish('İIı Şükrü GÖĞÜŞ çâ'),'iii sukru gogus ca');
 for(const [q,expected] of [['kurk mantlu','Kürk Mantolu'],['saftrik','Saftirik'],['ustun dokmen','Üstün Dökmen'],['nihn kaya','Nihan Kaya']]){
 assert.ok(searchBooks(books,q).slice(0,5).some(r=>(r.book.title+' '+r.book.author).includes(expected)),q);
 }
 assert.equal(searchBooks(books,'978-625-414-3144')[0].book.isbn,'9786254143144');
 assert.equal(searchBooks(books,'zzzzzzqqqqq').length,0);
});
test('routing avoids mapping all American time zones to the USA',()=>{
 assert.equal(detectMarket('Europe/Berlin','en'),'DE');assert.equal(detectMarket('America/New_York','en'),'US');
 assert.equal(detectMarket('America/Toronto','en-CA'),'ALL');assert.equal(detectMarket('Europe/Istanbul','tr-TR'),'ALL');
 assert.equal(detectMarket('','en-GB'),'UK');assert.equal(detectMarket('Australia/Sydney','en'),'AU');
});
test('19 encoded links across 14 countries',()=>{
 assert.equal(RETAILERS.length,19);assert.equal(new Set(RETAILERS.map(r=>r.countryCode)).size,14);
 for(const r of RETAILERS){assert.equal(new URL(r.buildUrl('Nihan Kaya & ö')).protocol,'https:');assert.ok(r.buildUrl('9786254143144').includes('9786254143144'));assert.ok(!r.buildUrl('Nihan Kaya & ö').includes(' '));}
});
const req=(body,origin='https://epsilonpublishinggroup.com')=>new Request('https://api.example/catalog-advisor',{method:'POST',headers:{Origin:origin,'Content-Type':'application/json'},body:JSON.stringify(body)});
const env={GEMINI_API_KEY:'test-only',GEMINI_MODEL:'test-model',AI_RATE_LIMITER:{limit:async()=>({success:true})}};
test('AI proxy rejects foreign origins, invalid requests and missing config',async()=>{
 assert.equal((await handle(req({},'https://other.example'),env)).status,403);
 assert.equal((await handle(req({}),{})).status,503);
 assert.equal((await handle(req({mode:'recommend',query:'a'.repeat(601)}),env)).status,400);
 assert.equal((await handle(req({mode:'analysis',isbn:'000'}),env)).status,400);
 assert.equal((await handle(req({mode:'recommend',query:'books'}),{...env,AI_RATE_LIMITER:{limit:async()=>({success:false})}})).status,429);
});
test('AI output allows only real catalogue ISBNs and handles failures',async()=>{
 const mock=async()=>new Response(JSON.stringify({candidates:[{content:{parts:[{text:JSON.stringify({text:'A reading suggestion',isbns:['invented','9786254143144','9786254143144']})}]}}]}));
 const result=await handle(req({mode:'recommend',query:'a novel'}),env,mock);assert.equal(result.status,200);assert.deepEqual((await result.json()).isbns,['9786254143144']);
 const fail=await handle(req({mode:'recommend',query:'a novel'}),env,async()=>new Response('',{status:503}));assert.equal(fail.status,502);
});

const {chooseMarket,primaryRetailers,scopedRetailers,marketLabel,marketFromGeo} = await import('../assets/international/market.mjs');
const {locationData,locationResponse} = await import('../integration/catalog-location/location.mjs');
test('Finland connection takes priority over language/timezone and ranks only Adlibris FI',()=>{
 const state=chooseMarket({geo:{country:'FI',continent:'EU'},device:'US'});
 assert.equal(state.market,'FI');assert.equal(marketLabel(state),'Europe · Finland');
 assert.deepEqual(primaryRetailers(RETAILERS,state.market).map(r=>r.id),['adlibris_fi']);
});
test('deliberate destination and shared links survive automatic detection',()=>{
 assert.equal(chooseMarket({saved:'DE',geo:{country:'FI'},device:'US'}).market,'DE');
 assert.equal(chooseMarket({shared:'EUROPE',saved:'DE',geo:{country:'FI'}}).market,'EUROPE');
 assert.equal(chooseMarket({shared:'INVALID',saved:'INVALID',geo:null,device:'FI'}).source,'device');
});
test('region browsing never presents another country as a local store',()=>{
 assert.equal(primaryRetailers(RETAILERS,'EUROPE').length,0);
 assert.ok(scopedRetailers(RETAILERS,'EUROPE').every(r=>!['US','AE','AU'].includes(r.countryCode)));
 assert.equal(marketFromGeo({country:'ES',continent:'EU'}).market,'EUROPE');
 assert.equal(marketLabel(marketFromGeo({country:'ES',continent:'EU'})),'Europe · Spain');
 assert.equal(marketFromGeo({country:'JP',continent:'AS'}).market,'ALL');
 assert.equal(marketFromGeo({country:'XX',continent:'EU'}),null);
});
test('location endpoint exposes coarse edge country only and cannot be overridden by visitor input',()=>{
 const request=new Request('https://example.test/api/location?country=US',{headers:{'CF-IPCountry':'US'}});
 Object.defineProperty(request,'cf',{value:{country:'FI',continent:'EU',city:'Helsinki',latitude:'60',longitude:'25'}});
 assert.deepEqual(locationData(request),{country:'FI',continent:'EU',source:'network'});
 assert.match(locationResponse(request).headers.get('Cache-Control'),/no-store/);
 const noEdge=new Request('https://example.test/api/location',{headers:{'CF-IPCountry':'FI'}});
 assert.equal(locationData(noEdge).country,null);
 assert.equal(locationResponse(new Request('https://example.test/api/location',{headers:{Origin:'https://untrusted.example'}})).status,403);
});
test('opt-in trusted country header supports Sites proxy without overriding direct edge metadata',()=>{
 const req=new Request('https://example.test/api/location',{headers:{'CF-IPCountry':'FI'}});
 assert.equal(locationData(req).country,null);
 assert.equal(locationData(req,{trustCloudflareHeader:true}).country,'FI');
 Object.defineProperty(req,'cf',{value:{country:'DE',continent:'EU'}});
 assert.equal(locationData(req,{trustCloudflareHeader:true}).country,'DE');
 assert.equal(marketFromGeo({country:'ES',continent:null}).market,'EUROPE');
 assert.equal(marketFromGeo({country:'JP',continent:null}).market,'ALL');
});
