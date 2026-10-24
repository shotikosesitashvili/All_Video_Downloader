import './style.css';
const icon = (name, size=20) => {
 const paths={arrow:'<path d="M12 4v16m-6-6 6 6 6-6M4 20v2h16v-2"/>',
 link:'<path d="m10 13 4-4m-6 7-1 1a4 4 0 0 1-6-6l4-4a4 4 0 0 1 6 0m2 1 1-1a4 4 0 1 1 6 6l-4 4a4 4 0 0 1-6 0"/>',
 play:'<path d="m9 6 10 6-10 6Z"/>', check:'<path d="m5 12 4 4L19 6"/>',
 clipboard:'<rect x="6" y="5" width="14" height="17" rx="2"/><path d="M9 5V2h8v3M6 8H3v12"/>',
 music:'<path d="M9 18V5l11-2v13M9 8l11-2"/><ellipse cx="6" cy="18" rx="3" ry="3"/><ellipse cx="17" cy="16" rx="3" ry="3"/>',
 globe:'<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c5 5 5 13 0 18-5-5-5-13 0-18Z"/>',
 close:'<path d="m6 6 12 12M6 18 18 6"/>', shield:'<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6Z"/><path d="m8 12 3 3 5-6"/>',
 external:'<path d="M14 3h7v7m0-7L10 14M10 4H4v16h16v-6"/>'};
 return '<svg width="'+size+'" height="'+size+'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'+(paths[name]||paths.play)+'</svg>';
};
document.querySelector('#app').innerHTML = `
<header class="nav wrap">
 <a class="brand" href="/" aria-label="Clipstack მთავარი"><span class="brand-mark">${icon('arrow',23)}</span>clipstack<span class="brand-dot">.</span></a>
 <nav aria-label="მთავარი ნავიგაცია"><a href="#how">როგორ მუშაობს</a><a href="#faq">კითხვები</a></nav>
 <span class="nav-badge"><i></i>უფასო ინსტრუმენტი</span>
</header>
<main>
 <section class="hero wrap">
  <div class="eyebrow"><span class="tiny-star">✳</span> ნაკლები ნაბიჯი. მეტი ვიდეო.</div>
  <h1>შენი ვიდეო.<br><span>შენთან.</span></h1>
  <p class="hero-copy">ჩასვი ბმული, აირჩიე ხარისხი და შეინახე.<br>შენი საყვარელი მომენტები — ერთ ადგილას.</p>
  <div class="platforms" aria-label="პლატფორმები"><span class="youtube">▶</span><span>YouTube</span><b>·</b><span class="tiktok">♪</span><span>TikTok</span><b>·</b><span class="instagram">◎</span><span>Instagram</span><b>·</b><span class="facebook">f</span><span>Facebook</span><b>·</b>${icon('globe',16)}<span>და სხვა</span></div>
  <div class="download-card">
   <div class="card-top"><span class="step-tag">01 / ბმული</span><span class="card-hint">ვიდეოდან — შენს მოწყობილობაზე</span></div>
   <form id="inspect-form">
    <label for="video-url" class="sr-only">ვიდეოს საჯარო ბმული</label>
    <div class="input-row"><span class="input-icon">${icon('link')}</span><input id="video-url" type="url" placeholder="ჩასვი ვიდეოს ბმული აქ…" required autocomplete="off" maxlength="4000"><button class="paste" id="paste" type="button" aria-label="ბმულის ჩასმა ბუფერიდან" title="ჩასმა">${icon('clipboard')}</button><button class="primary" id="inspect-btn" type="submit"><span>ვიდეოს პოვნა</span>${icon('arrow',18)}</button></div>
   </form>
   <div class="card-bottom"><span>${icon('shield',15)} რეგისტრაციის გარეშე</span><span>მხოლოდ საჯარო ვიდეოები</span></div>
   <div id="status" role="status" aria-live="polite" hidden></div>
   <section id="result" aria-label="ვიდეოს ხარისხის არჩევა" hidden>
    <div class="result-head"><span class="video-icon">${icon('play',25)}</span><div><span id="source" class="step-tag"></span><h2 id="title"></h2><p id="video-meta"></p></div></div>
    <div class="format-tabs" role="group" aria-label="ფორმატი"><button type="button" id="video-tab" class="active">${icon('play',16)} ვიდეო</button><button type="button" id="audio-tab">${icon('music',16)} MP3 აუდიო</button></div>
    <div id="quality-list" class="quality-list"></div>
    <p id="format-note" class="format-note"></p>
    <div class="download-actions"><button class="primary" type="button" id="download-btn">${icon('arrow',18)} ჩამოტვირთვა</button><button id="cancel-btn" class="secondary" type="button" hidden>გაუქმება</button><span id="size-note"></span></div>
    <div id="progress-area" hidden><div class="progress-track"><div id="progress-bar"></div></div><p id="progress-text" role="status" aria-live="polite"></p></div>
    <a id="save-again" class="save-link" hidden>ფაილის შენახვა ხელახლა ↗</a>
   </section>
  </div>
  <p class="usage-note">ჩამოტვირთე მხოლოდ მასალა, რომლის შენახვის უფლებაც გაქვს.</p>
 </section>
 <section class="feature-strip wrap" aria-label="უპირატესობები"><div><span class="feature-number">01</span><div><strong>აირჩიე ხარისხი</strong><p>რაც წყაროზე ხელმისაწვდომია</p></div></div><div><span class="feature-number">02</span><div><strong>ვიდეო ან აუდიო</strong><p>შეინახე ზუსტად რაც გჭირდება</p></div></div><div><span class="feature-number">03</span><div><strong>შენთან რჩება</strong><p>ფაილები სერვერზე არ ინახება</p></div></div></section>
 <section id="how" class="how wrap"><div class="section-heading"><div><span class="section-kicker">ბმულიდან ფაილამდე</span><h2>სამი მარტივი ნაბიჯი.</h2></div><p>ზედმეტი აპების გარეშე.<br>პირდაპირ ბრაუზერიდან.</p></div><div class="steps"><article><span class="step-visual">${icon('link',30)}<small>01</small></span><h3>დააკოპირე ბმული</h3><p>გახსენი საჯარო ვიდეო და დააკოპირე მისი მისამართი გაზიარების მენიუდან.</p></article><article><span class="step-visual">${icon('play',30)}<small>02</small></span><h3>აირჩიე ფორმატი</h3><p>ჩასვი ბმული და აირჩიე ნაპოვნი ხარისხი ან მხოლოდ MP3 აუდიო.</p></article><article><span class="step-visual">${icon('arrow',30)}<small>03</small></span><h3>შეინახე მომენტი</h3><p>დააჭირე ჩამოტვირთვას და დაელოდე. დამუშავებისას გვერდი ღია დატოვე.</p></article></div></section>
 <section id="faq" class="faq wrap"><div><span class="section-kicker">კარგია იცოდე</span><h2>მოკლე პასუხები.</h2><p>მარტივი ინსტრუმენტი,<br>გასაგები პირობებით.</p></div><div class="faq-items"><details><summary>რომელი ვიდეოების ჩამოტვირთვა შემიძლია?<span>+</span></summary><p>საჯარო ვიდეოების, რომელთაც წყარო ხელმისაწვდომ ფორმატში გვაწვდის. YouTube, TikTok, Instagram, Facebook და სხვა საიტების მხარდაჭერა დამოკიდებულია ვიდეოსა და პლატფორმის შეზღუდვებზე. პირადი და DRM-ით დაცული ვიდეოები არ მხარდაჭერება.</p></details><details><summary>რა ზომის ფაილების შენახვა შემიძლია?<span>+</span></summary><p>თითოეული საწყისი ვიდეო ან აუდიო ნაკადი მაქსიმუმ 64 MB. ვიდეოსა და ხმის გაერთიანება და MP3-ის შექმნა შენს ბრაუზერში ხდება. დიდმა ხარისხმა შეიძლება მოწყობილობის მეტი მეხსიერება მოითხოვოს.</p></details><details><summary>რატომ ვერ ჩამოიტვირთა ვიდეო?<span>+</span></summary><p>საიტმა შეიძლება დაბლოკოს სერვერის IP, ბმულის ვადა ამოიწუროს ან ვიდეოს გადაცემა ამ რეჟიმთან შეუთავსებელი იყოს. სცადე სხვა საჯარო ვიდეო ან დაბალი ხარისხი. ყველა საიტზე მუშაობა გარანტირებული არ არის.</p></details><details><summary>ინახავთ ჩემს ვიდეოებს?<span>+</span></summary><p>ვიდეოების ბიბლიოთეკას არ ვინახავთ. ჩამოტვირთვისას მონაცემები დროებით გადის სერვერზე და მუშავდება შენს ბრაუზერში. ჰოსტინგის პროვაიდერმა შეიძლება შეინახოს ტექნიკური მოთხოვნების ლოგები.</p></details></div></section>
</main>
<footer class="wrap"><a class="brand" href="/">clipstack<span class="brand-dot">.</span></a><span>კარგ მომენტებს შენახვა უხდება.</span><span>შექმნილია მარტივად.</span></footer>
`;
const $ = id=>document.getElementById(id);
let info=null,selected=0,mode='video',controller=null,ffmpeg=null,blobURL=null;
const MAX=64*1024*1024, CHUNK=2*1024*1024;
const size = bytes=> bytes ? (bytes/1024/1024).toFixed(1)+' MB' : 'ზომა უცნობია';
const message=(text,error=false)=>{ $('status').hidden=!text; $('status').textContent=text; $('status').className=error?'error':'notice'; };
const progress=(text,percent)=>{ $('progress-area').hidden=false; $('progress-text').textContent=text; $('progress-bar').style.width=Math.min(100,percent)+'%'; };
async function jsonRequest(action,body,signal){
 const response=await fetch('/api/index?action='+action,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal});
 if(!response.ok){ let data;try{data=await response.json();}catch{} throw new Error(data?.error||'სერვერი დროებით მიუწვდომელია. სცადე ხელახლა.');}
 return response.json();
}
$('paste').addEventListener('click',async()=>{try{$('video-url').value=await navigator.clipboard.readText();$('video-url').focus();}catch{message('ჩასასმელად გამოიყენე Ctrl+V ან ტელეფონის ჩასმის მენიუ.');$('video-url').focus();}});
$('inspect-form').addEventListener('submit',async e=>{
 e.preventDefault(); if(controller)return;
 try {const url=new URL($('video-url').value.trim());if(!['http:','https:'].includes(url.protocol))throw 0;}
 catch{message('ჩასვი სწორი http ან https ბმული.',true);return;}
 controller=new AbortController();
 $('inspect-btn').disabled=true; $('inspect-btn').querySelector('span').textContent='ვამოწმებ…';
 $('result').hidden=true;message('ვიდეოს ვეძებ და ხარისხებს ვამოწმებ…');
 try{info=await jsonRequest('inspect',{url:$('video-url').value.trim()},controller.signal);selected=0;mode=info.options.length?'video':'audio';
 $('title').textContent=info.title;$('source').textContent=info.source;
 $('video-meta').textContent=(info.duration?Math.floor(info.duration/60)+':'+String(Math.floor(info.duration%60)).padStart(2,'0')+' · ':'')+info.options.length+' ვიდეო ხარისხი';
 $('video-tab').disabled=!info.options.length;$('audio-tab').disabled=!info.audio;
 $('result').hidden=false;$('progress-area').hidden=true;$('save-again').hidden=true;renderOptions();message('');
 }catch(err){message(err.message,true);}
 finally{controller=null;$('inspect-btn').disabled=false;$('inspect-btn').querySelector('span').textContent='ვიდეოს პოვნა';}
});
function renderOptions(){
 $('video-tab').classList.toggle('active',mode==='video');$('audio-tab').classList.toggle('active',mode==='audio');
 $('quality-list').replaceChildren();
 const options=mode==='video'?info.options:[{label:'MP3',video:info.audio,audio:null}];
 options.forEach((option,i)=>{
 const b=document.createElement('button');b.type='button';b.className='quality'+(i===selected?' selected':'');
 const label=document.createElement('strong');label.textContent=option.label;
 const detail=document.createElement('span');detail.textContent=mode==='audio'?'192 kbps':option.video.ext.toUpperCase()+(option.audio?' + ხმა':'');
 b.append(label,detail);b.setAttribute('aria-pressed',String(i===selected));b.onclick=()=>{if(!controller){selected=i;renderOptions();}};$('quality-list').append(b);
 });
 const option=options[selected];
 $('size-note').textContent=option?size((option.video.size||0)+(option.audio?.size||0)):'';
 $('format-note').textContent=mode==='audio'?'MP3 შენს ბრაუზერში შეიქმნება. პირველად დამუშავების მოდული (~31 MB) ჩაიტვირთება.':option?.audio?'ვიდეო და ხმა შენს ბრაუზერში გაერთიანდება. პირველად დამუშავების მოდული (~31 MB) ჩაიტვირთება.':'ვიდეო ჩამოიტვირთება წყაროს ფორმატში, ხმით.';
}
$('video-tab').onclick=()=>{if(info&&!controller){mode='video';selected=0;renderOptions();}};
$('audio-tab').onclick=()=>{if(info&&!controller){mode='audio';selected=0;renderOptions();}};
async function fetchMedia(media,label,signal){
 let offset=0,total=media.size||0,parts=[];
 for(let i=0;i<MAX/CHUNK;i++){
  if(signal.aborted)throw new DOMException('Cancelled','AbortError');
  const response=await fetch('/api/index?action=chunk',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:media.token,offset}),signal});
  if(!response.ok){let data;try{data=await response.json();}catch{}throw new Error(data?.error||'წყაროდან ფაილის მიღება ვერ მოხერხდა.');}
  const bytes=new Uint8Array(await response.arrayBuffer());
  if(bytes.length>CHUNK)throw new Error('ფაილის ფრაგმენტი ზედმეტად დიდია.');
  parts.push(bytes);offset+=bytes.length;
  total=Number(response.headers.get('X-Download-Total'))||total;
  progress(label+' · '+size(offset)+(total?' / '+size(total):''),total?offset/total*75:Math.min(70,i*8+5));
  if(response.headers.get('X-Download-Done')==='1'){
   const result=new Uint8Array(offset);let position=0;
   for(const part of parts){result.set(part,position);position+=part.length;}
   return result;
  }
  if(bytes.length!==CHUNK)throw new Error('ფაილის გადაცემა შეწყდა. სცადე თავიდან.');
 }
 throw new Error('ფაილი 64 MB ლიმიტს აღემატება. აირჩიე დაბალი ხარისხი.');
}
async function getFFmpeg(signal){
 if(ffmpeg?.loaded)return ffmpeg;
 progress('დამუშავების მოდული იტვირთება (~31 MB)…',78);
 const {FFmpeg}=await import('@ffmpeg/ffmpeg');
 if(signal.aborted)throw new DOMException('Cancelled','AbortError');
 ffmpeg=new FFmpeg();
 ffmpeg.on('progress',({progress:p})=>progress('ფაილი შენს ბრაუზერში მუშავდება…',80+Math.max(0,Math.min(1,p))*18));
 await ffmpeg.load({coreURL:location.origin+'/ffmpeg/ffmpeg-core.js',wasmURL:location.origin+'/ffmpeg/ffmpeg-core.wasm'});
 if(signal.aborted){ffmpeg.terminate();ffmpeg=null;throw new DOMException('Cancelled','AbortError');}
 return ffmpeg;
}
function safeName(title){return title.replace(/[\\/:*?"<>|\x00-\x1f]/g,'_').slice(0,100)||'clipstack';}
$('cancel-btn').onclick=()=>{controller?.abort();if(ffmpeg){ffmpeg.terminate();ffmpeg=null;}};
$('download-btn').onclick=async()=>{
 if(!info||controller)return;
 controller=new AbortController();const signal=controller.signal;const actionMode=mode;
 $('download-btn').disabled=true;$('inspect-btn').disabled=true;$('cancel-btn').hidden=false;$('save-again').hidden=true;message('');
 try{
  const option=actionMode==='video'?info.options[selected]:{video:info.audio,audio:null};
  let data=await fetchMedia(option.video,actionMode==='audio'?'აუდიო იტვირთება':'ვიდეო იტვირთება',signal);
  let ext=option.video.ext;
  if(actionMode==='audio'||option.audio){
   const engine=await getFFmpeg(signal);
   const input='input.'+option.video.ext;
   await engine.writeFile(input,data);
   let args;
   if(actionMode==='audio'){ext='mp3';args=['-i',input,'-vn','-codec:a','libmp3lame','-b:a','192k','output.mp3'];}
   else {
    const audio=await fetchMedia(option.audio,'ხმა იტვირთება',signal);
    await engine.writeFile('audio.'+option.audio.ext,audio);
    ext=option.video.vcodec.startsWith('avc')&&option.audio.ext==='m4a'?'mp4':'mkv';
    args=['-i',input,'-i','audio.'+option.audio.ext,'-map','0:v:0','-map','1:a:0','-c','copy','output.'+ext];
   }
   progress('ფაილი მზადდება…',83);
   const code=await engine.exec(args,120000);
   if(code!==0)throw new Error('ბრაუზერში დამუშავება ვერ დასრულდა. სცადე დაბალი ხარისხი ან სხვა ბრაუზერი.');
   data=await engine.readFile('output.'+ext);
   for(const file of [input,'audio.'+option.audio?.ext,'output.'+ext]){try{await engine.deleteFile(file);}catch{}}
  }
  if(signal.aborted)throw new DOMException('Cancelled','AbortError');
  if(blobURL)URL.revokeObjectURL(blobURL);
  blobURL=URL.createObjectURL(new Blob([data],{type:actionMode==='audio'?'audio/mpeg':'application/octet-stream'}));
  const save=$('save-again');save.href=blobURL;save.download=safeName(info.title)+'.'+ext;save.hidden=false;save.click();
  progress('მზადაა — ფაილი შეგიძლია შეინახო.',100);
 }catch(err){
  if(ffmpeg){ffmpeg.terminate();ffmpeg=null;}
  message(signal.aborted?'ჩამოტვირთვა გაუქმდა.':err.message,true);
  $('progress-area').hidden=true;
 }finally{controller=null;$('download-btn').disabled=false;$('inspect-btn').disabled=false;$('cancel-btn').hidden=true;}
};
window.addEventListener('beforeunload',()=>{if(blobURL)URL.revokeObjectURL(blobURL);});
