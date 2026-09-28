/* split-kit — engine + biblioteca de ilustrações (padrão MARE).
   Uso: definir SCENES[] no index.html e chamar SplitKit.build({duration, scenes:SCENES}).
   Cada cena: {start,dur,layout:'default|reverse|stack',accent:'#hex',halo?,kick,headline,sub?,art:{type,...}}
   headline aceita **palavra** => vira acento (<b>). art.type = chave em ILLOS (abaixo). */
(function(){
  var DARK = "#07131f";

  // ---- helpers de ilustração ----
  function bars(a, dark, arrow){ // 3 barras subindo + seta opcional
    var s='<rect data-k="b1" x="96" y="252" width="72" height="76" rx="10" fill="'+a+'"/>'
      +'<rect data-k="b2" x="182" y="200" width="72" height="128" rx="10" fill="'+a+'"/>'
      +'<rect data-k="b3" x="268" y="146" width="72" height="182" rx="10" fill="'+a+'"/>';
    if(arrow) s+='<g data-k="arr"><path d="M112 214 L306 112" fill="none" stroke="'+(arrow)+'" stroke-width="13" stroke-linecap="round"/><path d="M274 104 L314 108 L300 146" fill="none" stroke="'+(arrow)+'" stroke-width="13" stroke-linecap="round" stroke-linejoin="round"/></g>';
    return s;
  }
  function barsSig(tl,g,q,u,at,arrow){
    g.set('#'+u+' [data-k=b1],#'+u+' [data-k=b2],#'+u+' [data-k=b3]',{scaleY:0,svgOrigin:"0 328"});
    tl.to('#'+u+' [data-k=b1]',{scaleY:1,duration:.28,ease:"back.out(1.4)"},q(at+.4));
    tl.to('#'+u+' [data-k=b2]',{scaleY:1,duration:.28,ease:"back.out(1.4)"},q(at+.58));
    tl.to('#'+u+' [data-k=b3]',{scaleY:1,duration:.28,ease:"back.out(1.4)"},q(at+.76));
    if(arrow){ g.set('#'+u+' [data-k=arr]',{opacity:0}); tl.fromTo('#'+u+' [data-k=arr]',{opacity:0,x:-16,y:16},{opacity:1,x:0,y:0,duration:.4,ease:"power3.out"},q(at+1.0)); }
  }
  function popSig(sel){ return function(tl,g,q,u,at){ tl.fromTo(sel(u),{scale:.55,svgOrigin:"216 210"},{scale:1,duration:.44,ease:"back.out(1.6)",immediateRender:false},q(at+.45)); }; }

  var ILLOS = {
    seal: { // medalha/selo com rótulo (ex.: CPRO-R, CPA)
      svg:function(a,u,o){ var t=(o.label||"SELO"); var fs=t.length>4?40:64;
        return '<path d="M170 300 l46 26 46 -26 v70 l-46 -22 -46 22 z" fill="#a5761a"/>'
        +'<g data-k="seal"><circle cx="216" cy="200" r="96" fill="'+a+'"/><circle cx="216" cy="200" r="78" fill="none" stroke="'+DARK+'" stroke-width="5" opacity=".5"/>'
        +'<text x="216" y="220" text-anchor="middle" textLength="'+(t.length>4?128:0)+'" lengthAdjust="spacingAndGlyphs" font-family="Black,Inter" font-weight="900" font-size="'+fs+'" fill="'+DARK+'">'+t+'</text></g>'; },
      sig:function(tl,g,q,u,at){ tl.fromTo('#'+u+' [data-k=seal]',{scale:.5,svgOrigin:"216 200"},{scale:1,duration:.5,ease:"back.out(1.7)",immediateRender:false},q(at+.45)); } },
    exam: { // folha de prova com checks
      svg:function(a,u){ return '<rect x="120" y="104" width="192" height="224" rx="16" fill="'+a+'"/>'
        +'<g data-k="ck" stroke="'+DARK+'" stroke-width="12" stroke-linecap="round" stroke-linejoin="round" fill="none"><path d="M150 158 l16 16 28 -32"/><path d="M150 214 l16 16 28 -32"/><path d="M150 270 l16 16 28 -32"/></g>'
        +'<g stroke="'+DARK+'" stroke-width="12" stroke-linecap="round"><line x1="212" y1="166" x2="288" y2="166"/><line x1="212" y1="222" x2="288" y2="222"/><line x1="212" y1="278" x2="288" y2="278"/></g>'; },
      sig:function(tl,g,q,u,at){ g.set('#'+u+' [data-k=ck] path',{opacity:0,x:-6}); tl.to('#'+u+' [data-k=ck] path',{opacity:1,x:0,duration:.26,ease:"power2.out",stagger:.14},q(at+.5)); } },
    download: { // seta de download + rótulo opcional
      svg:function(a,u,o){ var s='<g data-k="dl"><line x1="216" y1="120" x2="216" y2="244" stroke="'+a+'" stroke-width="20" stroke-linecap="round"/><path d="M172 204 L216 250 L260 204" fill="none" stroke="'+a+'" stroke-width="20" stroke-linecap="round" stroke-linejoin="round"/><rect x="132" y="278" width="168" height="26" rx="13" fill="'+a+'"/></g>';
        if(o.label) s+='<text x="216" y="300" text-anchor="middle" font-family="Black,Inter" font-weight="900" font-size="20" fill="'+DARK+'">'+o.label+'</text>'; return s; },
      sig:function(tl,g,q,u,at){ tl.fromTo('#'+u+' [data-k=dl]',{y:-16,opacity:0},{y:0,opacity:1,duration:.4,ease:"back.out(1.6)",immediateRender:false},q(at+.45)); tl.to('#'+u+' [data-k=dl]',{y:8,duration:.5,ease:"sine.inOut",yoyo:true,repeat:2},q(at+1.0)); } },
    chat: { svg:function(a,u){ return '<g data-k="c"><path d="M116 150 h200 a26 26 0 0 1 26 26 v92 a26 26 0 0 1 -26 26 h-96 l-58 46 v-46 h-46 a26 26 0 0 1 -26 -26 v-92 a26 26 0 0 1 26 -26 z" fill="'+a+'"/>'
        +'<circle data-k="d1" cx="166" cy="222" r="13" fill="'+DARK+'"/><circle data-k="d2" cx="216" cy="222" r="13" fill="'+DARK+'"/><circle data-k="d3" cx="266" cy="222" r="13" fill="'+DARK+'"/></g>'; },
      sig:function(tl,g,q,u,at){ tl.fromTo('#'+u+' [data-k=c]',{scale:.6,svgOrigin:"216 226"},{scale:1,duration:.42,ease:"back.out(1.6)",immediateRender:false},q(at+.45)); g.set('#'+u+' [data-k=d1],#'+u+' [data-k=d2],#'+u+' [data-k=d3]',{transformOrigin:"50% 50%"}); tl.to('#'+u+' [data-k=d1],#'+u+' [data-k=d2],#'+u+' [data-k=d3]',{scale:1.5,duration:.24,ease:"sine.inOut",yoyo:true,repeat:3,stagger:.1},q(at+.8)); } },
    button: { // botão + cursor (label = texto do botão)
      svg:function(a,u,o){ return '<rect data-k="btn" x="60" y="168" width="312" height="90" rx="22" fill="'+a+'"/>'
        +'<text data-k="txt" x="216" y="228" text-anchor="middle" font-family="Black,Inter" font-weight="900" font-size="44" fill="'+DARK+'">'+(o.label||"CLICAR")+'</text>'
        +'<path data-k="cur" d="M262 250 L262 326 L282 308 L296 340 L314 332 L300 301 L326 301 Z" fill="#f4f7f5" stroke="'+DARK+'" stroke-width="5" stroke-linejoin="round" opacity="0"/>'; },
      sig:function(tl,g,q,u,at){ tl.fromTo('#'+u+' [data-k=cur]',{opacity:0,x:40,y:40},{opacity:1,x:0,y:0,duration:.4,ease:"power3.out"},q(at+.5)); tl.to('#'+u+' [data-k=cur]',{y:9,duration:.1,yoyo:true,repeat:1,ease:"power2.in",overwrite:"auto"},q(at+1.0)); tl.to('#'+u+' [data-k=btn]',{attr:{y:174},duration:.1,yoyo:true,repeat:1,ease:"power2.in"},q(at+1.0)); tl.to('#'+u+' [data-k=txt]',{attr:{y:234},duration:.1,yoyo:true,repeat:1,ease:"power2.in"},q(at+1.0)); } },
    refresh: { svg:function(a,u){ return '<g data-k="r"><path d="M216 118 a82 82 0 1 1 -80 64" fill="none" stroke="'+a+'" stroke-width="22" stroke-linecap="round"/><path d="M216 94 l8 48 -50 -16 z" fill="'+a+'"/></g>'; },
      sig:function(tl,g,q,u,at){ tl.fromTo('#'+u+' [data-k=r]',{rotation:-170,opacity:0,svgOrigin:"216 200"},{rotation:0,opacity:1,duration:.5,ease:"power3.out",immediateRender:false},q(at+.45)); } },
    target: { svg:function(a,u,o){ var arrow=o.arrow||"#F5A623"; return '<g data-k="tgt"><circle cx="200" cy="216" r="104" fill="none" stroke="'+a+'" stroke-width="20"/><circle cx="200" cy="216" r="60" fill="none" stroke="'+a+'" stroke-width="20"/><circle cx="200" cy="216" r="18" fill="'+a+'"/></g>'
        +'<g data-k="arr"><line x1="300" y1="116" x2="212" y2="204" stroke="'+arrow+'" stroke-width="14" stroke-linecap="round"/><path d="M296 108 l20 4 -4 20" fill="none" stroke="'+arrow+'" stroke-width="14" stroke-linecap="round" stroke-linejoin="round"/></g>'; },
      sig:function(tl,g,q,u,at){ tl.fromTo('#'+u+' [data-k=tgt]',{scale:.6,svgOrigin:"200 216"},{scale:1,duration:.44,ease:"back.out(1.5)",immediateRender:false},q(at+.45)); tl.fromTo('#'+u+' [data-k=arr]',{x:80,y:-80,opacity:0},{x:0,y:0,opacity:1,duration:.4,ease:"power3.in",immediateRender:false},q(at+.95)); tl.to('#'+u+' [data-k=tgt]',{scale:1.08,svgOrigin:"200 216",duration:.12,ease:"power2.out",yoyo:true,repeat:1},q(at+1.35)); } },
    gradcap: { svg:function(a,u){ return '<g data-k="cap"><path d="M216 132 L346 182 L216 232 L86 182 Z" fill="'+a+'"/><path d="M146 206 v46 c0 26 140 26 140 0 v-46" fill="none" stroke="'+a+'" stroke-width="16"/><line data-k="tas" x1="330" y1="188" x2="330" y2="268" stroke="'+a+'" stroke-width="8" stroke-linecap="round"/><circle data-k="tasb" cx="330" cy="274" r="12" fill="'+a+'"/></g>'; },
      sig:function(tl,g,q,u,at){ tl.fromTo('#'+u+' [data-k=cap]',{y:-40,opacity:0},{y:0,opacity:1,duration:.5,ease:"back.out(1.5)",immediateRender:false},q(at+.45)); tl.fromTo('#'+u+' [data-k=tas]',{rotation:-18,svgOrigin:"330 188"},{rotation:0,duration:.5,ease:"elastic.out(1,0.4)"},q(at+.9)); } },
    shield: { svg:function(a,u){ return '<g data-k="sh"><path d="M216 108 l104 40 v78 c0 74 -58 124 -104 142 c-46 -18 -104 -68 -104 -142 v-78 z" fill="'+a+'"/><path data-k="ck" d="M172 214 l30 32 60 -70" fill="none" stroke="'+DARK+'" stroke-width="18" stroke-linecap="round" stroke-linejoin="round"/></g>'; },
      sig:function(tl,g,q,u,at){ g.set('#'+u+' [data-k=ck]',{strokeDasharray:"150",strokeDashoffset:"150"}); tl.fromTo('#'+u+' [data-k=sh]',{scale:.6,svgOrigin:"216 220"},{scale:1,duration:.4,ease:"back.out(1.5)",immediateRender:false},q(at+.45)); tl.to('#'+u+' [data-k=ck]',{strokeDashoffset:0,duration:.4,ease:"power2.out"},q(at+.85)); } },
    lupa: { svg:function(a,u){ return '<g data-k="doc"><rect x="112" y="112" width="150" height="200" rx="12" fill="#155e6b"/><rect x="136" y="146" width="102" height="12" rx="6" fill="'+a+'" opacity=".7"/><rect x="136" y="176" width="102" height="12" rx="6" fill="'+a+'" opacity=".7"/><rect x="136" y="206" width="64" height="12" rx="6" fill="'+a+'" opacity=".7"/></g>'
        +'<g data-k="lp"><circle cx="258" cy="232" r="62" fill="'+DARK+'" fill-opacity=".35" stroke="'+a+'" stroke-width="14"/><line x1="300" y1="276" x2="340" y2="316" stroke="'+a+'" stroke-width="20" stroke-linecap="round"/></g>'; },
      sig:function(tl,g,q,u,at){ tl.fromTo('#'+u+' [data-k=doc]',{scale:.6,svgOrigin:"187 212"},{scale:1,duration:.36,ease:"back.out(1.5)",immediateRender:false},q(at+.45)); tl.fromTo('#'+u+' [data-k=lp]',{scale:.5,svgOrigin:"258 232",opacity:0},{scale:1,opacity:1,duration:.36,ease:"back.out(1.7)",immediateRender:false},q(at+.7)); tl.to('#'+u+' [data-k=lp]',{x:-14,y:-10,duration:.5,ease:"sine.inOut",yoyo:true,repeat:1},q(at+1.1)); } },
    gift: { svg:function(a,u){ return '<g data-k="gf"><rect x="120" y="200" width="192" height="140" rx="12" fill="'+a+'"/><rect x="108" y="168" width="216" height="44" rx="10" fill="'+a+'" opacity=".8"/><rect x="204" y="168" width="24" height="172" fill="'+DARK+'"/><path data-k="bl" d="M216 168 q-46 -50 -70 -18 q-14 26 70 18 z" fill="#F5A623"/><path data-k="br" d="M216 168 q46 -50 70 -18 q14 26 -70 18 z" fill="#F5A623"/></g>'; },
      sig:function(tl,g,q,u,at){ tl.fromTo('#'+u+' [data-k=gf]',{scale:.6,svgOrigin:"216 260"},{scale:1,duration:.42,ease:"back.out(1.6)",immediateRender:false},q(at+.45)); tl.fromTo('#'+u+' [data-k=bl],#'+u+' [data-k=br]',{scale:0,svgOrigin:"216 150"},{scale:1,duration:.4,ease:"back.out(2)",immediateRender:false},q(at+.8)); } },
    bars: { svg:function(a,u,o){ return bars(a,DARK,o.arrow); }, sig:function(tl,g,q,u,at,o){ barsSig(tl,g,q,u,at,o.arrow); } },
    question: { svg:function(a,u){ return '<text data-k="q" x="216" y="312" text-anchor="middle" font-family="Black,Inter" font-weight="900" font-size="300" fill="'+a+'">?</text>'; },
      sig:function(tl,g,q,u,at){ g.set('#'+u+' [data-k=q]',{scale:.4,opacity:0,svgOrigin:"216 216"}); tl.to('#'+u+' [data-k=q]',{scale:1,opacity:1,duration:.36,ease:"back.out(1.8)"},q(at+.45)); tl.to('#'+u+' [data-k=q]',{scale:1.1,svgOrigin:"216 216",duration:.22,ease:"sine.inOut",yoyo:true,repeat:1},q(at+1.0)); } },
    person: { svg:function(a,u,o){ var s='<g data-k="p"><circle cx="216" cy="168" r="52" fill="'+a+'"/><path d="M144 306 a72 80 0 0 1 144 0 z" fill="'+a+'"/>';
        if(o.ring) s+='<circle data-k="ring" cx="216" cy="200" r="92" fill="none" stroke="'+(o.ring)+'" stroke-width="8" stroke-dasharray="14 12"/>'; return s+'</g>'; },
      sig:function(tl,g,q,u,at,o){ tl.fromTo('#'+u+' [data-k=p]',{scale:.6,svgOrigin:"216 200"},{scale:1,duration:.4,ease:"back.out(1.6)",immediateRender:false},q(at+.45)); if(o.ring) tl.fromTo('#'+u+' [data-k=ring]',{rotation:-40,opacity:0,svgOrigin:"216 200"},{rotation:0,opacity:1,duration:.5,ease:"power3.out"},q(at+.8)); } },
    price0: { svg:function(a,u){ return '<circle cx="216" cy="200" r="128" fill="'+a+'"/><text x="216" y="222" text-anchor="middle" font-family="Black,Inter" font-weight="900" font-size="86" fill="'+DARK+'">R$0</text><line data-k="sl" x1="112" y1="300" x2="320" y2="100" stroke="#f4f7f5" stroke-width="16" stroke-linecap="round"/>'; },
      sig:function(tl,g,q,u,at){ g.set('#'+u+' [data-k=sl]',{scaleX:0,transformOrigin:"50% 50%"}); tl.fromTo('#'+u+' circle',{scale:.6,svgOrigin:"216 200"},{scale:1,duration:.4,ease:"back.out(1.6)"},q(at+.45)); tl.to('#'+u+' [data-k=sl]',{scaleX:1,duration:.34,ease:"power2.out"},q(at+.85)); } },
    cue: { svg:function(a,u){ return '<g data-k="burst" opacity="0" stroke="'+a+'" stroke-width="8" stroke-linecap="round"><line x1="150" y1="150" x2="118" y2="118"/><line x1="150" y1="282" x2="118" y2="314"/><line x1="92" y1="216" x2="52" y2="216"/><line x1="188" y1="96" x2="172" y2="56"/><line x1="188" y1="336" x2="172" y2="376"/></g>'
        +'<g data-k="ball"><circle cx="180" cy="216" r="74" fill="#0b1d2b" stroke="'+a+'" stroke-width="11"/><circle cx="180" cy="216" r="30" fill="none" stroke="'+a+'" stroke-width="8"/></g>'
        +'<line data-k="cue" x1="256" y1="172" x2="398" y2="66" stroke="'+a+'" stroke-width="18" stroke-linecap="round"/>'; },
      sig:function(tl,g,q,u,at){ g.set('#'+u+' [data-k=burst]',{opacity:0,scale:.4,svgOrigin:"180 216"}); tl.fromTo('#'+u+' [data-k=cue]',{x:26,y:-18},{x:0,y:0,duration:.4,ease:"power3.in"},q(at+.6)); tl.to('#'+u+' [data-k=ball]',{x:-9,duration:.14,ease:"power2.out",yoyo:true,repeat:1},q(at+.95)); tl.fromTo('#'+u+' [data-k=burst]',{opacity:.95,scale:.4,svgOrigin:"180 216"},{opacity:0,scale:1.7,duration:.55,ease:"power1.out",immediateRender:false},q(at+.97)); } },
    num: { // count-up: art:{type:'num', to:120, prefix:'+', suffix:'MIL'}
      svg:function(a,u,o){ return '<text data-k="n" x="216" y="216" text-anchor="middle" font-family="Black,Inter" font-weight="900" font-size="150" fill="'+a+'">'+(o.prefix||'')+'0</text>'
        +(o.suffix?'<text x="216" y="300" text-anchor="middle" font-family="Black,Inter" font-weight="900" font-size="64" letter-spacing="10" fill="'+a+'">'+o.suffix+'</text>':''); },
      sig:function(tl,g,q,u,at,o){ var st={v:0},to=o.to||100,pre=o.prefix||''; tl.to(st,{v:to,duration:1.4,ease:"power2.out",onUpdate:function(){var e=document.querySelector('#'+u+' [data-k=n]'); if(e) e.textContent=pre+Math.round(st.v);}},q(at+.45)); } },
    arms: { // braços abertos + coração (correr pro abraço)
      svg:function(a,u){ return '<g data-k="h"><path d="M216 150 c-16 -30 -74 -26 -74 18 c0 34 54 62 74 74 c20 -12 74 -40 74 -74 c0 -44 -58 -48 -74 -18 z" fill="#ff5c67"/></g>'
        +'<g stroke="'+a+'" stroke-width="20" stroke-linecap="round" fill="none"><circle cx="216" cy="250" r="30" fill="'+a+'" stroke="none"/><path d="M216 280 v56"/><path data-k="al" d="M216 300 L150 250"/><path data-k="ar" d="M216 300 L282 250"/></g>'; },
      sig:function(tl,g,q,u,at){ g.set('#'+u+' [data-k=h]',{scale:0,svgOrigin:"216 200"}); tl.fromTo('#'+u+' [data-k=al]',{rotation:30,svgOrigin:"216 300"},{rotation:0,duration:.5,ease:"back.out(1.6)"},q(at+.5)); tl.fromTo('#'+u+' [data-k=ar]',{rotation:-30,svgOrigin:"216 300"},{rotation:0,duration:.5,ease:"back.out(1.6)"},q(at+.5)); tl.to('#'+u+' [data-k=h]',{scale:1,duration:.5,ease:"back.out(1.8)"},q(at+.9)); tl.to('#'+u+' [data-k=h]',{scale:1.14,svgOrigin:"216 200",duration:.34,ease:"sine.inOut",yoyo:true,repeat:3},q(at+1.5)); } },
    star: { svg:function(a,u){ return '<path data-k="st" d="M216 96 l38 78 86 12 -62 60 15 86 -77 -41 -77 41 15 -86 -62 -60 86 -12 z" fill="'+a+'"/>'; },
      sig:function(tl,g,q,u,at){ tl.fromTo('#'+u+' [data-k=st]',{scale:0,rotation:-60,svgOrigin:"216 200"},{scale:1,rotation:0,duration:.5,ease:"back.out(1.7)",immediateRender:false},q(at+.45)); } }
  };

  function hl(s){ return String(s||"").replace(/\*\*(.+?)\*\*/g,'<b>$1</b>'); }

  window.SplitKit = {
    ILLOS: ILLOS,
    build: function(opts){
      var doc=document, bottom=doc.getElementById('bottom'), g=window.gsap;
      var q=function(t){return Math.round(t*30)/30;};
      var scenes=opts.scenes;
      scenes.forEach(function(sc,i){
        var id=sc.id||('s'+(i+1)); sc.id=id;
        var halo=sc.halo||(sc.accent+'30');
        var cls='scene clip'+(sc.layout==='reverse'?' reverse':(sc.layout==='stack'?' stack':''));
        var art=sc.art||{}; var illo=ILLOS[art.type];
        var inner = illo ? illo.svg(sc.accent,id,art) : '';
        var hasFO = inner.indexOf('foreignObject')>-1;
        var illsvg = illo ? '<svg width="432" height="432" viewBox="0 0 432 432">'+inner+'</svg>' : '';
        var illClass = (art.center||hasFO) ? 'ill illf' : 'ill';
        var sec=doc.createElement('section');
        sec.className=cls; sec.id=id;
        sec.setAttribute('data-start',sc.start); sec.setAttribute('data-duration',sc.dur); sec.setAttribute('data-track-index','2');
        sec.setAttribute('style','--a:'+sc.accent+';--halo:'+halo);
        sec.innerHTML='<div class="atmo"></div><div class="grid"></div><div class="grain"></div>'
          +'<div class="layout"><div class="art"><div class="disc"></div><div class="'+illClass+'">'+illsvg+'</div></div>'
          +'<div class="copy"><div class="kick">'+(sc.kick||'')+'</div><div class="headline">'+hl(sc.headline)+'</div>'
          +'<div class="sub">'+(sc.sub||'')+'</div><div class="statline"><span></span><span></span><span></span></div></div></div>'
          +'<div class="spark sp1"></div><div class="spark sp2"></div><div class="spark sp3"></div><div class="footer"><i></i></div>';
        bottom.appendChild(sec);
      });
      // headline: quebra em palavras (span.word) + <b> vira .word
      doc.querySelectorAll('.headline').forEach(function(h){ [].slice.call(h.childNodes).forEach(function(n){
        if(n.nodeType===3&&n.textContent.trim()){ var f=doc.createDocumentFragment(); n.textContent.split(/(\s+)/).forEach(function(p){ if(!p.trim()) return f.appendChild(doc.createTextNode(p)); var s=doc.createElement('span'); s.className='word'; s.textContent=p; f.appendChild(s); }); h.replaceChild(f,n); }
        else if(n.nodeName==='B'){ n.classList.add('word'); }
      }); });
      var tl=g.timeline({paused:true});
      function enter(id,at){
        var node=doc.querySelector(id),rev=node.classList.contains('reverse'),stack=node.classList.contains('stack'),dir=rev?36:-36;
        tl.fromTo(id+' .art',{opacity:0,x:stack?0:dir,y:stack?-26:0,scale:.92},{opacity:1,x:0,y:0,scale:1,duration:.5,ease:"power3.out"},q(at+.04));
        tl.fromTo(id+' .disc',{opacity:0,scale:.76},{opacity:1,scale:1,duration:.46,ease:"back.out(1.35)"},q(at+.08));
        tl.fromTo(id+' .kick',{opacity:0,x:stack?0:(rev?-24:24),y:stack?14:0},{opacity:1,x:0,y:0,duration:.32,ease:"power3.out"},q(at+.12));
        tl.fromTo(id+' .headline .word',{opacity:0,y:24},{opacity:1,y:0,duration:.4,ease:"power4.out",stagger:.05},q(at+.22));
        tl.fromTo(id+' .sub',{opacity:0,y:14},{opacity:1,y:0,duration:.36,ease:"power3.out"},q(at+.5));
        tl.fromTo(id+' .footer i',{scaleX:0},{scaleX:1,duration:.7,ease:"power2.inOut"},q(at+.16));
        tl.fromTo(id+' .statline span',{scaleX:0,transformOrigin:"0% 50%"},{scaleX:1,duration:.3,ease:"power2.out",stagger:.07},q(at+.66));
        tl.fromTo(id+' .spark',{opacity:0,scale:.3},{opacity:.72,scale:1,duration:.28,ease:"back.out(2)",stagger:.07},q(at+.58));
      }
      scenes.forEach(function(sc){ enter('#'+sc.id,sc.start); });
      scenes.forEach(function(sc){ var a=sc.start+0.9,b=sc.start+sc.dur-.3,n=Math.max(1,Math.floor((b-a)/1.2)-1); if(b>a) tl.to('#'+sc.id+' .art',{y:-6,duration:1.2,ease:"sine.inOut",yoyo:true,repeat:n},q(a)); });
      scenes.forEach(function(sc){ var illo=ILLOS[(sc.art||{}).type]; if(illo&&illo.sig) illo.sig(tl,g,q,sc.id,sc.start,sc.art||{}); });
      window.__timelines=window.__timelines||{}; window.__timelines.split=tl;
      return tl;
    }
  };
})();
