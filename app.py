import os, re, io
from datetime import date, datetime, timedelta, timezone
from urllib.parse import quote
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse, Response, StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt
import bcrypt
from pydantic import BaseModel, field_validator
from sqlalchemy import create_engine, String, Integer, DateTime, Text, Boolean, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session
from fpdf import FPDF
import openpyxl

SECRET = os.getenv("SECRET_KEY", "TONGAS_LANCHONETE_2026")
DBURL = os.getenv("DATABASE_URL", "sqlite:///./tongas.db")
if DBURL.startswith("postgres://"): DBURL = DBURL.replace("postgres://", "postgresql://", 1)
engine = create_engine(DBURL, connect_args={"check_same_thread": False} if DBURL.startswith("sqlite") else {}, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# CRIA PASTAS SE NÃO EXISTIREM - CORREÇÃO 4
os.makedirs("static/imagem", exist_ok=True)

class Pwd:
    def hash(self, p): return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()
    def verify(self, p, h):
        try: return bcrypt.checkpw(p.encode(), h.encode())
        except: return False
pwd = Pwd()
def agora(): return datetime.now(timezone.utc)
class Base(DeclarativeBase): pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    telefone: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    idade: Mapped[int] = mapped_column(Integer, default=18)
    email: Mapped[str] = mapped_column(String(180), default="")
    foto: Mapped[str] = mapped_column(Text, default="")
    pais: Mapped[str] = mapped_column(String(60), default="Moçambique")
    bairro: Mapped[str] = mapped_column(String(80), default="Matola")
    endereco: Mapped[str] = mapped_column(String(180), default="")
    tipo: Mapped[str] = mapped_column(String(30), default="Cliente")
    password_hash: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    pontos: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=agora)

class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    categoria: Mapped[str] = mapped_column(String(60), default="Lanches")
    preco: Mapped[float] = mapped_column(Float, default=0)
    custo: Mapped[float] = mapped_column(Float, default=0)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    stock_minimo: Mapped[int] = mapped_column(Integer, default=5)
    foto: Mapped[str] = mapped_column(Text, default="")
    descricao: Mapped[str] = mapped_column(Text, default="")
    updated_by: Mapped[str] = mapped_column(String(120), default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=agora)

class Venda(Base):
    __tablename__ = "vendas"
    id: Mapped[int] = mapped_column(primary_key=True)
    cliente: Mapped[str] = mapped_column(String(120), default="Cliente Balcão")
    cliente_tel: Mapped[str] = mapped_column(String(30), default="")
    vendedor: Mapped[str] = mapped_column(String(120), default="")
    produto: Mapped[str] = mapped_column(String(120))
    qtd: Mapped[int] = mapped_column(Integer, default=1)
    total: Mapped[float] = mapped_column(Float, default=0)
    custo_total: Mapped[float] = mapped_column(Float, default=0)
    lucro: Mapped[float] = mapped_column(Float, default=0)
    pagamento: Mapped[str] = mapped_column(String(40), default="M-Pesa")
    estado: Mapped[str] = mapped_column(String(30), default="Pago")
    data_pagamento: Mapped[str] = mapped_column(String(20), default="")
    whatsapp_link: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=agora)

class Despesa(Base):
    __tablename__ = "despesas"
    id: Mapped[int] = mapped_column(primary_key=True)
    descricao: Mapped[str] = mapped_column(String(180))
    valor: Mapped[float] = mapped_column(Float, default=0)
    categoria: Mapped[str] = mapped_column(String(60), default="Geral")
    criado_por: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=agora)

class Compra(Base):
    __tablename__ = "compras"
    id: Mapped[int] = mapped_column(primary_key=True)
    fornecedor: Mapped[str] = mapped_column(String(120))
    produto: Mapped[str] = mapped_column(String(120))
    qtd: Mapped[int] = mapped_column(Integer, default=1)
    preco_unitario: Mapped[float] = mapped_column(Float, default=0)
    total: Mapped[float] = mapped_column(Float, default=0)
    pagamento: Mapped[str] = mapped_column(String(40), default="Dinheiro")
    comprado_por: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=agora)

class Fornecedor(Base):
    __tablename__ = "fornecedores"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    telefone: Mapped[str] = mapped_column(String(30), default="")
    produto: Mapped[str] = mapped_column(String(120), default="")
    preco: Mapped[float] = mapped_column(Float, default=0)
    localizacao: Mapped[str] = mapped_column(String(120), default="")

class Encomenda(Base):
    __tablename__ = "encomendas"
    id: Mapped[int] = mapped_column(primary_key=True)
    cliente: Mapped[str] = mapped_column(String(120))
    telefone: Mapped[str] = mapped_column(String(30), default="")
    tipo: Mapped[str] = mapped_column(String(120))
    personalizacao: Mapped[str] = mapped_column(Text, default="")
    data_entrega: Mapped[str] = mapped_column(String(20), default="")
    hora_entrega: Mapped[str] = mapped_column(String(20), default="")
    modo: Mapped[str] = mapped_column(String(30), default="Levantamento")
    preco: Mapped[float] = mapped_column(Float, default=0)
    sinal: Mapped[str] = mapped_column(String(60), default="Ainda não paguei")
    obs: Mapped[str] = mapped_column(Text, default="")
    estado: Mapped[str] = mapped_column(String(30), default="Recebida")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=agora)

