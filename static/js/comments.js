function initCommentCollapse(root=document){
  root.querySelectorAll('.collapse-toggle').forEach(btn=>{
    if(btn.dataset.ready) return;
    btn.dataset.ready = '1';
    btn.addEventListener('click',()=>{
      const comment = btn.closest('.comment');
      if(!comment) return;
      const isCollapsed = comment.classList.toggle('collapsed');
      btn.setAttribute('aria-expanded', (!isCollapsed).toString());
    });
  });
}

function initQuoteButtons(root=document){
  root.querySelectorAll('.quote-btn').forEach(btn=>{
    if(btn.dataset.ready) return;
    btn.dataset.ready = '1';
    btn.addEventListener('click',()=>{
      const comment = btn.closest('.comment');
      if(!comment) return;
      const quote = btn.dataset.quote || window.getSelection().toString();
      if(!quote) return;
      const lines = quote.split('\n').map(l=>'> '+l).join('\n');
      const insert = ta=>{
        if(!ta) return;
        if(ta.value && !ta.value.endsWith('\n')) ta.value += '\n';
        ta.value += lines + '\n';
        ta.focus();
      };
      let form = comment.nextElementSibling;
      let ta = form && form.querySelector ? form.querySelector('textarea') : null;
      if(ta){
        insert(ta);
      }else{
        const replyBtn = comment.querySelector('button[hx-get*="/comments/new"]');
        if(replyBtn){
          const handler = e=>{
            const nf = comment.nextElementSibling;
            const nta = nf && nf.querySelector ? nf.querySelector('textarea') : null;
            if(nta){
              insert(nta);
              document.body.removeEventListener('htmx:afterSwap', handler);
            }
          };
          document.body.addEventListener('htmx:afterSwap', handler);
          replyBtn.click();
        }
      }
      hideQuoteBubbles();
    });
  });
}

function hideQuoteBubbles(){
  document.querySelectorAll('.quote-btn').forEach(btn=>{btn.hidden=true;});
}

function handleSelection(){
  const sel = window.getSelection();
  if(!sel.rangeCount || sel.isCollapsed){
    hideQuoteBubbles();
    return;
  }
  const range = sel.getRangeAt(0);
  const ancestor = range.commonAncestorContainer;
  const comment = ancestor.nodeType === 1
    ? ancestor.closest('.comment')
    : ancestor.parentElement && ancestor.parentElement.closest('.comment');
  if(!comment){
    hideQuoteBubbles();
    return;
  }
  const btn = comment.querySelector('.quote-btn');
  if(!btn) return;
  const rect = range.getBoundingClientRect();
  btn.style.position = 'absolute';
  btn.style.fontSize = '0.75rem';
  btn.style.padding = '2px 4px';
  btn.style.left = (rect.right + window.scrollX - btn.offsetWidth) + 'px';
  btn.style.top = (rect.top + window.scrollY - btn.offsetHeight - 4) + 'px';
  btn.dataset.quote = sel.toString();
  btn.hidden = false;
}

document.addEventListener('mouseup',handleSelection);
document.addEventListener('keyup',handleSelection);
document.addEventListener('selectionchange',handleSelection);
document.addEventListener('click',e=>{if(!e.target.classList.contains('quote-btn')) hideQuoteBubbles();});

document.addEventListener('DOMContentLoaded',()=>{initCommentCollapse();initQuoteButtons();});

document.body.addEventListener('htmx:afterSwap',e=>{initCommentCollapse(e.detail.elt);initQuoteButtons(e.detail.elt);});
