// Prefer trusted edge metadata. The header fallback is opt-in and only valid behind
// a Cloudflare proxy that overwrites CF-IPCountry (verified on the review host).
export function locationData(request, options={}) {
 const edgeCountry=request.cf?.country || (options.trustCloudflareHeader?request.headers.get("CF-IPCountry"):null);
 const edgeContinent=request.cf?.continent;
 const country=/^[A-Z]{2}$/.test(edgeCountry||'')&&!['XX','T1'].includes(edgeCountry)?edgeCountry:null;
 const continent=['EU','NA','SA','AF','AS','OC','AN'].includes(edgeContinent)?edgeContinent:null;
 return {country,continent:country?continent:null,source:country?'network':'unavailable'};
}
export function locationResponse(request,allowedOrigins=[],options={}) {
 const origin=request.headers.get('Origin');
 if(origin&&origin!==new URL(request.url).origin&&!allowedOrigins.includes(origin))return new Response('Forbidden',{status:403});
 return Response.json(locationData(request,options),{headers:{'Cache-Control':'private, no-store, max-age=0','Vary':'Origin',...(origin?{'Access-Control-Allow-Origin':origin}:{})}});
}
export default {fetch(request,env={}){
 if(new URL(request.url).pathname!=='/api/location')return new Response('Not found',{status:404});
 if(request.method!=='GET')return new Response('Method not allowed',{status:405});
 return locationResponse(request,(env.ALLOWED_ORIGINS||'').split(',').filter(Boolean),{trustCloudflareHeader:env.TRUST_CLOUDFLARE_COUNTRY_HEADER==='true'});
}};
