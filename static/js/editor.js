function setupEditor(ta){
  if(!ta||ta.dataset.editorReady)return;ta.dataset.editorReady=1;
  ta.addEventListener('keydown',e=>{
    const ctrl=e.ctrlKey||e.metaKey,key=e.key.toLowerCase();
    if(ctrl&&key==='enter'){e.preventDefault();const f=ta.closest('form');if(f){if(f.requestSubmit)f.requestSubmit();else f.submit();}}
    else if(key==='enter'&&e.shiftKey){
      e.preventDefault();
      e.stopPropagation();
      ta.setRangeText('\n',ta.selectionStart,ta.selectionEnd,'end');
      ta.dispatchEvent(new Event('input',{bubbles:true}));
    }
    else if(ctrl&&key==='b'){e.preventDefault();toggleWrap('**');}
    else if(ctrl&&key==='i'){e.preventDefault();toggleWrap('_');}

    function toggleWrap(w){const s=ta.selectionStart,e=ta.selectionEnd,v=ta.value,b=v.slice(0,s),sel=v.slice(s,e),a=v.slice(e),l=w.length;if(sel.startsWith(w)&&sel.endsWith(w)){ta.setRangeText(sel.slice(l,sel.length-l),s,e,'end');ta.setSelectionRange(s,e-2*l);}else if(b.endsWith(w)&&a.startsWith(w)){ta.setRangeText(sel,s-l,e+l,'end');ta.setSelectionRange(s-l,e-l);}else{ta.setRangeText(w+sel+w,s,e,'end');ta.setSelectionRange(s+l,e+l);}ta.dispatchEvent(new Event('input',{bubbles:true}));}
  });
}

function initToolbar(root=document){
  root.querySelectorAll('.editor-toolbar').forEach(tb=>{
    if(tb.dataset.ready)return;tb.dataset.ready=1;
    const ta=tb.nextElementSibling;if(!ta)return;
    if(!ta.dataset.editor)ta.dataset.editor=1;
    if(!ta.closest('.post-form')){ta.style.lineHeight='1.5';ta.style.maxWidth='var(--prose-max)';if(ta.parentElement){ta.parentElement.style.maxWidth='var(--prose-max)';ta.parentElement.style.lineHeight='1.5';}}
    tb.querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{
      const s=ta.selectionStart,e=ta.selectionEnd,v=ta.value,sel=v.slice(s,e);
      if(b.dataset.wrap){const w=b.dataset.wrap;ta.value=v.slice(0,s)+w+sel+w+v.slice(e);ta.setSelectionRange(s+w.length,s+w.length+sel.length);}
      else if(b.dataset.link){const u=prompt('URL','https://');if(!u)return;const t=sel||'text',m=`[${t}](${u})`;ta.value=v.slice(0,s)+m+v.slice(e);ta.setSelectionRange(s+m.length,s+m.length);}
      else if(b.dataset.prefix){const p=b.dataset.prefix,l=sel.split('\n').map(x=>p+x).join('\n');ta.value=v.slice(0,s)+l+v.slice(e);ta.setSelectionRange(s,s+l.length);}
      ta.focus();ta.dispatchEvent(new Event('input',{bubbles:true}));
    }));

    setupEditor(ta);
  });
  root.querySelectorAll('textarea[data-editor]').forEach(setupEditor);
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
    let pill=form.querySelector('.draft-pill');
    if(!pill){pill=document.createElement('div');pill.className='draft-pill';form.prepend(pill);} 
    pill.hidden=false;pill.textContent='';
    const restore=document.createElement('button');restore.type='button';restore.textContent='Restore';
    const discard=document.createElement('button');discard.type='button';discard.textContent='Discard';
    pill.append(restore,' / ',discard);
    restore.addEventListener('click',()=>{fields.forEach(f=>{if(form[f]&&data[f]!==undefined){form[f].value=data[f];form[f].dispatchEvent(new Event('input',{bubbles:true}));}});pill.hidden=true;});
    discard.addEventListener('click',()=>{localStorage.removeItem(key);pill.hidden=true;});
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
  if(pf){const path=pf.getAttribute('action')||location.pathname;const m=path.match(/\/r\/([^/]+)/);if(m)setupDraft(pf,`draft:post:${m[1]}`,['title','body','url']);}
  root.querySelectorAll('form.comment-form').forEach(f=>{
    const postField=f.querySelector('input[name="post"]');
    const postId=postField&&postField.value;
    const parentField=f.querySelector('input[name="parent"]');
    const parentId=parentField&&parentField.value?parentField.value:'root';
    if(postId)setupDraft(f,`draft:comment:${postId}:${parentId}`,['body']);
  });
}

const TITLE_MAX=300,BODY_MAX=40000;

function updateCount(f,c,m){
  if(!f||!c)return;
  const len=f.value.length;
  c.textContent=`${len} / ${m}`;
  c.classList.toggle('near-limit',len>m*0.9&&len<=m);
  c.classList.toggle('over-limit',len>m);
}

