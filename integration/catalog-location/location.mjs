// Cloudflare supplies cf.country from the connection. Never trust user-supplied query/header overrides.
export function locationData(request) {
 const country=/^[A-Z]{2}$/.test(request.cf?.country||'')&&!['XX','T1'].includes(request.cf.country)?request.cf.country:null;
 const continent=['EU','NA','SA','AF','AS','OC','AN'].includes(request.cf?.continent)?request.cf.continent:null;
 return {country,continent:country?continent:null,source:country?'network':'unavailable'};
}
export function locationResponse(request,allowedOrigins=[]) {
 const origin=request.headers.get('Origin');
 if(origin&&origin!==new URL(request.url).origin&&!allowedOrigins.includes(origin))return new Response('Forbidden',{status:403});
 return Response.json(locationData(request),{headers:{'Cache-Control':'private, no-store, max-age=0','Vary':'Origin',...(origin?{'Access-Control-Allow-Origin':origin}:{})}});
}
export default {fetch(request,env={}){
 if(new URL(request.url).pathname!=='/api/location')return new Response('Not found',{status:404});
 if(request.method!=='GET')return new Response('Method not allowed',{status:405});
 return locationResponse(request,(env.ALLOWED_ORIGINS||'').split(',').filter(Boolean));
}};
