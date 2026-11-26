let token = localStorage.getItem('token') || '';
let ME = null, PRODS = [], EDIT_ID = null, FOTO_TEMP = '', FOTO_PERFIL = '';
function H(){ return {'Content-Type':'application/json','Authorization':'Bearer '+token}; }
async function api(u,m,b){ const r=await fetch(u,{method:m||'GET',headers:H(),body:b?JSON.stringify(b):undefined}); const d=await r.json().catch(()=>({})); if(!r.ok) throw new Error(d.detail||'Erro'); return d; }
function val(id){ return document.getElementById(id)?.value||''; }
function esc(s){ return String(s||'').replace(/'/g,"\\'"); }
function toast(m){ let t=document.getElementById('toast'); if(!t){ t=document.createElement('div'); t.id='toast'; t.style.cssText='position:fixed;bottom:22px;left:50%;transform:translateX(-50%);background:#1A0F0F;color:#fff;padding:12px 20px;border-radius:999px;z-index:999;font-weight:700'; document.body.appendChild(t);} t.innerText=m; t.style.display='block'; clearTimeout(t._h); t._h=setTimeout(()=>t.style.display='none',3000); }
function mostrarSec(id, btn){
  ['dashSec','pessoasSec','produtosSec','vendasSec','producaoSec','caixaSec','fornecedorSec','fazerEncSec','minhasEncSec','encomendasSec','dividasSec','adminSec','historicoSec','sugestaoSec'].forEach(s=>document.getElementById(s)?.classList.add('hidden'));
  document.getElementById(id)?.classList.remove('hidden');
  document.querySelectorAll('.sidebar button[data-sec]').forEach(b=>b.classList.remove('on'));
  if(btn) btn.classList.add('on');
}
function voltarProdutos(){ mostrarSec('produtosSec', document.querySelector('#menuCliente [data-sec="produtosSec"], #menuFunc [data-sec="produtosSec"], #menuAdmin [data-sec="produtosSec"]')); }
function sair(){ localStorage.removeItem('token'); location.reload(); }
function lerFoto(e){ const f=e.target.files[0]; if(!f) return; const rd=new FileReader(); rd.onload=()=>FOTO_TEMP=rd.result; rd.readAsDataURL(f); }
function lerFotoPerfil(e){ const f=e.target.files[0]; if(!f) return; const rd=new FileReader(); rd.onload=()=>{ FOTO_PERFIL=rd.result; document.getElementById('perfilFotoPrev').src=FOTO_PERFIL; }; rd.readAsDataURL(f); }
async function login(){ try{ const d=await api('/api/login','POST',{telefone:val('loginTel'),password:val('loginSenha')}); token=d.token; localStorage.setItem('token',token); await mostrarBoasVindas(); }catch(e){ document.getElementById('authMsg').innerText=e.message; } }
async function registar(){ try{ const d=await api('/api/register','POST',{nome:val('rNome'),telefone:val('rTel'),idade:parseInt(val('rIdade')||18),email:val('rEmail'),foto:'',pais:'Moçambique',bairro:val('rBairro'),endereco:val('rEndereco'),tipo:val('rTipo'),password:val('rSenha')}); token=d.token; localStorage.setItem('token',token); await mostrarBoasVindas(); }catch(e){ document.getElementById('authMsg2').innerText=e.message; } }
async function mostrarBoasVindas(){ try{ ME=await api('/api/me'); }catch(e){ location.reload(); return; } document.getElementById('loginPage').classList.add('hidden'); const w=document.getElementById('welcome'); w.classList.remove('hidden'); document.getElementById('welcomeNome').innerText='Bem-vindo, '+ME.nome+'!'; document.getElementById('welcomeTexto').innerText = ME.tipo==='Cliente' ? 'Vê os produtos frescos de hoje e faz a tua encomenda.' : ME.tipo==='Funcionário' ? 'Bom trabalho! Vamos vender bem hoje.' : 'Bem-vindo, Admin. Tudo sob controlo.'; document.getElementById('welcomeFoto').src=ME.foto||'/static/imagem/logo.jpg'; }
function entrarSistema(){ document.getElementById('welcome').classList.add('hidden'); document.getElementById('app').classList.remove('hidden'); carregarDados(); }
function abrirPerfil(){ document.getElementById('modalPerfil').classList.remove('hidden'); document.getElementById('perfilNome').value=ME?.nome||''; document.getElementById('perfilBairro').value=ME?.bairro||''; document.getElementById('perfilEndereco').value=ME?.endereco||''; document.getElementById('perfilEmail').value=ME?.email||''; document.getElementById('perfilFotoPrev').src=ME?.foto||'/static/imagem/logo.jpg'; FOTO_PERFIL=''; }
function fecharPerfil(){ document.getElementById('modalPerfil').classList.add('hidden'); }
async function salvarPerfil(){ try{ await api('/api/me','PUT',{nome:val('perfilNome'),bairro:val('perfilBairro'),endereco:val('perfilEndereco'),email:val('perfilEmail'),foto:FOTO_PERFIL}); toast('Perfil atualizado!'); fecharPerfil(); carregarDados(); }catch(e){ alert(e.message); } }
async function mudarSenha(){ try{ await api('/api/me/senha','POST',{antiga:val('senhaAntiga'),nova:val('senhaNova')}); toast('Senha trocada!'); }catch(e){ alert(e.message); } }

async function carregarDados(){
  if(!token) return;
  try{ ME=await api('/api/me'); }catch(e){ localStorage.removeItem('token'); token=''; location.reload(); return; }
  document.getElementById('loginPage').classList.add('hidden'); document.getElementById('app').classList.remove('hidden');
  document.getElementById('saudacao').innerText='Olá, '+ME.nome;
  document.getElementById('infoUser').innerText=ME.tipo+' • '+ME.telefone;
  document.getElementById('infoPontos').innerText='⭐ Pontos: '+(ME.pontos||0);
  if(ME.foto){ document.getElementById('meuAvatar').src=ME.foto; document.getElementById('sideFoto').src=ME.foto; }
  const isAdmin=ME.is_admin, isFunc=ME.tipo==='Funcionário', isCliente=ME.tipo==='Cliente';
  document.getElementById('menuCliente').classList.toggle('hidden', !isCliente);
  document.getElementById('menuFunc').classList.toggle('hidden', !isFunc);
  document.getElementById('menuAdmin').classList.toggle('hidden', !isAdmin);
  document.getElementById('adminProdForm').classList.toggle('hidden', !isAdmin);
  document.getElementById('adminFornForm').classList.toggle('hidden', !isAdmin);
  if(isCliente) mostrarSec('produtosSec', document.querySelector('#menuCliente [data-sec="produtosSec"]'));
  else if(isFunc) mostrarSec('vendasSec', document.querySelector('#menuFunc [data-sec="vendasSec"]'));
  else mostrarSec('dashSec', document.querySelector('#menuAdmin [data-sec="dashSec"]'));

  if(isAdmin){
    try{ const dash=await api('/api/dashboard'); document.getElementById('tVendas').innerText=dash.semana.vendas+' MT'; document.getElementById('tLucro').innerText=dash.semana.lucro+' MT'; document.getElementById('tClientes').innerText=dash.totais.clientes; document.getElementById('tDividas').innerText=dash.totais.dividas+' MT'; document.getElementById('grafico').innerHTML=dash.grafico.map(g=>`<div class="bar" style="height:${Math.max(5,Math.min(100,g.vendas/50))}px"></div>`).join(''); document.getElementById('graficoLabels').innerHTML=dash.grafico.map(g=>`<span>${g.label}</span>`).join(''); document.getElementById('maisVendidos').innerHTML=dash.mais_vendidos.map(m=>`<p>${m.produto} - ${m.qtd}</p>`).join('')||'Ainda sem vendas'; }catch(e){}
  }
  try{
    PRODS=await api('/api/products'); const q=val('pesquisaProd').toLowerCase(); const lista=PRODS.filter(p=>p.nome.toLowerCase().includes(q));
    document.getElementById('gridProd').innerHTML=lista.map(p=>`<div class="prod-card"><img src="${p.foto||'/static/imagem/logo.jpg'}"><b>${p.nome}</b><p>${p.categoria} • ${p.preco} MT</p><p>${p.descricao||''}</p><p>Stock: <b>${p.stock}</b> ${p.stock<=0?'❌ ACABOU':p.stock<=5?'⚠️ A ACABAR':'✅ Disponível'}</p>${isAdmin?`<button class="btn" onclick="editarProd(${p.id})">Editar</button><button class="btn btn-red" onclick="apagarProd(${p.id})">Apagar</button>`:''}${isCliente?`<button class="btn btn-green" onclick="encomendarProduto('${esc(p.nome)}')">Encomendar</button>`:''}</div>`).join('');
    document.getElementById('vProd').innerHTML=PRODS.map(p=>`<option value="${p.id}">${p.nome} - ${p.preco} MT (stock ${p.stock})</option>`).join('');
    document.getElementById('prodProd').innerHTML=PRODS.map(p=>`<option value="${p.id}">${p.nome}</option>`).join('');
    document.getElementById('eTipo').innerHTML=PRODS.map(p=>`<option>${p.nome}</option>`).join('');
  }catch(e){}
  try{
    const enc=await api('/api/encomendas');
    const minhas = enc.filter(e=> isCliente ? true : true);
    // Minhas encomendas - cliente já vem filtrado no backend, func/admin vê tudo
    document.getElementById('listaMinhasEnc').innerHTML = enc.map(e=>`<div class="linha"><b>${e.tipo}</b> - ${e.personalizacao||''}<br>Entrega: ${e.data_entrega} ${e.hora_entrega} • ${e.modo} • Estado: <b>${e.estado}</b> • Pagamento: ${e.sinal} • Preço base: ${e.preco} MT ${e.estado!=='Entregue'&&e.estado!=='Cancelada'?`<button class="btn btn-red" onclick="cancelarEnc(${e.id})">Cancelar</button>`:''}</div>`).join('')||'Ainda não tens encomendas';
    if(!isCliente) document.getElementById('listaEnc').innerHTML = enc.map(e=>`<div class="linha"><b>${e.cliente}</b> - ${e.tipo} - ${e.personalizacao||''} - ${e.data_entrega} ${e.hora_entrega} - ${e.estado} - ${e.sinal} <button class="btn btn-green" onclick="mudarEstadoEnc(${e.id},'Em Preparação')">Em Preparação</button><button class="btn" onclick="mudarEstadoEnc(${e.id},'Pronta')">Pronta</button><button class="btn btn-dark" onclick="mudarEstadoEnc(${e.id},'Entregue')">Entregue</button></div>`).join('');
  }catch(e){}
  try{
    const hist=await api('/api/meu-historico');
    document.getElementById('listaHistorico').innerHTML = hist.map(h=>`<div class="linha">${h.data} - ${h.produto} x${h.qtd} = ${h.total} MT - ${h.pagamento} - ${h.estado}</div>`).join('')||'Sem histórico ainda';
  }catch(e){}
  try{
    if(isAdmin){
      const pessoas=await api('/api/pessoas');
      document.getElementById('listaPessoas').innerHTML=pessoas.map(p=>{ const ativo=p.active!==false; return `<div class="linha"><b>${p.nome}</b> - ${p.telefone} - ${p.tipo} - Pontos: ${p.pontos} ${ativo?'<span class="badge-ok">Ativo</span>':'<span class="badge-off">DEMITIDO</span>'} ${p.id!==ME.id?(ativo?`<button class="btn btn-red" onclick="demitirPessoa(${p.id},'${esc(p.nome)}')">Demitir</button>`:`<button class="btn btn-green" onclick="reativarPessoa(${p.id},'${esc(p.nome)}')">Reativar</button>`):''}</div>`; }).join('');
      const fin=await api('/api/financeiro');
      document.getElementById('listaDividas').innerHTML=fin.dividas.map(v=>`<div class="linha"><b>${v.cliente}</b> - ${v.produto} - ${v.total} MT <button class="btn btn-green" onclick="pagarDivida(${v.id})">Marcar Pago</button></div>`).join('')||'Sem dívidas';
      document.getElementById('listaCompras').innerHTML=fin.compras.slice(0,20).map(c=>`<div class="linha">${c.fornecedor} - ${c.produto} x${c.qtd} = ${c.total} MT</div>`).join('');
      const sug=await api('/api/sugestoes');
      document.getElementById('listaSugestoes').innerHTML=sug.map(s=>`<div class="linha"><b>${s.cliente}</b> [${s.tipo}] - ${s.texto} - ${s.data}</div>`).join('');
    }
  }catch(e){}
  try{
    if(!isCliente){
      const forn=await api('/api/fornecedores');
      document.getElementById('listaForn').innerHTML=forn.map(f=>`<div class="linha"><b>${f.nome}</b> - ${f.telefone} - ${f.produto} - ${f.preco} MT - ${f.localizacao}</div>`).join('');
      document.getElementById('cForn').innerHTML=forn.map(f=>`<option value="${f.id}">${f.nome} - ${f.produto}</option>`).join('');
    }
  }catch(e){}
}
function encomendarProduto(nome){ document.getElementById('eTipo').value=nome; mostrarSec('fazerEncSec', document.querySelector('#menuCliente [data-sec="fazerEncSec"]')); }
async function demitirPessoa(id,nome){ if(!confirm('Demitir '+nome+'?')) return; try{ await api('/api/pessoas/'+id+'/demitir','POST',{}); toast('Demitido'); carregarDados(); }catch(e){ alert(e.message); } }
async function reativarPessoa(id,nome){ try{ await api('/api/pessoas/'+id+'/reativar','POST',{}); toast('Reativado'); carregarDados(); }catch(e){ alert(e.message); } }
async function pagarDivida(id){ try{ await api('/api/vendas/'+id+'/pagar','POST',{}); toast('Dívida paga'); carregarDados(); }catch(e){ alert(e.message); } }
async function editarProd(id){ let p=PRODS.find(x=>x.id===id); if(!p) return; document.getElementById('pNome').value=p.nome; document.getElementById('pCat').value=p.categoria; document.getElementById('pPreco').value=p.preco; document.getElementById('pCusto').value=p.custo; document.getElementById('pStock').value=p.stock; document.getElementById('pDesc').value=p.descricao||''; EDIT_ID=id; FOTO_TEMP=''; document.getElementById('btnSalvarProd').innerText='Guardar alterações'; mostrarSec('produtosSec', document.querySelector('#menuAdmin [data-sec="produtosSec"]')); }
async function salvarProd(){ let dados={nome:val('pNome'),categoria:val('pCat'),preco:parseFloat(val('pPreco')||0),custo:parseFloat(val('pCusto')||0),stock:parseInt(val('pStock')||0),stock_minimo:5,foto:FOTO_TEMP,descricao:val('pDesc')}; try{ if(EDIT_ID){ if(!dados.foto) delete dados.foto; await api('/api/products/'+EDIT_ID,'PUT',dados); toast('Produto atualizado!'); } else { await api('/api/products','POST',dados); toast('Produto adicionado!'); } EDIT_ID=null; carregarDados(); }catch(e){ alert(e.message); } }
async function apagarProd(id){ if(!confirm('Apagar produto?')) return; try{ await api('/api/products/'+id,'DELETE'); toast('Apagado'); carregarDados(); }catch(e){ alert(e.message); } }
async function addVenda(){ try{ let d=await api('/api/vendas','POST',{produto_id:parseInt(val('vProd')),qtd:parseInt(val('vQtd')||1),cliente:val('vCliente')||'Cliente Balcão',cliente_tel:val('vTel'),pagamento:val('vPag'),data_pagamento:val('vDataPag')}); toast('Venda feita! '+d.total+' MT'); if(d.whatsapp_link) window.open(d.whatsapp_link,'_blank'); carregarDados(); }catch(e){ alert(e.message); } }
async function addDespesa(){ try{ await api('/api/despesas','POST',{descricao:val('sDesc'),valor:parseFloat(val('sValor')||0),categoria:val('sCat')}); toast('Despesa registada'); carregarDados(); }catch(e){ alert(e.message); } }
async function addProducao(){ try{ await api('/api/producao','POST',{produto_id:parseInt(val('prodProd')),qtd:parseInt(val('prodQtd')||1),obs:val('prodObs')}); toast('Produção registada'); carregarDados(); }catch(e){ alert(e.message); } }
async function addForn(){ try{ await api('/api/fornecedores','POST',{nome:val('fNome'),telefone:val('fTel'),produto:val('fProd'),preco:parseFloat(val('fPreco')||0),localizacao:val('fLocal')}); toast('Fornecedor adicionado'); carregarDados(); }catch(e){ alert(e.message); } }
async function addCompra(){ try{ await api('/api/compras','POST',{fornecedor_id:parseInt(val('cForn')),produto:val('cProd'),qtd:parseInt(val('cQtd')||1),preco_unitario:parseFloat(val('cPreco')||0),pagamento:val('cPag')}); toast('Compra registada'); carregarDados(); }catch(e){ alert(e.message); } }
async function addEnc(){ if(!val('eData')){ alert('Escolhe a data de entrega! Quando queres receber?'); return; } try{ let d=await api('/api/encomendas','POST',{cliente:ME.nome,telefone:ME.telefone,tipo:val('eTipo'),personalizacao:val('ePersonalizar'),data_entrega:val('eData'),hora_entrega:val('eHora'),modo:val('eModo'),sinal:val('eSinal'),obs:val('eObs')}); toast(d.msg||'Encomenda recebida!'); carregarDados(); mostrarSec('minhasEncSec', document.querySelector('#menuCliente [data-sec="minhasEncSec"]')); }catch(e){ alert(e.message); } }
async function mudarEstadoEnc(id,estado){ try{ await api('/api/encomendas/'+id+'/estado?estado='+encodeURIComponent(estado),'POST',{}); toast('Estado: '+estado); carregarDados(); }catch(e){ alert(e.message); } }
async function cancelarEnc(id){ if(!confirm('Cancelar esta encomenda?')) return; try{ await api('/api/encomendas/'+id+'/cancelar','POST',{}); toast('Encomenda cancelada'); carregarDados(); }catch(e){ alert(e.message); } }
async function addSugestao(){ try{ await api('/api/sugestoes','POST',{texto:val('sugTexto'),tipo:val('sugTipo')}); toast('Obrigado! Recebemos a tua mensagem.'); carregarDados(); }catch(e){ alert(e.message); } }
async function carregarPainelAdmin(){ try{ let d=await api('/api/admin/painel'); document.getElementById('adminResumo').innerHTML=`<div class="kpis"><div class="kpi"><span>Total Vendas</span><b>${d.resumo.total_vendas} MT</b></div><div class="kpi"><span>Lucro Líquido</span><b>${d.resumo.lucro_liquido_final} MT</b></div><div class="kpi"><span>Dívidas</span><b>${d.resumo.dividas} MT</b></div></div>`; document.getElementById('adminVendas').innerHTML='<h3>Últimas Vendas</h3>'+d.ultimas_vendas.map(v=>`<div class="linha">${v.data} - ${v.cliente} - ${v.produto} x${v.qtd} = ${v.total} MT</div>`).join(''); document.getElementById('adminCompras').innerHTML='<h3>Últimas Compras</h3>'+d.ultimas_compras.map(c=>`<div class="linha">${c.data} - ${c.fornecedor} - ${c.produto} x${c.qtd} = ${c.total} MT</div>`).join(''); document.getElementById('adminFluxo').innerHTML='<h3>Logs</h3>'+d.fluxo.map(l=>`<div class="linha">${l.data} - <b>${l.quem}</b> - ${l.acao} - ${l.detalhe}</div>`).join(''); }catch(e){ alert(e.message); } }
async function backup(){ try{ let d=await api('/api/backup'); let blob=new Blob([JSON.stringify(d,null,2)],{type:'application/json'}); let a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='tongas-backup.json'; a.click(); }catch(e){ alert(e.message); } }
window.addEventListener('load', ()=>{ if(token) carregarDados(); });