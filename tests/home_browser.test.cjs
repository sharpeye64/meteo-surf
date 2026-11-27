// Données simulées du test hors ligne, jamais publiées. Chromium réel, pas de requête météo.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const os = require('node:os');
const src=fs.readdirSync(os.tmpdir()).filter(x=>x.startsWith('houlalah-test-')).map(x=>path.join(os.tmpdir(),x)).sort((a,b)=>fs.statSync(b).mtimeMs-fs.statSync(a).mtimeMs)[0];
assert(src,'Exécuter tests.test_offline avant ce test');
// La CI teste aussi une seconde génération pour l'archive #1 : le forecast de référence
// peut avoir été restauré après ce test. Ne jamais mélanger ces fixtures.
const fcPath=path.join(src,'data/forecast.json'), ixPath=path.join(src,'data/home-index.json');
const fc=JSON.parse(fs.readFileSync(fcPath)), ix=JSON.parse(fs.readFileSync(ixPath));
if(fc.meta.generated!==ix.meta.generated){
  console.log('Fixture archive : génération index',ix.meta.generated,'forecast',fc.meta.generated);
  // Reconstituer uniquement le dérivé de la fixture à partir du forecast restauré.
  require('node:child_process').execFileSync('python',['-c','import json,sys; from pathlib import Path; from tools.benchmark_home_index import compact,encode; Path(sys.argv[2]).write_bytes(encode(compact(json.loads(Path(sys.argv[1]).read_text()))))',fcPath,ixPath]);
}
assert.equal(JSON.parse(fs.readFileSync(ixPath)).meta.generated,fc.meta.generated);
const server=http.createServer((req,res)=>{
  const p=new URL(req.url,'http://localhost').pathname;
  const rel=p==='/'?'index.html':p.slice(1);
  const file=[path.join(src,rel),path.join('web',rel)].find(x=>fs.existsSync(x)&&fs.statSync(x).isFile());
  if(!file){res.writeHead(404);res.end();return;}
  res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.js':'application/javascript','.json':'application/json','.svg':'image/svg+xml','.css':'text/css'})[path.extname(file)]||'application/octet-stream');
  fs.createReadStream(file).pipe(res);
});
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const url='http://127.0.0.1:'+server.address().port;
 const browser=await chromium.launch({args:['--enable-unsafe-swiftshader']});
 try{
 for(const mobile of [false,true]){
   const context=await browser.newContext({viewport:mobile?{width:390,height:844}:{width:1440,height:900},isMobile:mobile,hasTouch:mobile,serviceWorkers:'block'});
   const page=await context.newPage();
   const errors=[], requests=[];
   const start=Date.now();
   page.on('pageerror',e=>errors.push(e.message));
   page.on('request',r=>requests.push(r.url()));
   // Bloque les appels météo directs ; les dépendances cartographiques externes restent autorisées.
   await page.route(/https?:\/\/[^/]*open-meteo\.com\//,r=>r.abort());
   await page.goto(url);
   await page.waitForFunction(()=>typeof HOME!=='undefined'&&HOME.on&&HOME.data.length>0);
   assert.equal(await page.evaluate(()=>HOME_COMPACT),true);
   console.log('Accueil données prêtes (ms)',mobile?'mobile':'desktop',Date.now()-start);
   assert(!requests.some(x=>x.endsWith('/data/forecast.json')),'forecast chargé trop tôt');
   const compact=await page.evaluate(()=>HOME.data.map(s=>({n:s.n,hm:Object.values(s.hm).map(h=>[h.time,h.H,h.T,h.D,h.v,h.wd,h.wind??null])})));
   assert.equal(compact.length,214);
   const spot=await page.evaluate(()=>{const s=HOME.data.find(s=>s.n==='Lacanau');homeSpot(s,false);return s.n;});
   assert.equal(spot,'Lacanau');
   await page.locator('#hoNums').waitFor({state:'visible'});
   await page.locator('#hoFv').click();
   assert(await page.evaluate(()=>state.fav.includes('Lacanau')));
   const buoy=await page.evaluate(()=>{const b=HOME.bu[0];return b?homeBuoyTip(b):null;});
   assert(buoy&&buoy.includes('m'),'infobulle bouée absente');
   // Sur mobile, simuler une nouvelle génération arrivée après l'ouverture de la carte.
   if(mobile) await page.route('**/data/forecast.json',async route=>{
     const response=await route.fetch(), data=await response.json();
     data.meta.generated=new Date(Date.parse(data.meta.generated)+3600000).toISOString();
     await route.fulfill({response,json:data});
   });
   await page.locator('#hoGo').click();
   await page.waitForFunction(()=>!HOME.on&&!HOME_COMPACT&&state.data[state.spot].spot.name==='Lacanau');
   assert.equal(requests.filter(x=>x.endsWith('/data/forecast.json')).length,1);
   const full=await page.evaluate(()=>homeData().map(s=>({n:s.n,hm:Object.values(s.hm).map(h=>[h.time,h.H,h.T,h.D,h.v,h.wd,h.wind??null])})));
   assert.deepEqual(compact,full,'parité des 214 spots');
   if(mobile){
     assert.equal(await page.evaluate(()=>HOME.ready),false,'carte à reconstruire après changement de génération');
     await page.evaluate(()=>homeOpen(true));
     await page.waitForFunction(()=>HOME.on&&HOME.ready);
     assert.equal(requests.filter(x=>x.endsWith('/data/forecast.json')).length,1,'aucun rechargement au retour carte');
     await page.unroute('**/data/forecast.json');
   }
   await page.goto(url+'/?spot=lacanau');
   await page.waitForFunction(()=>state.data&&state.data[state.spot].spot.name==='Lacanau'&&!HOME.on);
   assert.equal(await page.evaluate(()=>HOME_COMPACT),false);
   assert.deepEqual(errors,[]);
   console.log('OK',mobile?'mobile':'desktop','214 spots, favoris, infobulle, navigation, lien profond');
   await context.close();
 }
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exit(1);});