class Log(Base):
    __tablename__ = "logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    quem: Mapped[str] = mapped_column(String(120), default="")
    tipo: Mapped[str] = mapped_column(String(30), default="")
    acao: Mapped[str] = mapped_column(String(80))
    detalhe: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=agora)

class Sugestao(Base):
    __tablename__ = "sugestoes"
    id: Mapped[int] = mapped_column(primary_key=True)
    cliente: Mapped[str] = mapped_column(String(120), default="")
    texto: Mapped[str] = mapped_column(Text, default="")
    tipo: Mapped[str] = mapped_column(String(30), default="Sugestão")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=agora)

Base.metadata.create_all(engine)
def dbdep():
    d = SessionLocal()
    try: yield d
    finally: d.close()
def log_action(d, quem, tipo, acao, detalhe=""):
    try: d.add(Log(quem=quem, tipo=tipo, acao=acao, detalhe=detalhe[:600])); d.commit()
    except Exception: d.rollback()
def make_token(u): return jwt.encode({"sub": str(u.id), "exp": datetime.now(timezone.utc) + timedelta(hours=24)}, SECRET, algorithm="HS256")
def clean_tel(tel): return re.sub(r"\D", "", tel or "")
def normalizar_tipo(tipo):
    t = (tipo or "Cliente").strip().lower()
    if "funcion" in t: return "Funcionário"
    if "admin" in t: return "Admin"
    return "Cliente"
def is_funcionario(u): return u.is_admin or normalizar_tipo(u.tipo) == "Funcionário"
def whatsapp_link(tel, msg):
    tel = clean_tel(tel)
    if not tel: return ""
    if tel.startswith("0"): tel = "258" + tel[1:]
    if not tel.startswith("258"): tel = "258" + tel
    return f"https://wa.me/{tel}?text={quote(msg)}"

def init_data():
    d = SessionLocal()
    try:
        if not d.query(User).filter_by(telefone="840000000").first():
            d.add(User(nome="Tongas", telefone="840000000", idade=18, email="tongas@lanchonete.co.mz", pais="Moçambique", bairro="Matola", tipo="Admin", password_hash=pwd.hash(os.getenv("ADMIN_PASSWORD", "Tongas12345")), is_admin=True)); d.commit()
        if d.query(Product).count() == 0:
            dados = [("Água","Bebidas",30,15,100,"/static/imagem/agua.jpg","Água mineral fresca"),("Batatas Fritas","Lanches",150,70,40,"/static/imagem/batatas.jpg","Batatas crocantes"),("Batido Pulso Runner","Batidos",250,120,25,"/static/imagem/batidos-pulso-runner.jpg","Batido energético"),("Sumo Cappy","Bebidas",120,60,40,"/static/imagem/CAPPY.jpg","Sumo Cappy"),("Hambúrguer","Lanches",350,180,30,"/static/imagem/hamburguer.jpg","Hambúrguer da casa"),("Coca-Cola Lata","Bebidas",100,55,60,"/static/imagem/lat.jpg","Coca-Cola gelada"),("Sumo Natural","Bebidas",150,70,30,"/static/imagem/natural.jpg","Sumo natural do dia"),("Prego","Lanches",280,140,25,"/static/imagem/prego.jpg","Prego no pão"),("Sanduíche / Sando","Lanches",200,100,30,"/static/imagem/sando.jpg","Sando fresco"),("Sumo","Bebidas",90,40,40,"/static/imagem/sumo.jpg","Sumo fresco")]
            for p in dados: d.add(Product(nome=p[0], categoria=p[1], preco=p[2], custo=p[3], stock=p[4], foto=p[5], descricao=p[6]))
            d.commit()
        for p in d.query(Product).all():
            if p.foto.endswith(".avif"): p.foto = p.foto.replace(".avif", ".jpg")
            if p.nome == "Bolo de Aniversário": p.nome = "Sumo"; p.preco = 90; p.foto = "/static/imagem/sumo.jpg"; p.categoria = "Bebidas"
        d.commit()
        if d.query(Fornecedor).count() == 0:
            for f in [("Coca-Cola Matola","841234567","Coca-Cola Lata",55,"Matola"),("Pão Matola","849876543","Pão Hambúrguer",40,"Matola"),("Frutas Maputo","842222333","Fruta p/ Sumo",70,"Maputo")]: d.add(Fornecedor(nome=f[0], telefone=f[1], produto=f[2], preco=f[3], localizacao=f[4]))
            d.commit()
    finally: d.close()
init_data()

