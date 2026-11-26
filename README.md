# 🍞 TONGA'S BBQ - Sistema de Gestão de Padaria 

Sistema completo para padaria / lanchonete em Matola, Moçambique.

### Papéis
- **Cliente:** Ver produtos, comprar, encomendar, ver Minhas Encomendas, histórico, pontos, sugestões. NÃO vê dashboard, stock, finanças.
- **Funcionário:** Vender, caixa, encomendas, stock, produção. NÃO vê lucro, financeiro completo, não cria utilizadores, não altera preços, não faz backup.
- **Admin:** Tudo. Utilizadores, produtos, stock, produção, vendas, financeiro, relatórios, backup, configurações.

### Login Demo
- Admin: `840000000` / `Tongas12345`
- Cliente: cria conta nova

### Como correr local
```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000 --reload