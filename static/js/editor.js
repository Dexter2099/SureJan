function initToolbar(root=document){
  root.querySelectorAll('.editor-toolbar').forEach(tb=>{
    if(tb.dataset.ready)return;tb.dataset.ready=1;
    const ta=tb.nextElementSibling;if(!ta)return;
    tb.querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{
      const s=ta.selectionStart,e=ta.selectionEnd,v=ta.value,sel=v.slice(s,e);
      if(b.dataset.wrap){const w=b.dataset.wrap;ta.value=v.slice(0,s)+w+sel+w+v.slice(e);ta.setSelectionRange(s+w.length,s+w.length+sel.length);} 
      else if(b.dataset.link){const u=prompt('URL','https://');if(!u)return;const t=sel||'text',m=`[${t}](${u})`;ta.value=v.slice(0,s)+m+v.slice(e);ta.setSelectionRange(s+m.length,s+m.length);} 
      else if(b.dataset.prefix){const p=b.dataset.prefix,l=sel.split('\n').map(x=>p+x).join('\n');ta.value=v.slice(0,s)+l+v.slice(e);ta.setSelectionRange(s,s+l.length);} 
      ta.focus();ta.dispatchEvent(new Event('input',{bubbles:true}));
    }));
  });
}

document.addEventListener('DOMContentLoaded',()=>{
  const titleField=document.getElementById('id_title');
  const bodyField=document.getElementById('id_body');
  const urlField=document.getElementById('id_url');
  const postTypeField=document.getElementById('id_post_type');
  const titleCount=document.getElementById('title-count');
  const bodyCount=document.getElementById('body-count');
  const TITLE_MAX=300,BODY_MAX=40000;

  function updateCount(f,c,m){if(!f||!c)return;c.textContent=`${f.value.length} / ${m}`;}

  if(titleField&&titleCount){updateCount(titleField,titleCount,TITLE_MAX);titleField.addEventListener('input',()=>updateCount(titleField,titleCount,TITLE_MAX));}

  function autoResize(el){if(!el)return;el.style.height='auto';const max=window.innerHeight*0.6;el.style.height=Math.min(el.scrollHeight,max)+'px';}

  if(bodyField&&bodyCount){updateCount(bodyField,bodyCount,BODY_MAX);autoResize(bodyField);bodyField.addEventListener('input',()=>{updateCount(bodyField,bodyCount,BODY_MAX);autoResize(bodyField);});}

  const form=document.querySelector('.post-form');
  if(form){form.addEventListener('submit',()=>{if(postTypeField){const urlVal=urlField&&urlField.value.trim();postTypeField.value=urlVal?'link':'text';}});}

  initToolbar();
});

document.addEventListener('htmx:load',e=>initToolbar(e.detail.elt));
