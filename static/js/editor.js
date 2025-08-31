function initToolbar(root=document){
  root.querySelectorAll('.editor-toolbar').forEach(tb=>{
    if(tb.dataset.ready)return;tb.dataset.ready=1;
    const ta=tb.nextElementSibling;if(!ta)return;
    if(!ta.closest('.post-form')){ta.style.lineHeight='1.5';ta.style.maxWidth='65ch';if(ta.parentElement){ta.parentElement.style.maxWidth='65ch';ta.parentElement.style.lineHeight='1.5';}}
    tb.querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{
      const s=ta.selectionStart,e=ta.selectionEnd,v=ta.value,sel=v.slice(s,e);
      if(b.dataset.wrap){const w=b.dataset.wrap;ta.value=v.slice(0,s)+w+sel+w+v.slice(e);ta.setSelectionRange(s+w.length,s+w.length+sel.length);}
      else if(b.dataset.link){const u=prompt('URL','https://');if(!u)return;const t=sel||'text',m=`[${t}](${u})`;ta.value=v.slice(0,s)+m+v.slice(e);ta.setSelectionRange(s+m.length,s+m.length);}
      else if(b.dataset.prefix){const p=b.dataset.prefix,l=sel.split('\n').map(x=>p+x).join('\n');ta.value=v.slice(0,s)+l+v.slice(e);ta.setSelectionRange(s,s+l.length);}
      ta.focus();ta.dispatchEvent(new Event('input',{bubbles:true}));
    }));

    ta.addEventListener('keydown',e=>{
      const ctrl=e.ctrlKey||e.metaKey;
      if(ctrl&&e.key==='Enter'){e.preventDefault();const f=ta.closest('form');if(f){if(f.requestSubmit)f.requestSubmit();else f.submit();}}
      else if(e.key==='Enter'&&e.shiftKey){e.stopPropagation();}
      else if(ctrl&&(e.key==='b'||e.key==='B')){e.preventDefault();toggleWrap('**');}
      else if(ctrl&&(e.key==='i'||e.key==='I')){e.preventDefault();toggleWrap('_');}

      function toggleWrap(w){const s=ta.selectionStart,e=ta.selectionEnd,v=ta.value,b=v.slice(0,s),sel=v.slice(s,e),a=v.slice(e),l=w.length;if(sel.startsWith(w)&&sel.endsWith(w)){ta.setRangeText(sel.slice(l,sel.length-l),s,e,'end');ta.setSelectionRange(s,e-2*l);}else if(b.endsWith(w)&&a.startsWith(w)){ta.setRangeText(sel,s-l,e+l,'end');ta.setSelectionRange(s-l,e-l);}else{ta.setRangeText(w+sel+w,s,e,'end');ta.setSelectionRange(s+l,e+l);}ta.dispatchEvent(new Event('input',{bubbles:true}));}
    });
  });
}

function initPreview(root=document){
  root.querySelectorAll('.editor-container').forEach(ed=>{
    if(ed.dataset.previewReady)return;ed.dataset.previewReady=1;
    const write=ed.querySelector('.tab-write');
    const preview=ed.querySelector('.tab-preview');
    const ta=ed.querySelector('textarea');
    const pv=ed.querySelector('.preview');
    if(write&&preview&&ta&&pv){
      write.addEventListener('click',()=>{
        write.classList.add('active');
        preview.classList.remove('active');
        ta.style.display='';
        pv.style.display='none';
      });
      preview.addEventListener('click',()=>{
        preview.classList.add('active');
        write.classList.remove('active');
        ta.style.display='none';
        pv.style.display='';
      });
    }
  });
}