oauth = OAuth2PasswordBearer(tokenUrl="/api/login")
def current_user(tok: str = Depends(oauth), d: Session = Depends(dbdep)):
    try: uid = int(jwt.decode(tok, SECRET, algorithms=["HS256"])["sub"])
    except Exception: raise HTTPException(401, "Sessão inválida.")
    u = d.get(User, uid)
    if not u or not u.is_active: raise HTTPException(401, "Conta indisponível.")
    return u
def admin_only(u: User = Depends(current_user)):
    if not u.is_admin: raise HTTPException(403, "Só Admin.")
    return u
def funcionario_only(u: User = Depends(current_user)):
    if not is_funcionario(u): raise HTTPException(403, "Só Funcionário / Admin.")
    return u

app = FastAPI(title="TONGAS V3")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORREÇÃO 1 - HTML JUNTO: / e /dashboard mostram o mesmo index.html
def _index_html():
    try: return open("static/index.html", encoding="utf-8").read()
    except FileNotFoundError: return "<h1>Tongas - Falta o ficheiro static/index.html</h1>"

@app.get("/", response_class=HTMLResponse)
def home(): return _index_html()
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(): return _index_html()  # antes era dashboard.html que já não existe
@app.get("/login", response_class=HTMLResponse)
def login_page(): return RedirectResponse(url="/")
@app.get("/api/health")
def health(): return {"status": "ok", "app": "TONGAS V3"}

# CORREÇÃO 2 - Validação de quantidade e preço
class Register(BaseModel):
    nome: str; telefone: str; idade: int = 18; email: str = ""; foto: str = ""; pais: str = "Moçambique"; bairro: str = "Matola"; endereco: str = ""; tipo: str = "Cliente"; password: str
    @field_validator("nome")
    @classmethod
    def nome_ok(cls, v):
        if not v or len(v.strip()) < 2: raise ValueError("Nome muito curto")
        return v.strip()
    @field_validator("password")
    @classmethod
    def senha_ok(cls, v):
        if len(v) < 4: raise ValueError("Senha curta, usa 4+ caracteres.")
        return v
class Login(BaseModel): telefone: str; password: str
class ProdIn(BaseModel):
    nome: str; categoria: str = "Lanches"; preco: float = 0; custo: float = 0; stock: int = 0; stock_minimo: int = 5; foto: str = ""; descricao: str = ""
    @field_validator("preco", "custo", "stock")
    @classmethod
    def nao_negativo(cls, v):
        if v < 0: raise ValueError("Valor não pode ser negativo")
        return v
class FornIn(BaseModel): nome: str; telefone: str = ""; produto: str = ""; preco: float = 0; localizacao: str = ""
class CompraIn(BaseModel):
    fornecedor_id: int; produto: str; qtd: int = 1; preco_unitario: float = 0; pagamento: str = "Dinheiro"
    @field_validator("qtd")
    @classmethod
    def qtd_ok(cls, v):
        if v <= 0: raise ValueError("Quantidade tem de ser 1 ou mais")
        return v
class VendaIn(BaseModel):
    produto_id: int; qtd: int = 1; cliente: str = "Cliente Balcão"; cliente_tel: str = ""; pagamento: str = "M-Pesa"; data_pagamento: str = ""
    @field_validator("qtd")
    @classmethod
    def qtd_ok(cls, v):
        if v <= 0: raise ValueError("Quantidade tem de ser 1 ou mais")
        return v
class DespesaIn(BaseModel):
    descricao: str; valor: float; categoria: str = "Geral"
    @field_validator("valor")
    @classmethod
    def valor_ok(cls, v):
        if v <= 0: raise ValueError("Valor tem de ser maior que 0")
        return v
class EncIn(BaseModel): cliente: str; telefone: str = ""; tipo: str = "Hambúrguer"; personalizacao: str = ""; data_entrega: str = ""; hora_entrega: str = ""; modo: str = "Levantamento"; sinal: str = "Ainda não paguei"; obs: str = ""
class SenhaIn(BaseModel): antiga: str; nova: str
class PerfilIn(BaseModel): nome: str = ""; bairro: str = ""; endereco: str = ""; foto: str = ""; email: str = ""
class SugestaoIn(BaseModel): texto: str; tipo: str = "Sugestão"
class ProducaoIn(BaseModel):
    produto_id: int; qtd: int = 1; obs: str = ""
    @field_validator("qtd")
    @classmethod
    def qtd_ok(cls, v):
        if v <= 0: raise ValueError("Quantidade tem de ser 1 ou mais")
        return v

