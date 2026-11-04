// Country is used for retailer ranking; region is used for navigation and fallback.
export const REGIONS = [
 {id:'EUROPE',name:'Europe',countries:['DE','UK','NL','BE','AT','CH','SE','FI','DK','NO','FR'],continent:'EU'},
 {id:'NORTH_AMERICA',name:'North America',countries:['US'],continent:'NA'},
 {id:'MIDDLE_EAST',name:'Middle East',countries:['AE'],continent:'AS'},
 {id:'OCEANIA',name:'Oceania',countries:['AU'],continent:'OC'},
];
export const countryName = code => {try{return new Intl.DisplayNames(['en'],{type:'region'}).of(code==='UK'?'GB':code);}catch{return code;}};
export const normalizeCountry = code => code==='GB'?'UK':/^[A-Z]{2}$/.test(code||'')&&!['XX','T1'].includes(code)?code:null;
export function regionFor(country,continent){return REGIONS.find(r=>r.countries.includes(country)) || REGIONS.find(r=>r.continent===continent&&continent!=='AS');}
export function isMarket(value){return value==='ALL'||REGIONS.some(r=>r.id===value||r.countries.includes(value));}
export function marketFromGeo(data){
 const country=normalizeCountry(data?.country), region=regionFor(country,data?.continent);
 if(!country)return null;
 return {market:REGIONS.some(r=>r.countries.includes(country))?country:region?.id||'ALL',country,source:'network'};
}
export function chooseMarket({shared,saved,geo,device}){
 if(isMarket(shared))return {market:shared,source:'shared'};
 if(isMarket(saved))return {market:saved,source:'saved'};
 const network=marketFromGeo(geo);if(network)return network;
 return isMarket(device)&&device!=='ALL'?{market:device,source:'device'}:{market:'ALL',source:'unknown'};
}
export function primaryRetailers(retailers,market){return REGIONS.some(r=>r.id===market)||market==='ALL'?[]:retailers.filter(r=>r.countryCode===market);}
export function scopedRetailers(retailers,market){
 if(market==='ALL')return retailers;
 const region=REGIONS.find(r=>r.id===market);return retailers.filter(r=>region?region.countries.includes(r.countryCode):r.countryCode===market);
}
export function marketLabel(state){
 const region=REGIONS.find(r=>r.id===state.market)||regionFor(state.market);
 if(state.country&&state.source==='network')return [region?.name,countryName(state.country)].filter(Boolean).join(' · ');
 return REGIONS.find(r=>r.id===state.market)?.name || (state.market==='ALL'?'All destinations':`${region?.name?region.name+' · ':''}${countryName(state.market)}`);
}
