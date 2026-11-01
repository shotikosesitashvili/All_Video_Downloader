const nav=document.querySelector('.nav');
const button=document.createElement('button');
button.type='button';
button.textContent='აპის დაყენება';
button.setAttribute('aria-label','Clipstack-ის მთავარ ეკრანზე დამატება');
button.style.cssText='border:1px solid #526144;border-radius:8px;background:#c5f568;color:#152012;padding:10px 14px;font:600 11px inherit;cursor:pointer';
nav.append(button);
let installPrompt=null;
const standalone=()=>matchMedia('(display-mode: standalone)').matches||navigator.standalone===true;
const update=()=>{button.hidden=standalone();};
update();
window.addEventListener('appinstalled',()=>{installPrompt=null;button.hidden=true;});
window.addEventListener('beforeinstallprompt',event=>{
 event.preventDefault();
 installPrompt=event;
 button.textContent='აპის დაყენება';
});
button.addEventListener('click',async()=>{
 if(standalone())return;
 if(installPrompt){
  installPrompt.prompt();
  await installPrompt.userChoice;
  installPrompt=null;
  return;
 }
 const ios=/iphone|ipad|ipod/i.test(navigator.userAgent);
 alert(ios
  ? 'Safari-ში დააჭირე გაზიარების ღილაკს, შემდეგ აირჩიე „Add to Home Screen“ / „მთავარ ეკრანზე დამატება“.'
  : 'Chrome-ში გახსენი ⋮ მენიუ და აირჩიე „Install app“ ან „Add to Home screen“.');
});