@app.post("/api/register")
def register(x: Register, d: Session = Depends(dbdep)):
    tel = clean_tel(x.telefone)
    if len(tel) < 9: raise HTTPException(400, "Telefone inválido.")
    existente = d.query(User).filter_by(telefone=tel).first()
    if existente:
        try: ok = pwd.verify(x.password, existente.password_hash)
        except Exception: ok = False
        if ok:
            if not existente.is_active: raise HTTPException(403, "Conta bloqueada.")
            return {"token": make_token(existente), "user": {"nome": existente.nome, "tipo": existente.tipo}}
        raise HTTPException(409, "Este número já tem conta! Vai para ENTRAR.")
    u = User(nome=x.nome.strip(), telefone=tel, idade=x.idade, email=x.email, foto=x.foto, pais=x.pais, bairro=x.bairro, endereco=x.endereco, tipo=normalizar_tipo(x.tipo), password_hash=pwd.hash(x.password))
    d.add(u); d.commit(); log_action(d, u.nome, u.tipo, "registo", f"{u.nome} - {tel}")
    return {"token": make_token(u), "user": {"nome": u.nome, "tipo": u.tipo}}

@app.post("/api/login")
def login(x: Login, d: Session = Depends(dbdep)):
    tel = clean_tel(x.telefone); u = d.query(User).filter_by(telefone=tel).first()
    if not u: raise HTTPException(401, "Este número ainda não tem conta. Clica em Criar Conta.")
    try: ok = pwd.verify(x.password, u.password_hash)
    except Exception: ok = False
    if not ok: raise HTTPException(401, "Telefone ou senha errada.")
    if not u.is_active: raise HTTPException(403, "Conta bloqueada. Fala com o Admin.")
    log_action(d, u.nome, u.tipo, "login", "Entrou")
    return {"token": make_token(u), "user": {"nome": u.nome, "tipo": u.tipo, "is_admin": u.is_admin}}

@app.get("/api/me")
def me(u: User = Depends(current_user)): return {"id": u.id, "nome": u.nome, "telefone": u.telefone, "idade": u.idade, "email": u.email, "foto": u.foto, "pais": u.pais, "bairro": u.bairro, "endereco": u.endereco, "tipo": u.tipo, "is_admin": u.is_admin, "pontos": u.pontos}
@app.put("/api/me")
def atualizar_meu_perfil(x: PerfilIn, u: User = Depends(current_user), d: Session = Depends(dbdep)):
    if x.nome: u.nome = x.nome.strip()
    if x.bairro: u.bairro = x.bairro
    if x.endereco: u.endereco = x.endereco
    if x.email: u.email = x.email
    if x.foto: u.foto = x.foto
    d.commit(); return {"ok": True, "msg": "Perfil atualizado!"}
@app.post("/api/me/senha")
def mudar_senha(x: SenhaIn, u: User = Depends(current_user), d: Session = Depends(dbdep)):
    try: ok = pwd.verify(x.antiga, u.password_hash)
    except Exception: ok = False
    if not ok: raise HTTPException(401, "Senha antiga errada.")
    if len(x.nova) < 4: raise HTTPException(400, "Nova senha muito curta")
    u.password_hash = pwd.hash(x.nova); d.commit(); return {"ok": True, "msg": "Senha trocada!"}
@app.get("/api/pessoas")
def pessoas(u: User = Depends(admin_only), d: Session = Depends(dbdep)):
    return [{"id": x.id, "nome": x.nome, "telefone": x.telefone, "idade": x.idade, "email": x.email, "foto": x.foto, "bairro": x.bairro, "tipo": x.tipo, "active": x.is_active, "pontos": x.pontos} for x in d.query(User).all()]
@app.post("/api/pessoas/{pid}/demitir")
def demitir(pid: int, a: User = Depends(admin_only), d: Session = Depends(dbdep)):
    u = d.get(User, pid)
    if not u: raise HTTPException(404, "Não existe")
    if u.is_admin: raise HTTPException(400, "Não podes demitir o Admin!")
    u.is_active = False; d.commit(); log_action(d, a.nome, "Admin", "demitir", f"Demitiu {u.nome}"); return {"ok": True, "msg": f"{u.nome} demitido"}
@app.post("/api/pessoas/{pid}/reativar")
def reativar(pid: int, a: User = Depends(admin_only), d: Session = Depends(dbdep)):
    u = d.get(User, pid)
    if not u: raise HTTPException(404, "Não existe")
    u.is_active = True; d.commit(); return {"ok": True, "msg": f"{u.nome} reativado"}
@app.delete("/api/pessoas/{pid}")
def apagar_pessoa(pid: int, a: User = Depends(admin_only), d: Session = Depends(dbdep)):
    u = d.get(User, pid)
    if not u: raise HTTPException(404, "Não existe")
    if u.is_admin: raise HTTPException(400, "Não podes apagar o Admin!")
    d.delete(u); d.commit(); return {"ok": True}
@app.get("/api/products")
def get_products(u: User = Depends(current_user), d: Session = Depends(dbdep)): return [{"id": p.id, "nome": p.nome, "categoria": p.categoria, "preco": p.preco, "custo": p.custo if u.is_admin else 0, "stock": p.stock, "stock_minimo": p.stock_minimo, "foto": p.foto, "descricao": p.descricao} for p in d.query(Product).order_by(Product.nome).all()]
@app.post("/api/products")
def add_product(x: ProdIn, a: User = Depends(admin_only), d: Session = Depends(dbdep)):
    p = Product(**x.model_dump()); p.updated_by = a.nome; d.add(p); d.commit(); return {"ok": True}
