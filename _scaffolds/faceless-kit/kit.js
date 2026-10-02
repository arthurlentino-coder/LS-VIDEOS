/* faceless-kit — engine dirigida por config. window.FacelessKit.build({duration, scenes, cues}).
   Cada cena de SCENES: { type, start, end, eb, ebc, hl, ...params, ...anchors }.
   Padrão de animação: esconder no init (gsap.set) + revelar só com .to (nada vaza).
   B-roll: declarar os <video class="clip"> no template (nível root); a cena 'broll' cuida da grade+lower-third. */
window.FacelessKit = (function(){
  var G = window.gsap;
  function q(r,s){ return r.querySelector(s); }
  function qa(r,s){ return Array.prototype.slice.call(r.querySelectorAll(s)); }
  function at(s,k,def){ return (s[k]!=null)?s[k]:def; }

  function ehHtml(s){ return "<div class='eb "+(s.ebc||'')+"'>"+(s.eb||'')+"</div><div class='hl'>"+(s.hl||'')+"</div>"; }
  function ehInit(tl,r,s){
    G.set(qa(r,'.eb,.hl'),{opacity:0,x:-24});
    if(q(r,'.eb')) tl.to(q(r,'.eb'),{opacity:1,x:0,duration:.32,ease:'power3.out'}, at(s,'ebAt',s.start+0.15));
    if(q(r,'.hl')) tl.to(q(r,'.hl'),{opacity:1,x:0,duration:.36,ease:'power3.out'}, at(s,'hlAt',s.start+0.27));
  }
  function pop(tl,sel,a){ tl.to(sel,{opacity:1,scale:1,duration:.42,ease:'back.out(1.7)'},a); }
  function up(tl,sel,a){ tl.to(sel,{opacity:1,y:0,duration:.4,ease:'back.out(1.5)'},a); }

  var TYPES = {
    headline: { html:ehHtml, init:ehInit },

    poster: { // eb+hl (topo) + ILLO do split-kit com ANIMAÇÃO INTERNA (padrão) + anel ambiente
      html:function(s){
        var acc=s.acc||({ye:'#fbbf24',cy:'#22d3ee',gr:'#34d399',co:'#ff5c67'}[s.ebc]||'#22d3ee');
        var ill='';
        if(s.illo && window.SplitKit && SplitKit.ILLOS[s.illo]){ var uid=s.id+'ill'; s._uid=uid;
          ill="<svg id='"+uid+"' class='fillo' width='432' height='432' viewBox='0 0 432 432'>"+SplitKit.ILLOS[s.illo].svg(acc,uid,s.illoOpts||{})+"</svg>"; }
        return ehHtml(s)+"<div class='fring'></div><div class='fhero'>"+ill+"</div>"+(s.fsub?"<div class='fsub'>"+s.fsub+"</div>":"");
      },
      init:function(tl,r,s){ ehInit(tl,r,s);
        var ha=at(s,'heroAt',s.start+.5);
        var ring=q(r,'.fring');
        if(ring){ G.set(ring,{opacity:0,scale:.7,xPercent:-50,rotation:0,transformOrigin:'50% 50%'});
          tl.to(ring,{opacity:.4,scale:1,duration:.9,ease:'power2.out'},s.start+.3);
          tl.to(ring,{rotation:360,duration:20,ease:'none',repeat:-1},s.start+.3); }           // ambiente girando (não é o ícone)
        var h=q(r,'.fhero');
        if(h){ G.set(h,{opacity:0,xPercent:-50,transformOrigin:'50% 50%'});
          tl.set(h,{opacity:1},ha);   // aparece instantâneo — sem flash do estado final
          // ANIMAÇÃO INTERNA do ícone (padrão split-kit). sig antecipado -.45 pra o reveal cair EM ha (a entrada é do próprio sig)
          if(s.illo && window.SplitKit && SplitKit.ILLOS[s.illo]){
            var qz=function(t){return Math.round(t*30)/30;};
            SplitKit.ILLOS[s.illo].sig(tl, G, qz, s._uid, ha-0.45, s.illoOpts||{}); }
          tl.to(h,{y:'-=12',duration:2.6,yoyo:true,repeat:-1,ease:'sine.inOut'},ha+1.6); }      // idle sutil (secundário)
        if(q(r,'.hl')) tl.to(q(r,'.hl'),{y:'+=10',duration:3.6,yoyo:true,repeat:-1,ease:'sine.inOut'},s.start+.7);
        var fs=q(r,'.fsub');
        if(fs){ G.set(fs,{opacity:0,y:22}); tl.to(fs,{opacity:1,y:0,duration:.4,ease:'back.out(1.4)'},at(s,'subAt',ha+.5)); }
      } },

    isoladas: {
      html:function(s){ var it=s.items||["CPA","CPRO-I","CPRO-R","CFP"];
        return ehHtml(s)+it.map(function(t,i){return "<div class='badge b"+(i+1)+"'><span class='bt'>"+t+"</span></div>";}).join(""); },
      init:function(tl,r,s){ ehInit(tl,r,s); G.set(qa(r,'.badge'),{opacity:0,scale:.6,transformOrigin:'50% 50%'});
        qa(r,'.badge').forEach(function(b,i){ pop(tl,b, at(s,'heroAt',s.start+.7)+i*at(s,'stagger',.4)); }); }
    },

    connect: {
      html:function(s){ var it=s.items||["CPA","CPRO-I","CPRO-R","CFP"];
        return ehHtml(s)+it.map(function(t,i){return "<div class='badge b"+(i+1)+"'><span class='bt' style='color:#22d3ee'>"+t+"</span></div>";}).join("")
          +"<svg class='linksvg'><path class='lkp' d='M340,830 L740,830 L340,1090 L740,1090 L340,830' fill='none' stroke='#34d399' stroke-width='6' stroke-dasharray='1900' stroke-dashoffset='1900' opacity='0'/></svg>"; },
      init:function(tl,r,s){ ehInit(tl,r,s); G.set(qa(r,'.badge'),{opacity:0,scale:.6,transformOrigin:'50% 50%'}); G.set(q(r,'.lkp'),{opacity:0,strokeDashoffset:2800});
        qa(r,'.badge').forEach(function(b,i){ pop(tl,b, at(s,'heroAt',s.start+.7)+i*.3); });
        var la=at(s,'linkAt',s.start+3.5); tl.to(q(r,'.lkp'),{opacity:1,duration:.01},la); tl.to(q(r,'.lkp'),{strokeDashoffset:0,duration:2.0,ease:'power2.inOut'},la); }
    },

    grid: {
      html:function(s){ var it=s.items||["CPA","CPRO-I","CPRO-R","CFP"]; var h=ehHtml(s)+"<div class='grid'>"+it.map(function(t){return "<div class='g'>"+t+"</div>";}).join("")+"</div>";
        if(s.futbar) h+="<div class='futbar'>"+s.futbar+"</div>"; if(s.seal) h+="<div class='seal'><span class='inf'>∞</span><span class='lb'>"+s.seal+"</span></div>"; return h; },
      init:function(tl,r,s){ ehInit(tl,r,s); G.set(qa(r,'.g'),{opacity:0,scale:.7,transformOrigin:'50% 50%'});
        tl.to(qa(r,'.g'),{opacity:1,scale:1,duration:.4,ease:'back.out(1.6)',stagger:at(s,'stagger',.16)}, at(s,'heroAt',s.start+1.1));
        if(q(r,'.futbar')){ G.set(q(r,'.futbar'),{opacity:0,y:18}); up(tl,q(r,'.futbar'), at(s,'futAt',s.start+3.5)); }
        if(q(r,'.seal')){ G.set(q(r,'.seal'),{opacity:0,scale:.6,transformOrigin:'50% 50%'}); pop(tl,q(r,'.seal'), at(s,'sealAt',s.end?s.end-1.4:s.start+5)); } }
    },

    cost: {
      html:function(s){ var it=s.items||[["Certificação 1","R$ 297"],["Certificação 2","R$ 397"],["Certificação 3","R$ 497"]];
        return ehHtml(s)+it.map(function(c,i){return "<div class='cc cc"+(i+1)+"'><span class='t'>"+c[0]+"</span><span class='v'>"+c[1]+"</span></div>";}).join("")
          +"<div class='total'><span class='k'>"+(s.totalLabel||"GASTANDO SEMPRE +")+"</span><span class='n' id='"+s.id+"tot'>R$ 0</span></div>"; },
      init:function(tl,r,s){ ehInit(tl,r,s); G.set(qa(r,'.cc'),{opacity:0,y:22}); G.set(q(r,'.total'),{opacity:0});
        qa(r,'.cc').forEach(function(c,i){ up(tl,c, at(s,'heroAt',s.start+1.0)+i*1.1); });
        var ca=at(s,'countAt',s.start+3.0); tl.to(q(r,'.total'),{opacity:1,duration:.3},ca-.1);
        var tot=q(r,'.total .n'), target=s.total||1191;
        tl.to({v:0},{v:target,duration:1.5,ease:'power1.out',onUpdate:function(){tot.textContent='R$ '+Math.round(this.targets()[0].v);}},ca); }
    },

    flatline: {
      html:function(s){ return ehHtml(s)
        +"<div class='flchart'><svg viewBox='0 0 900 640'><line x1='40' y1='600' x2='880' y2='600' stroke='#4b6b7d' stroke-width='3'/><line x1='40' y1='600' x2='40' y2='40' stroke='#4b6b7d' stroke-width='3'/><polyline class='fline' points='40,560 200,470 360,360 520,250 680,250 880,250' fill='none' stroke='#22d3ee' stroke-width='12' stroke-linecap='round' stroke-linejoin='round' stroke-dasharray='1200' stroke-dashoffset='1200'/></svg></div>"
        +"<div class='wall'></div><div class='stopx'>✕</div>"; },
      init:function(tl,r,s){ ehInit(tl,r,s); G.set(q(r,'.fline'),{strokeDashoffset:1200}); G.set(q(r,'.wall'),{opacity:0,scaleY:0,transformOrigin:'50% 100%'}); G.set(q(r,'.stopx'),{opacity:0,scale:.6,transformOrigin:'50% 50%'});
        tl.to(q(r,'.fline'),{strokeDashoffset:0,duration:4.4,ease:'power1.inOut'}, at(s,'heroAt',s.start+.7));
        var wa=at(s,'stopAt',s.start+5.6); tl.to(q(r,'.wall'),{opacity:1,scaleY:1,duration:.5,ease:'power3.out'},wa); pop(tl,q(r,'.stopx'),wa+.4); }
    },

    stopdate: {
      html:function(s){ return ehHtml(s)+"<div class='stopc'>✕</div><div class='datebig'>"+(s.date||"14 <span>SET</span>")+"</div>"; },
      init:function(tl,r,s){ ehInit(tl,r,s); G.set(q(r,'.stopc'),{opacity:0,scale:.5,transformOrigin:'50% 50%'}); G.set(q(r,'.datebig'),{opacity:0,y:16});
        pop(tl,q(r,'.stopc'), at(s,'heroAt',s.start+.4)); up(tl,q(r,'.datebig'), at(s,'dateAt',s.start+1.0)); }
    },

    lock: {
      html:function(s){ return ehHtml(s)+"<div class='lock'><div class='ic'>"+(s.ic||"🔒")+"</div><div class='lb'>"+(s.lockLabel||"VOCÊ NÃO TEM")+"</div></div>"; },
      init:function(tl,r,s){ ehInit(tl,r,s); G.set(q(r,'.lock'),{opacity:0,scale:.6,transformOrigin:'50% 50%'}); pop(tl,q(r,'.lock'), at(s,'heroAt',s.start+1.4)); }
    },

    vaga: {
      html:function(s){ return ehHtml(s)+"<div class='vaga'><div class='role'>"+(s.role||"PROMOÇÃO")+"</div><div class='sub'>"+(s.sub||"a vaga que você sonhou")+"</div><div class='up'>"+(s.upline||"↑ o próximo passo da carreira")+"</div></div>"; },
      init:function(tl,r,s){ ehInit(tl,r,s); G.set(q(r,'.vaga'),{opacity:0,y:22}); up(tl,q(r,'.vaga'), at(s,'heroAt',s.start+1.2)); }
    },

    cta: { // datecard e live são OPCIONAIS (só entram se s.date / s.live); botão sempre
      html:function(s){ var h=ehHtml(s);
        if(s.date) h+="<div class='datecard'><div class='d'>"+s.date+"</div><div class='h'>"+(s.dateSub||"")+"</div></div>";
        if(s.live) h+="<div class='live'><span class='pl'></span><span class='lt'>"+s.live+"</span></div>";
        h+="<div class='ctabtn'"+(!s.date&&!s.live?" style='top:760px'":"")+">"+(s.btn||"CLICA AQUI 👇")+"</div>"; return h; },
      init:function(tl,r,s){ ehInit(tl,r,s);
        if(q(r,'.datecard')){ G.set(q(r,'.datecard'),{opacity:0,y:22}); up(tl,q(r,'.datecard'), at(s,'dateAt',s.start+.7)); }
        if(q(r,'.live')){ G.set(q(r,'.live'),{opacity:0,y:22}); up(tl,q(r,'.live'), at(s,'liveAt',s.start+3.5)); }
        G.set(q(r,'.ctabtn'),{opacity:0,scale:.6,transformOrigin:'50% 50%'});
        var ba=at(s,'btnAt',s.start+(s.date||s.live?8:.6)); pop(tl,q(r,'.ctabtn'),ba); tl.to(q(r,'.ctabtn'),{scale:1.06,duration:.7,yoyo:true,repeat:-1,ease:'sine.inOut',transformOrigin:'50% 50%'},ba+.6); }
    },

    broll: { // video declarado no template; aqui só grade + lower-third
      html:function(s){ return "<div class='lt "+(s.ltc||'')+"'><div class='bar'></div><div class='box'><div class='t'>"+(s.lt||'')+"</div></div></div>"; },
      init:function(tl,r,s){ G.set(q(r,'.lt .bar'),{scaleX:0}); G.set(q(r,'.lt .box'),{opacity:0,x:-20});
        var a=at(s,'ltAt',s.start+.3); tl.to(q(r,'.lt .bar'),{scaleX:1,duration:.4,ease:'power3.out'},a); tl.to(q(r,'.lt .box'),{opacity:1,x:0,duration:.4,ease:'back.out(1.5)'},a+.12); }
    },

    offer: { // card positivo (oferta/download) — verde/ciano, opcional selo
      html:function(s){ return ehHtml(s)+"<div class='offer "+(s.oc||'')+"'><div class='ot'>"+(s.ot||'')+"</div>"
        +(s.os?"<div class='os'>"+s.os+"</div>":"")+(s.obadge?"<div class='obadge'>"+s.obadge+"</div>":"")+"</div>"; },
      init:function(tl,r,s){ ehInit(tl,r,s); G.set(q(r,'.offer'),{opacity:0,y:24}); up(tl,q(r,'.offer'), at(s,'heroAt',s.start+.5));
        if(q(r,'.obadge')){ G.set(q(r,'.obadge'),{opacity:0,scale:.6,transformOrigin:'50% 50%'}); pop(tl,q(r,'.obadge'), at(s,'badgeAt',s.start+1.3)); } }
    },

    checklist: { // itens com check, revelados 1 a 1
      html:function(s){ var it=s.items||[]; return ehHtml(s)+"<div class='checklist'>"+it.map(function(t){return "<div class='ck'><span class='mk'>✓</span><span class='cx'>"+t+"</span></div>";}).join("")+"</div>"; },
      init:function(tl,r,s){ ehInit(tl,r,s); G.set(qa(r,'.ck'),{opacity:0,x:-24});
        qa(r,'.ck').forEach(function(c,i){ tl.to(c,{opacity:1,x:0,duration:.4,ease:'back.out(1.4)'}, at(s,'heroAt',s.start+.5)+i*at(s,'stagger',.45)); }); }
    }
  };

  function build(opts){
    var root=document.getElementById('root');
    var cap=document.getElementById('capwrap');
    var tl=G.timeline({paused:true}); window.__timelines=window.__timelines||{}; window.__timelines['main']=tl;
    tl.to({},{duration:opts.duration},0);
    // fundo vivo: zoom+pan lento durante o vídeo todo (parallax ambiente)
    var bg0=root.querySelector('.bg');
    if(bg0){ G.set(bg0,{transformOrigin:'50% 50%'}); tl.fromTo(bg0,{scale:1.06,x:-22,y:-10},{scale:1.13,x:22,y:10,duration:opts.duration,ease:'sine.inOut'},0); }
    // grade das janelas de b-roll
    var grade=root.querySelector('.grade');
    if(grade){ G.set(grade,{opacity:0}); }
    (opts.scenes||[]).forEach(function(s,i){
      s.id='s'+i+'_';
      var sc=document.createElement('div'); sc.className='scene'; sc.id='sc'+i; root.insertBefore(sc, cap);
      G.set(sc,{opacity:0});
      var T=TYPES[s.type]; if(!T){ console.warn('tipo desconhecido',s.type); return; }
      sc.innerHTML=T.html(s);
      tl.set(sc,{opacity:1},s.start); if(s.end!=null) tl.set(sc,{opacity:0},s.end);
      T.init(tl,sc,s);
      // movimento ambiente: push-in + pan alternado (câmera viva) durante a cena — nunca congela
      var sdur=(s.end!=null?s.end:opts.duration)-s.start;
      if(sdur>0.6 && s.type!=='broll'){
        var pz=1.0+Math.min(0.075, sdur*0.011);
        var panx=(i%2===0)?20:-20;
        tl.fromTo(sc,{scale:1.0,x:0},{scale:pz,x:panx,duration:sdur,ease:'sine.inOut',transformOrigin:'50% 45%',immediateRender:false},s.start);
      }
      // lint "cena nunca vazia": herói não pode entrar > 0.9s depois do start
      var heroA = (s.type==='cta') ? (s.btnAt||(s.date||s.live?null:s.start+0.6)) : (s.heroAt||null);
      if(heroA!=null && (heroA - s.start) > 0.9) console.warn('[faceless-kit] cena '+i+' ('+s.type+'): herói entra '+(heroA-s.start).toFixed(1)+'s depois do start — vai deixar cena vazia. Traga heroAt/btnAt pra ~start+0.5 (sincronia fica na legenda/animação-chave).');
      if(s.type==='broll' && grade){ tl.set(grade,{opacity:1},s.start); if(s.end!=null) tl.set(grade,{opacity:0},s.end); }
    });
    // legenda pill (karaokê)
    var cues=opts.cues||window.__cues||[];
    cues.forEach(function(c){ var cue=document.createElement('div'); cue.className='cue'; var pill=document.createElement('div'); pill.className='pill';
      var spans=c.words.map(function(w){var sp=document.createElement('span');sp.textContent=w.tx+' ';pill.appendChild(sp);return sp;});
      cue.appendChild(pill); cap.appendChild(cue); tl.set(cue,{opacity:1},c.s); tl.set(spans,{color:'#8a97a0'},c.s);
      c.words.forEach(function(w,i){ tl.set(spans[i],{color:'#0e2a36'},w.t); }); tl.set(cue,{opacity:0},c.e+0.05); });
    return tl;
  }
  return { build:build, TYPES:TYPES };
})();
