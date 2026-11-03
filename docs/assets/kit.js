/* Reel kits: shared behaviour for every page (copy buttons, share, tabs, home search). */
(function(){
  var PAGE=document.body.getAttribute('data-url')||location.href;
  var TITLE=document.title;
  var toastEl=document.getElementById('toast'),tt;
  function toast(m){if(!toastEl)return;toastEl.textContent=m;toastEl.classList.add('show');clearTimeout(tt);tt=setTimeout(function(){toastEl.classList.remove('show');},1700);}
  function selectEl(el){var r=document.createRange();r.selectNodeContents(el);var s=window.getSelection();s.removeAllRanges();s.addRange(r);}
  function legacyCopy(text){
    var ta=document.createElement('textarea');ta.value=text;ta.setAttribute('readonly','');ta.style.position='fixed';ta.style.opacity='0';
    document.body.appendChild(ta);ta.select();ta.setSelectionRange(0,text.length);var ok=false;try{ok=document.execCommand('copy');}catch(e){}
    document.body.removeChild(ta);return ok;
  }
  function copy(text,btn,el,msg){
    function ok(){toast(msg||'Copied');if(!btn)return;var keep=btn.classList.contains('fix');
      if(!keep){btn.dataset.orig=btn.dataset.orig||btn.textContent;btn.textContent='Copied ✓';}
      btn.classList.add('done');setTimeout(function(){btn.classList.remove('done');if(!keep)btn.textContent=btn.dataset.orig;},1500);}
    function bad(){if(legacyCopy(text)){ok();return;}if(el)selectEl(el);toast('Press and hold to copy');}
    if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(text).then(ok,bad);}else{bad();}
  }
  document.querySelectorAll('[data-copy],[data-copy-target]').forEach(function(b){
    b.addEventListener('click',function(){
      var el=b.dataset.copyTarget?document.getElementById(b.dataset.copyTarget):null;
      copy(b.dataset.copy||(el?el.innerText.trim():''),b,el);
    });
  });
  document.querySelectorAll('.more').forEach(function(b){
    b.addEventListener('click',function(){var c=b.closest('.card');c.classList.toggle('open');b.textContent=c.classList.contains('open')?'Show less':'Show full prompt';});
  });
  document.querySelectorAll('[data-share]').forEach(function(b){
    b.addEventListener('click',function(){
      var text=b.dataset.share||TITLE;
      var fallback=function(){copy(PAGE,null,null,'Link copied. Paste it wherever you like');};
      if(navigator.share){navigator.share({title:TITLE,text:text,url:PAGE}).catch(function(e){if(e&&e.name!=='AbortError')fallback();});}
      else{fallback();}
    });
  });
  // active tab follows the section in view
  var tabs=[].slice.call(document.querySelectorAll('.tabs a[href^="#"]')),lock=0;
  function setTab(h){tabs.forEach(function(t){var on=t.getAttribute('href')===h;t.classList.toggle('on',on);if(on&&t.scrollIntoView)t.scrollIntoView({block:'nearest',inline:'center'});});}
  tabs.forEach(function(t){t.addEventListener('click',function(){setTab(t.getAttribute('href'));lock=Date.now()+1200;});});
  if(tabs.length&&'IntersectionObserver' in window){
    var io=new IntersectionObserver(function(es){if(Date.now()<lock)return;es.forEach(function(e){if(e.isIntersecting)setTab('#'+e.target.id);});},{rootMargin:'-45% 0px -50% 0px'});
    document.querySelectorAll('main section[id]').forEach(function(s){io.observe(s);});
  }
  // home page: type the keyword from the Reel
  var q=document.getElementById('q');
  if(q){
    var cards=[].slice.call(document.querySelectorAll('.list li')),none=document.getElementById('none');
    function norm(s){return (s||'').toUpperCase().replace(/[^A-Z0-9]/g,'');}
    function filter(){
      var v=norm(q.value),shown=0;
      cards.forEach(function(li){var hit=!v||norm(li.dataset.kw).indexOf(v)===0||norm(li.dataset.text).indexOf(v)>-1;li.hidden=!hit;if(hit)shown++;});
      if(none)none.hidden=shown>0;
    }
    q.addEventListener('input',filter);
    q.addEventListener('keydown',function(e){
      if(e.key!=='Enter')return;var v=norm(q.value);
      var exact=cards.filter(function(li){return norm(li.dataset.kw)===v;})[0]||cards.filter(function(li){return !li.hidden;})[0];
      if(exact){location.href=exact.querySelector('a').getAttribute('href');}
    });
    // links like reel-kits/#EDITOR jump straight to that kit
    var h=norm(decodeURIComponent(location.hash.slice(1)));
    if(h){var m=cards.filter(function(li){return norm(li.dataset.kw)===h;})[0];if(m){location.replace(m.querySelector('a').getAttribute('href'));}else{q.value=h;filter();}}
  }
})();