@app.put("/api/products/{pid}")
def edit_product(pid: int, x: ProdIn, a: User = Depends(admin_only), d: Session = Depends(dbdep)):
    p = d.get(Product, pid)
    if not p: raise HTTPException(404, "Não existe")
    dados = x.model_dump()
    if not dados.get("foto"): dados.pop("foto")
    for k, v in dados.items(): setattr(p, k, v)
    p.updated_by = a.nome; p.updated_at = agora(); d.commit(); return {"ok": True}
@app.delete("/api/products/{pid}")
def del_product(pid: int, a: User = Depends(admin_only), d: Session = Depends(dbdep)):
    p = d.get(Product, pid)
    if not p: raise HTTPException(404, "Não existe")
    d.delete(p); d.commit(); return {"ok": True}
@app.post("/api/producao")
def registar_producao(x: ProducaoIn, u: User = Depends(funcionario_only), d: Session = Depends(dbdep)):
    p = d.get(Product, x.produto_id)
    if not p: raise HTTPException(404, "Produto não existe")
    p.stock += x.qtd; p.updated_by = u.nome; p.updated_at = agora(); d.commit(); log_action(d, u.nome, u.tipo, "producao", f"Produziu {p.nome} x{x.qtd} - {x.obs}"); return {"ok": True, "stock": p.stock}
@app.get("/api/fornecedores")
def get_forn(u: User = Depends(funcionario_only), d: Session = Depends(dbdep)): return [{"id": f.id, "nome": f.nome, "telefone": f.telefone, "produto": f.produto, "preco": f.preco, "localizacao": f.localizacao} for f in d.query(Fornecedor).all()]
@app.post("/api/fornecedores")
def add_forn(x: FornIn, a: User = Depends(admin_only), d: Session = Depends(dbdep)):
    f = Fornecedor(**x.model_dump()); d.add(f); d.commit(); return {"ok": True}
@app.post("/api/compras")
def add_compra(x: CompraIn, u: User = Depends(funcionario_only), d: Session = Depends(dbdep)):
    f = d.get(Fornecedor, x.fornecedor_id)
    if not f: raise HTTPException(404, "Fornecedor não existe")
    total = x.qtd * x.preco_unitario; c = Compra(fornecedor=f.nome, produto=x.produto, qtd=x.qtd, preco_unitario=x.preco_unitario, total=total, pagamento=x.pagamento, comprado_por=u.nome); d.add(c); d.commit(); log_action(d, u.nome, u.tipo, "compra", f"{x.produto} x{x.qtd} = {total} MT"); return {"ok": True, "total": total}
# CORREÇÃO 3 - Faltavam GET /api/vendas, /api/compras, /api/despesas
@app.get("/api/vendas")
def listar_vendas(u: User = Depends(funcionario_only), d: Session = Depends(dbdep)):
    return [{"id": v.id, "cliente": v.cliente, "produto": v.produto, "qtd": v.qtd, "total": v.total, "pagamento": v.pagamento, "estado": v.estado, "data": v.created_at.strftime("%d/%m/%Y %H:%M")} for v in d.query(Venda).order_by(Venda.created_at.desc()).limit(100).all()]
@app.get("/api/compras")
def listar_compras(u: User = Depends(funcionario_only), d: Session = Depends(dbdep)):
    return [{"id": c.id, "fornecedor": c.fornecedor, "produto": c.produto, "qtd": c.qtd, "total": c.total, "pagamento": c.pagamento} for c in d.query(Compra).order_by(Compra.created_at.desc()).limit(100).all()]
@app.get("/api/despesas")
def listar_despesas(u: User = Depends(funcionario_only), d: Session = Depends(dbdep)):
    return [{"id": x.id, "descricao": x.descricao, "valor": x.valor, "categoria": x.categoria, "criado_por": x.criado_por} for x in d.query(Despesa).order_by(Despesa.created_at.desc()).limit(100).all()]
