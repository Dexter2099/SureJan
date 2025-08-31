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

function showToast(message){
  const toast = document.createElement('div');
  toast.textContent = message;
  toast.style.position = 'fixed';
  toast.style.bottom = '1rem';
  toast.style.left = '50%';
  toast.style.transform = 'translateX(-50%)';
  toast.style.background = '#333';
  toast.style.color = '#fff';
  toast.style.padding = '0.5rem 1rem';
  toast.style.borderRadius = '4px';
  toast.style.zIndex = '1000';
  toast.style.opacity = '0';
  toast.style.transition = 'opacity 0.3s';
  document.body.appendChild(toast);
  requestAnimationFrame(()=>{toast.style.opacity='1';});
  setTimeout(()=>{toast.style.opacity='0';},2000);
  setTimeout(()=>{toast.remove();},2300);
}

function initCopyLinkButtons(root=document){
  root.querySelectorAll('.copy-link').forEach(btn=>{
    if(btn.dataset.ready) return;
    btn.dataset.ready = '1';
    btn.addEventListener('click',()=>{
      const link = btn.dataset.link;
      if(!link) return;
      navigator.clipboard.writeText(link).then(()=>{
        showToast('Link copied');
      });
    });
  });
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

function formatTimeAgo(seconds){
  if(seconds < 60) return seconds + 's';
  const minutes = Math.floor(seconds / 60);
  if(minutes < 60) return minutes + 'm';
  const hours = Math.floor(minutes / 60);
  if(hours < 24) return hours + 'h';
  const days = Math.floor(hours / 24);
  if(days < 30) return days + 'd';
  const months = Math.floor(days / 30);
  if(months < 12) return months + 'mo';
  const years = Math.floor(months / 12);
  return years + 'y';
}

function updateTimeAgo(root=document){
  root.querySelectorAll('time[data-ts]').forEach(el=>{
    const ts = parseInt(el.dataset.ts, 10);
    if(isNaN(ts)) return;
    const diff = Math.floor(Date.now()/1000 - ts);
    el.textContent = formatTimeAgo(diff);
    if(!el.getAttribute('title')){
      const d = new Date(ts*1000);
      const pad = n=>n.toString().padStart(2,'0');
      el.setAttribute('title',
        d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate())+' '+pad(d.getHours())+':'+pad(d.getMinutes())
      );
    }
  });
}

document.addEventListener('mouseup',handleSelection);
document.addEventListener('keyup',handleSelection);
document.addEventListener('selectionchange',handleSelection);
document.addEventListener('click',e=>{if(!e.target.classList.contains('quote-btn')) hideQuoteBubbles();});

document.addEventListener('DOMContentLoaded',()=>{
  initCommentCollapse();
  initQuoteButtons();
  initCopyLinkButtons();
  updateTimeAgo();
  setInterval(updateTimeAgo,60000);
});

document.body.addEventListener('htmx:afterSwap',e=>{
  initCommentCollapse(e.detail.elt);
  initQuoteButtons(e.detail.elt);
  initCopyLinkButtons(e.detail.elt);
  updateTimeAgo(e.detail.elt);
});