function setupDraft(form,key,fields){
  if(!form||form.dataset.draftReady)return;form.dataset.draftReady=1;
  let data={};try{data=JSON.parse(localStorage.getItem(key)||'{}');}catch(e){}
  if(Object.values(data).some(v=>v)){
    const banner=document.createElement('div');banner.className='draft-banner';
    const restore=document.createElement('button');restore.type='button';restore.textContent='Restore';
    const discard=document.createElement('button');discard.type='button';discard.textContent='Discard';
    banner.append('Restore draft? ',restore,' ',discard);form.prepend(banner);
    restore.addEventListener('click',()=>{fields.forEach(f=>{if(form[f]&&data[f]!==undefined){form[f].value=data[f];form[f].dispatchEvent(new Event('input',{bubbles:true}));}});banner.remove();});
    discard.addEventListener('click',()=>{localStorage.removeItem(key);banner.remove();});
  }
  const i=setInterval(()=>{
    const draft={};let empty=true;
    fields.forEach(f=>{const v=form[f]?form[f].value:'';draft[f]=v;if(v.trim())empty=false;});
    if(empty)localStorage.removeItem(key);else localStorage.setItem(key,JSON.stringify(draft));
  },2000);
  form.addEventListener('submit',()=>{clearInterval(i);localStorage.removeItem(key);});
}

function initDrafts(root=document){
  const pf=root.querySelector('.post-form');
  if(pf){const path=pf.getAttribute('action')||location.pathname;const m=path.match(/\/r\/([^/]+)/);if(m)setupDraft(pf,`draft:${m[1]}:post`,['title','body','url']);}
  root.querySelectorAll('form[hx-post*="/comment/"][hx-post$="/reply/"]').forEach(f=>{const hx=f.getAttribute('hx-post');const m=hx&&hx.match(/comment\/(\d+)/);if(m)setupDraft(f,`draft:comment:${m[1]}`,['body']);});
}

document.addEventListener('DOMContentLoaded',()=>{
  const titleField=document.getElementById('id_title');
  const bodyField=document.getElementById('id_body');
  const urlField=document.getElementById('id_url');
  const postTypeField=document.getElementById('id_post_type');
  const titleCount=document.getElementById('title-count');
  const bodyCount=document.getElementById('body-count');
  const TITLE_MAX=300,BODY_MAX=40000;
  let domainHint;
  function updateDomain(){if(!urlField||!domainHint)return;const v=urlField.value.trim();let h='';if(v){try{h=new URL(v).hostname;}catch(e){}}domainHint.textContent=h?`(${h})`:'';}
  if(urlField){domainHint=document.createElement('div');domainHint.id='link-domain';urlField.insertAdjacentElement('afterend',domainHint);urlField.addEventListener('input',updateDomain);updateDomain();}

  function updateCount(f,c,m){if(!f||!c)return;c.textContent=`${f.value.length} / ${m}`;}

  if(titleField&&titleCount){updateCount(titleField,titleCount,TITLE_MAX);titleField.addEventListener('input',()=>updateCount(titleField,titleCount,TITLE_MAX));}

  function autoResize(el){if(!el)return;el.style.height='auto';const max=window.innerHeight*0.6;el.style.height=Math.min(el.scrollHeight,max)+'px';}

  if(bodyField&&bodyCount){updateCount(bodyField,bodyCount,BODY_MAX);autoResize(bodyField);bodyField.addEventListener('input',()=>{updateCount(bodyField,bodyCount,BODY_MAX);autoResize(bodyField);});}
  if(bodyField&&urlField){bodyField.addEventListener('paste',e=>{const t=e.clipboardData.getData('text/plain').trim();if(/^https?:\/\/\S+$/.test(t)&&!urlField.value.trim()){setTimeout(()=>{if(confirm('Move this to Content URL?')){urlField.value=t;urlField.dispatchEvent(new Event('input',{bubbles:true}));}},0);}});}

  const form=document.querySelector('.post-form');
  if(form){form.addEventListener('submit',()=>{if(postTypeField){const urlVal=urlField&&urlField.value.trim();postTypeField.value=urlVal?'link':'text';}});}

  initToolbar();
  initPreview();
  initDrafts();
});

document.addEventListener('htmx:load',e=>{initToolbar(e.detail.elt);initPreview(e.detail.elt);initDrafts(e.detail.elt);});
