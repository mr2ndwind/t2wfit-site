(function(){var W=__DATA__;var g=document.getElementById('wk-grid');if(!g)return;var f='all',q='',v=false;
var cards=[].slice.call(g.querySelectorAll('.wk')),btns=[].slice.call(document.querySelectorAll('#wk-filters button')),se=document.getElementById('wk-search'),vt=document.getElementById('wk-video'),em=document.getElementById('wk-empty');
function apply(){var n=0;cards.forEach(function(c){var ok=(f==='all'||c.dataset.tags.split(' ').indexOf(f)>-1)&&(!q||c.dataset.s.indexOf(q)>-1)&&(!v||c.dataset.v==='1');c.hidden=!ok;if(ok)n++});em.hidden=n>0}
btns.forEach(function(b){b.onclick=function(){btns.forEach(function(x){x.classList.remove('on')});b.classList.add('on');f=b.dataset.f;apply()}});
se.oninput=function(){q=se.value.trim().toLowerCase();apply()};vt.onchange=function(){v=vt.checked;apply()};
var d=document.getElementById('wk-dlg'),m=document.getElementById('wk-media');function $(i){return document.getElementById(i)}
function open(i){var w=W[i];$('wk-cat').textContent=w.cat;$('wk-name').textContent=w.name;$('wk-dur').textContent=w.dur;$('wk-lvl').textContent=w.level;$('wk-type').textContent=w.type;$('wk-eq').textContent=w.equip;
$('wk-ben').innerHTML=w.benefits.map(function(x){return '<li>'+x+'</li>'}).join('');var im=cards[i].querySelector('img').src;
m.innerHTML='<img src="'+im+'" alt="">'+(w.yt?'<button type="button" class="wk-playbtn" aria-label="Play preview">&#9654;</button>':'<div class="wk-nov">Video preview coming soon</div>');
var pb=m.querySelector('.wk-playbtn');if(pb)pb.onclick=function(){m.innerHTML='<iframe src="https://www.youtube-nocookie.com/embed/'+w.yt+'?autoplay=1&rel=0" title="'+w.name+' preview" allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen></iframe>'};
if(d.showModal)d.showModal();else d.setAttribute('open','')}
function shut(){m.innerHTML='';if(d.close)d.close();else d.removeAttribute('open')}
cards.forEach(function(c){c.onclick=function(){open(+c.dataset.i)};c.onkeydown=function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();open(+c.dataset.i)}}});
d.querySelector('.wk-x').onclick=shut;d.addEventListener('click',function(e){if(e.target===d)shut()});d.addEventListener('close',function(){m.innerHTML=''})})();