@app.post("/api/vendas")
def add_venda(x: VendaIn, u: User = Depends(funcionario_only), d: Session = Depends(dbdep)):
    p = d.get(Product, x.produto_id)
    if not p: raise HTTPException(404, "Produto não existe")
    if p.stock < x.qtd: raise HTTPException(400, f"Stock insuficiente! Só tem {p.stock}")
    p.stock -= x.qtd; total = p.preco * x.qtd; custo = p.custo * x.qtd; lucro = total - custo
    estado = "Dívida" if "Fiado" in x.pagamento or "Dívida" in x.pagamento else "Pago"
    msg = f"Ola {x.cliente}! Obrigado pela compra na Tongas. {p.nome} x{x.qtd} = {total} MT. Pagamento: {x.pagamento}. Volte sempre!"
    wa = whatsapp_link(x.cliente_tel, msg) if x.cliente_tel else ""
    v = Venda(cliente=x.cliente, cliente_tel=x.cliente_tel, vendedor=u.nome, produto=p.nome, qtd=x.qtd, total=total, custo_total=custo, lucro=lucro, pagamento=x.pagamento, estado=estado, data_pagamento=x.data_pagamento, whatsapp_link=wa); d.add(v); d.commit(); log_action(d, u.nome, u.tipo, "venda", f"{p.nome} x{x.qtd} = {total} MT")
    cli = d.query(User).filter_by(telefone=clean_tel(x.cliente_tel)).first() if x.cliente_tel else None
    if cli: cli.pontos += int(total // 100); d.commit()
    return {"ok": True, "total": total, "lucro": lucro, "venda_id": v.id, "whatsapp_link": wa}
@app.post("/api/vendas/{vid}/pagar")
def pagar(vid: int, u: User = Depends(funcionario_only), d: Session = Depends(dbdep)):
    v = d.get(Venda, vid)
    if not v: raise HTTPException(404, "Não existe")
    v.estado = "Pago"; d.commit(); return {"ok": True}
@app.post("/api/vendas/{vid}/anular")
def anular_venda(vid: int, a: User = Depends(admin_only), d: Session = Depends(dbdep)):
    v = d.get(Venda, vid)
    if not v: raise HTTPException(404, "Não existe")
    p = d.query(Product).filter_by(nome=v.produto).first()
    if p: p.stock += v.qtd
    d.delete(v); d.commit(); log_action(d, a.nome, "Admin", "anular_venda", f"Anulou venda #{vid}"); return {"ok": True}
@app.post("/api/despesas")
def add_despesa(x: DespesaIn, u: User = Depends(funcionario_only), d: Session = Depends(dbdep)):
    ds = Despesa(**x.model_dump(), criado_por=u.nome); d.add(ds); d.commit(); return {"ok": True}
@app.get("/api/encomendas")
def get_enc(u: User = Depends(current_user), d: Session = Depends(dbdep)):
    q = d.query(Encomenda)
    if normalizar_tipo(u.tipo) == "Cliente" and not u.is_admin: q = q.filter_by(telefone=u.telefone)
    return [{"id": e.id, "cliente": e.cliente, "telefone": e.telefone, "tipo": e.tipo, "personalizacao": e.personalizacao, "data_entrega": e.data_entrega, "hora_entrega": e.hora_entrega, "modo": e.modo, "preco": e.preco, "sinal": e.sinal, "obs": e.obs, "estado": e.estado, "whatsapp_link": whatsapp_link(e.telefone, f"Ola {e.cliente}! A tua encomenda {e.tipo} esta {e.estado}. Entrega: {e.data_entrega} {e.hora_entrega}. - Tongas")} for e in q.order_by(Encomenda.created_at.desc()).all()]
@app.post("/api/encomendas")
def add_enc(x: EncIn, u: User = Depends(current_user), d: Session = Depends(dbdep)):
    if not x.data_entrega: raise HTTPException(400, "Escolhe a data de entrega!")
    prod = d.query(Product).filter_by(nome=x.tipo).first(); preco_base = prod.preco if prod else 0
    e = Encomenda(cliente=x.cliente or u.nome, telefone=x.telefone or u.telefone, tipo=x.tipo, personalizacao=x.personalizacao, data_entrega=x.data_entrega, hora_entrega=x.hora_entrega, modo=x.modo, preco=preco_base, sinal=x.sinal, obs=x.obs, estado="Recebida"); d.add(e); d.commit(); log_action(d, u.nome, u.tipo, "encomenda", f"{x.tipo} para {x.data_entrega}"); return {"ok": True, "preco_base": preco_base, "msg": "Encomenda recebida!"}
@app.post("/api/encomendas/{eid}/estado")
def mudar_estado_enc(eid: int, estado: str, u: User = Depends(funcionario_only), d: Session = Depends(dbdep)):
    e = d.get(Encomenda, eid)
    if not e: raise HTTPException(404, "Não existe")
    e.estado = estado; d.commit(); return {"ok": True}
@app.post("/api/encomendas/{eid}/cancelar")
def cancelar_enc(eid: int, u: User = Depends(current_user), d: Session = Depends(dbdep)):
    e = d.get(Encomenda, eid)
    if not e: raise HTTPException(404, "Não existe")
    if normalizar_tipo(u.tipo) == "Cliente" and e.telefone != u.telefone and not u.is_admin: raise HTTPException(403, "Só podes cancelar as tuas encomendas")
    if e.estado in ["Entregue","Pronta"]: raise HTTPException(400, "Já não podes cancelar - já está pronta/entregue.")
    e.estado = "Cancelada"; d.commit(); return {"ok": True}
@app.get("/api/meu-historico")
def meu_historico(u: User = Depends(current_user), d: Session = Depends(dbdep)):
    vendas = d.query(Venda).filter_by(cliente_tel=u.telefone).order_by(Venda.created_at.desc()).all() if normalizar_tipo(u.tipo)=="Cliente" else d.query(Venda).order_by(Venda.created_at.desc()).limit(50).all()
    return [{"id": v.id, "produto": v.produto, "qtd": v.qtd, "total": v.total, "pagamento": v.pagamento, "estado": v.estado, "data": v.created_at.strftime("%d/%m/%Y %H:%M")} for v in vendas]
@app.post("/api/sugestoes")
def add_sugestao(x: SugestaoIn, u: User = Depends(current_user), d: Session = Depends(dbdep)):
    if not x.texto.strip(): raise HTTPException(400, "Escreve a tua mensagem!")
    s = Sugestao(cliente=u.nome, texto=x.texto.strip(), tipo=x.tipo); d.add(s); d.commit(); return {"ok": True}
@app.get("/api/sugestoes")
def get_sugestao(a: User = Depends(admin_only), d: Session = Depends(dbdep)): return [{"id": s.id, "cliente": s.cliente, "texto": s.texto, "tipo": s.tipo, "data": s.created_at.strftime("%d/%m/%Y")} for s in d.query(Sugestao).order_by(Sugestao.created_at.desc()).all()]
@app.get("/api/financeiro")
def financeiro(u: User = Depends(funcionario_only), d: Session = Depends(dbdep)):
    vendas = d.query(Venda).order_by(Venda.created_at.desc()).limit(300).all(); despesas = d.query(Despesa).order_by(Despesa.created_at.desc()).limit(300).all(); compras = d.query(Compra).order_by(Compra.created_at.desc()).limit(300).all()
    return {"vendas": [{"id": v.id, "cliente": v.cliente, "vendedor": v.vendedor, "produto": v.produto, "qtd": v.qtd, "total": v.total, "lucro": v.lucro, "pagamento": v.pagamento, "estado": v.estado, "data": v.created_at.isoformat()} for v in vendas], "despesas": [{"id": x.id, "descricao": x.descricao, "valor": x.valor, "categoria": x.categoria, "criado_por": x.criado_por} for x in despesas], "compras": [{"id": c.id, "fornecedor": c.fornecedor, "produto": c.produto, "qtd": c.qtd, "total": c.total, "pagamento": c.pagamento, "comprado_por": c.comprado_por} for c in compras], "dividas": [{"id": v.id, "cliente": v.cliente, "produto": v.produto, "total": v.total, "data_pagamento": v.data_pagamento} for v in vendas if v.estado=="Dívida"], "resumo": {"entradas": sum(v.total for v in vendas), "saidas": sum(x.valor for x in despesas), "compras_total": sum(c.total for c in compras), "lucro_liquido": sum(v.total for v in vendas) - sum(c.total for c in compras) - sum(x.valor for x in despesas), "dividas": sum(v.total for v in vendas if v.estado=="Dívida")}}
# CORREÇÃO 5 - Dashboard agora funciona para Cliente também (versão limitada)
@app.get("/api/dashboard")
def dashboard(u: User = Depends(current_user), d: Session = Depends(dbdep)):
    vendas = d.query(Venda).all(); produtos = d.query(Product).all(); users = d.query(User).all(); despesas = d.query(Despesa).all(); compras = d.query(Compra).all(); hoje = date.today()
    def soma(dia):
        vs = [x for x in vendas if x.created_at.date() == dia]; cs = [x for x in compras if x.created_at.date() == dia]; ds = [x for x in despesas if x.created_at.date() == dia]
        return {"data": dia.isoformat(), "label": dia.strftime("%d/%m"), "vendas": sum(x.total for x in vs), "lucro": sum(x.lucro for x in vs) - sum(x.total for x in cs) - sum(x.valor for x in ds), "n": len(vs)}
    ult7 = [soma(hoje - timedelta(days=i)) for i in range(6, -1, -1)]
    cont = {}
    for v in vendas: cont[v.produto] = cont.get(v.produto, 0) + v.qtd
    mais = sorted(cont.items(), key=lambda x: x[1], reverse=True)[:5]
    por_pag = {}
    for v in vendas: por_pag[v.pagamento] = por_pag.get(v.pagamento, 0) + v.total
    is_cli = normalizar_tipo(u.tipo) == "Cliente" and not u.is_admin
    return {"hoje": ult7[-1], "semana": {"vendas": 0 if is_cli else sum(x["vendas"] for x in ult7), "lucro": 0 if is_cli else sum(x["lucro"] for x in ult7)}, "mes": {"vendas": 0 if is_cli else sum(x.total for x in vendas if x.created_at.month == hoje.month), "lucro": 0 if is_cli else sum(x.lucro for x in vendas if x.created_at.month == hoje.month) - sum(x.total for x in compras if x.created_at.month == hoje.month) - sum(x.valor for x in despesas if x.created_at.month == hoje.month)}, "grafico": ult7 if not is_cli else [{"data": g["data"], "label": g["label"], "vendas": 0, "lucro": 0, "n": 0} for g in ult7], "mais_vendidos": [{"produto": k, "qtd": v} for k, v in mais], "por_pagamento": {} if is_cli else por_pag, "totais": {"clientes": len([x for x in users if x.tipo == "Cliente"]), "funcionarios": len([x for x in users if normalizar_tipo(x.tipo) == "Funcionário"]), "produtos": len(produtos), "vendas_total": 0 if is_cli else sum(v.total for v in vendas), "lucro_liquido": 0 if is_cli else sum(v.total for v in vendas) - sum(c.total for c in compras) - sum(x.valor for x in despesas), "dividas": 0 if is_cli else sum(v.total for v in vendas if v.estado == "Dívida")}}
@app.get("/api/recibo/venda/{vid}")
def recibo_venda_pdf(vid: int, d: Session = Depends(dbdep)):
    v = d.get(Venda, vid)
    if not v: raise HTTPException(404, "Não existe")
    pdf = FPDF(); pdf.add_page(); pdf.set_font("Helvetica", "B", 18); pdf.cell(0, 12, "TONGAS BBQ", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "", 11); pdf.cell(0, 8, f"Recibo Venda #{vid} - {v.created_at.strftime('%d/%m/%Y %H:%M')}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(0, 8, f"Cliente: {v.cliente} | Vendedor: {v.vendedor}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"Produto: {v.produto} x{v.qtd} | Pagamento: {v.pagamento} | Estado: {v.estado}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 14); pdf.cell(0, 12, f"TOTAL: {v.total} MT", new_x="LMARGIN", new_y="NEXT")
    out = bytes(pdf.output()); return Response(content=out, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=recibo_venda_{vid}.pdf"})
@app.get("/api/export/excel")
def export_excel(a: User = Depends(admin_only), d: Session = Depends(dbdep)):
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Vendas"; ws.append(["Data","Cliente","Vendedor","Produto","Qtd","Total MT","Lucro MT","Pagamento","Estado"])
    for v in d.query(Venda).all(): ws.append([v.created_at.strftime("%d/%m/%Y %H:%M"), v.cliente, v.vendedor, v.produto, v.qtd, v.total, v.lucro, v.pagamento, v.estado])
    ws2 = wb.create_sheet("Produtos"); ws2.append(["Produto","Categoria","Preco MT","Custo MT","Stock"])
    for p in d.query(Product).all(): ws2.append([p.nome, p.categoria, p.preco, p.custo, p.stock])
    buf = io.BytesIO(); wb.save(buf); buf.seek(0)
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=tongas.xlsx"})
@app.get("/api/admin/painel")
def painel_admin(a: User = Depends(admin_only), d: Session = Depends(dbdep)):
    vendas = d.query(Venda).order_by(Venda.created_at.desc()).limit(100).all(); compras = d.query(Compra).order_by(Compra.created_at.desc()).limit(100).all(); logs = d.query(Log).order_by(Log.created_at.desc()).limit(300).all()
    total_v = sum(v.total for v in d.query(Venda).all()); total_c = sum(c.total for c in d.query(Compra).all()); total_d = sum(x.valor for x in d.query(Despesa).all())
    return {"resumo": {"total_vendas": total_v, "lucro_bruto": sum(v.lucro for v in d.query(Venda).all()), "total_compras": total_c, "total_despesas": total_d, "lucro_liquido_final": total_v - total_c - total_d, "dividas": sum(v.total for v in d.query(Venda).all() if v.estado == "Dívida")}, "ultimas_vendas": [{"id": v.id, "data": v.created_at.strftime("%d/%m/%Y"), "hora": v.created_at.strftime("%H:%M:%S"), "cliente": v.cliente, "vendedor": v.vendedor, "produto": v.produto, "qtd": v.qtd, "total": v.total, "lucro": v.lucro, "pagamento": v.pagamento, "estado": v.estado} for v in vendas], "ultimas_compras": [{"id": c.id, "data": c.created_at.strftime("%d/%m/%Y"), "fornecedor": c.fornecedor, "produto": c.produto, "qtd": c.qtd, "total": c.total, "comprado_por": c.comprado_por} for c in compras], "fluxo": [{"data": l.created_at.strftime("%d/%m/%Y %H:%M:%S"), "quem": l.quem, "tipo": l.tipo, "acao": l.acao, "detalhe": l.detalhe} for l in logs]}
@app.get("/api/backup")
def backup(a: User = Depends(admin_only), d: Session = Depends(dbdep)): return {"users": [{"nome": u.nome, "telefone": u.telefone, "tipo": u.tipo} for u in d.query(User).all()], "products": [{"nome": p.nome, "preco": p.preco, "stock": p.stock} for p in d.query(Product).all()], "vendas": [{"cliente": v.cliente, "produto": v.produto, "total": v.total, "data": str(v.created_at)} for v in d.query(Venda).all()]}

# CORREÇÃO 6 - Porta do Render
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