function initCounts(root=document){
  const titleField=root.querySelector('#id_title');
  const bodyField=root.querySelector('#id_body');
  const titleCount=root.querySelector('#title-count');
  const bodyCount=root.querySelector('#body-count');
  function bind(field,count,max){
    if(!field||!count||field.dataset.countReady)return;
    field.dataset.countReady=1;
    const upd=()=>updateCount(field,count,max);
    upd();
    field.addEventListener('input',upd);
  }
  bind(titleField,titleCount,TITLE_MAX);
  bind(bodyField,bodyCount,BODY_MAX);
}

function initAutogrow(root=document){
  root.querySelectorAll('textarea').forEach(el=>{
    if(el.dataset.autogrowReady)return;el.dataset.autogrowReady=1;
    function grow(){el.style.height='auto';const max=window.innerHeight*0.6;el.style.height=Math.min(el.scrollHeight,max)+'px';}
    grow();
    el.addEventListener('input',grow);
  });
}

document.addEventListener('DOMContentLoaded',()=>{
  initAutogrow();
  initCounts();
  const bodyField=document.getElementById('id_body');
  const urlField=document.getElementById('id_url');
  const postTypeField=document.getElementById('id_post_type');
  let domainHint;
  function updateDomain(){if(!urlField||!domainHint)return;const v=urlField.value.trim();let h='';if(v){try{h=new URL(v).hostname;}catch(e){}}domainHint.textContent=h?`(${h})`:'';}
  if(urlField){domainHint=document.createElement('div');domainHint.id='link-domain';urlField.insertAdjacentElement('afterend',domainHint);urlField.addEventListener('input',updateDomain);updateDomain();}

  if(bodyField&&urlField){bodyField.addEventListener('paste',e=>{const t=e.clipboardData.getData('text/plain').trim();if(/^https?:\/\/\S+$/.test(t)&&!urlField.value.trim()){setTimeout(()=>{if(confirm('Move this to Content URL?')){urlField.value=t;urlField.dispatchEvent(new Event('input',{bubbles:true}));}},0);}});}

  const form=document.querySelector('.post-form');
  if(form){form.addEventListener('submit',()=>{if(postTypeField){const urlVal=urlField&&urlField.value.trim();postTypeField.value=urlVal?'link':'text';}});}

  initToolbar();
  initPreview();
  initDrafts();
});

document.addEventListener('htmx:load',e=>{initToolbar(e.detail.elt);initPreview(e.detail.elt);initDrafts(e.detail.elt);initAutogrow(e.detail.elt);initCounts(e.detail.elt);});

function toggleSubmit(form,on){
  if(!form)return;
  const btn=form.querySelector('button[type="submit"],input[type="submit"]');
  if(!btn)return;
  btn.disabled=on;
  const sp=btn.querySelector('.spinner');
  if(sp)sp.hidden=!on;
  if(on)showFormError(form,'');
}

function showFormError(form,msg){
  const box=form.querySelector('.form-error');
  if(box){box.textContent=msg;box.style.display=msg?'block':'none';}
}

document.addEventListener('submit',e=>{toggleSubmit(e.target,true);},true);
document.body.addEventListener('htmx:beforeRequest',e=>{const f=e.detail.elt.closest('form');toggleSubmit(f,true);});
document.body.addEventListener('htmx:responseError',e=>{e.preventDefault();const f=e.detail.elt.closest('form');const msg=e.detail.xhr&&e.detail.xhr.responseText?e.detail.xhr.responseText:'Error submitting form';toggleSubmit(f,false);showFormError(f,msg);});
document.body.addEventListener('htmx:sendError',e=>{e.preventDefault();const f=e.detail.elt.closest('form');toggleSubmit(f,false);showFormError(f,'Network error');});
document.body.addEventListener('htmx:afterRequest',e=>{const f=e.detail.elt.closest('form');if(f&&e.detail.xhr&&e.detail.xhr.status<400)toggleSubmit(f,false);});

let lastFocus=null,lastScroll=null;
document.body.addEventListener('htmx:beforeSwap',()=>{
  const ae=document.activeElement;
  lastFocus=null;
  if(ae&&(ae.id||ae.name)){
    lastFocus={id:ae.id,name:ae.name,start:ae.selectionStart,end:ae.selectionEnd};
  }
  lastScroll={x:window.scrollX,y:window.scrollY};
});
document.body.addEventListener('htmx:afterSwap',()=>{
  if(lastScroll)window.scrollTo(lastScroll.x,lastScroll.y);
  if(lastFocus){
    const el=lastFocus.id?document.getElementById(lastFocus.id):document.querySelector(`[name="${lastFocus.name}"]`);
    if(el){
      el.focus();
      if(lastFocus.start!=null)try{el.setSelectionRange(lastFocus.start,lastFocus.end);}catch{}
    }
  }
  lastFocus=null;lastScroll=null;
});
