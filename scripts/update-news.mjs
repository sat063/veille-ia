import fs from 'node:fs';
import path from 'node:path';

const DAYS=35;
const minTime=Date.now()-DAYS*86400000;
const github=[
 {repo:'ollama/ollama',category:'local',label:'Ollama',icon:'🦙',kind:'pc',importance:5},
 {repo:'NousResearch/hermes-agent',category:'automation',label:'Hermes Agent',icon:'🤖',kind:'pc',importance:5},
 {repo:'upstash/context7',category:'plugins',label:'Context7',icon:'🧩',kind:'plugin',importance:4},
 {repo:'supabase/supabase',category:'plugins',label:'Supabase',icon:'🟢',kind:'plugin',importance:3},
 {repo:'google-gemini/gemini-cli',category:'other',label:'Gemini CLI',icon:'💎',kind:'pc',importance:3},
 {repo:'openai/codex',category:'other',label:'Codex',icon:'💻',kind:'web',importance:4}
];
const rss=[
 {url:'https://openai.com/news/rss.xml',domain:'openai.com',source:'OpenAI',category:'chatgpt',icon:'✦',kind:'web',importance:4,pattern:/chatgpt|gpt[-\s]?[456]|codex|connectors?|plugins?|apps?|memory|projects?|tasks?|agents?|voice/i},
 {url:'https://openai.com/products/release-notes/rss.xml',domain:'openai.com',source:'OpenAI',category:'chatgpt',icon:'✦',kind:'web',importance:4,pattern:/chatgpt|codex|gpt[-\s]?6|plugins?|connectors?|agents?|apps?/i},
 {url:'https://ollama.com/blog/rss.xml',domain:'ollama.com',source:'Ollama',category:'local',icon:'🧠',kind:'pc',importance:5,pattern:/.+/}
];
const headers={'User-Agent':'VeilleIA/2.0 (+https://github.com/sat063/veille-ia)','Accept':'application/json, application/rss+xml, text/xml, */*'};
async function get(url){const r=await fetch(url,{headers,signal:AbortSignal.timeout(15000)});if(!r.ok)throw new Error(url+' HTTP '+r.status);return r}
function plain(s){return String(s||'').replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g,'$1').replace(/<[^>]*>/g,'').replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"').replace(/&#39;/g,"'").replace(/\s+/g,' ').trim().slice(0,155)}
function field(item,tag){const m=new RegExp('<'+tag+'(?:\\s[^>]*)?>([\\s\\S]*?)<\\/'+tag+'>','i').exec(item);return m?plain(m[1]):''}
function sortNews(a,b){return Date.parse(b.date)-Date.parse(a.date)}
async function fromGithub(f){
 const response=await get('https://api.github.com/repos/'+f.repo+'/releases?per_page=5');
 const list=await response.json();
 if(!Array.isArray(list))return [];
 return list.filter(x=>!x.draft&&!x.prerelease&&x.published_at&&Date.parse(x.published_at)>minTime&&/^https:\/\/github\.com\//.test(x.html_url||'')).slice(0,3).map(x=>({
 id:'gh:'+f.repo+':'+String(x.tag_name||x.id),category:f.category,
 title:f.label+' · '+plain(x.name||x.tag_name||'Nouvelle version'),
 description:'Version officielle publiee sur GitHub. Consulter les notes avant installation.',
 short:'Nouvelle version disponible.',date:x.published_at,source:'GitHub · '+f.repo,url:x.html_url,
 badge:'Nouveau',importance:f.importance,platform:['iphone','windows'],free:true,noApi:true,kind:f.kind,icon:f.icon,isLive:true
 }));
}
async function fromRSS(f){
 const xml=await (await get(f.url)).text();
 const items=[...xml.matchAll(/<item(?:\s[^>]*)?>([\s\S]*?)<\/item>/gi)];
 return items.map(m=>m[1]).map(item=>{
 const title=field(item,'title'),url=field(item,'link'),stamp=field(item,'pubDate')||field(item,'dc:date'),date=new Date(stamp);
 if(!title||!url||!Number.isFinite(date.getTime())||date.getTime()<minTime||!f.pattern.test(title))return null;
 let link;try{link=new URL(url)}catch{return null}
 if(link.protocol!=='https:'||link.hostname!==f.domain&&link.hostname!=='www.'+f.domain)return null;
 const category=/connectors?|plugins?|apps? in chatgpt/i.test(title)?'plugins':f.category;
 return {id:'rss:'+link.pathname+link.search,category,title:plain(title),description:'Annonce officielle de '+f.source+'. Consulte les details dans la source.',short:'Annonce officielle a decouvrir.',date:date.toISOString(),source:f.source,url:link.href,badge:'Nouveau',importance:f.importance,platform:['iphone','windows'],free:true,noApi:true,kind:f.kind,icon:f.icon,isLive:true};
 }).filter(Boolean).slice(0,8);
}
const results=await Promise.allSettled([...github.map(fromGithub),...rss.map(fromRSS)]);
const entries=results.flatMap((result,i)=>{
 if(result.status==='fulfilled'){console.log('OK',i,result.value.length);return result.value}
 console.error('SOURCE ERROR',i,String(result.reason));return [];
});
const outputFile=path.join('data','updates.json');fs.mkdirSync('data',{recursive:true});
const previous=fs.existsSync(outputFile)?JSON.parse(fs.readFileSync(outputFile,'utf8')):{entries:[]};
const candidates=[...entries,...(previous.entries||[]).filter(x=>x?.isLive&&Date.parse(x.date)>minTime)];
const seen=new Set(),unique=[];
for(const item of candidates.sort(sortNews)){
 if(!item?.id||seen.has(item.id)||!/^https:\/\//.test(item.url))continue;
 seen.add(item.id);unique.push(item);if(unique.length>=40)break;
}
if(!unique.length&&results.every(x=>x.status==='rejected'))throw new Error('Toutes les sources sont indisponibles, pas de publication de donnees vides');
fs.writeFileSync(outputFile,JSON.stringify({version:2,generatedAt:new Date().toISOString(),timezone:'Europe/Paris',schedule:'quotidien 08:17',entries:unique},null,2)+'\n','utf8');
console.log('Daily update:',unique.length,'items, from',results.filter(x=>x.status==='fulfilled').length,'sources');
