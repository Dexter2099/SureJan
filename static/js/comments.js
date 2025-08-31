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

document.addEventListener('DOMContentLoaded',()=>{initCommentCollapse();});

document.body.addEventListener('htmx:afterSwap',e=>{initCommentCollapse(e.detail.elt);});
