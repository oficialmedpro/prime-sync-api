# 🚀 PASSO A PASSO COMPLETO - Render.com

## ✅ O QUE JÁ FOI CRIADO:

1. ✅ `app.py` - Versão simplificada (precisa adicionar todas as funções)
2. ✅ `requirements.txt` - Dependências Python
3. ✅ `atualizar_supabase.sql` - SQL para atualizar o pg_cron
4. ✅ `README.md` - Instruções básicas

## ⚠️ IMPORTANTE:

O `app.py` atual está **simplificado** e só tem `sync_clientes_novos()` básica.

**Você precisa copiar TODAS as funções do `sync-api/app.py` original para o `render/app.py`:**

### Funções que precisam ser copiadas:

1. `sync_clientes_novos()` - ✅ Já tem (mas precisa completar)
2. `sync_pedidos_novos()` - ❌ Copiar do original
3. `sync_formulas_novas()` - ❌ Copiar do original
4. `sync_formulas_itens_novos()` - ❌ Copiar do original
5. `sync_rastreabilidade_nova()` - ❌ Copiar do original
6. `sync_tipos_processo_novos()` - ❌ Copiar do original
7. `sync_missing_clientes()` - ❌ Copiar do original
8. `sync_missing_pedidos()` - ❌ Copiar do original

### Função `/sync` principal:

- Copiar a função `/sync` completa do `sync-api/app.py` original
- Ela chama todas as funções acima na ordem correta

## 🔧 PRÓXIMOS PASSOS:

### 1. Completar o `app.py`:

Copie todas as funções do `sync-api/app.py` para `render/app.py`, EXCETO:
- ❌ `read_secret()` - Não precisa (Render usa env vars direto)
- ❌ `auditoria.py` imports - Opcional (pode remover se não usar)

### 2. Criar serviço no Render.com:

1. Acesse: https://dashboard.render.com
2. Clique em **"New +"** → **"Web Service"**
3. Conecte ao seu repositório GitHub
4. Configure:
   - **Name:** `prime-sync`
   - **Root Directory:** `render` (ou `.` se estiver na raiz)
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn --bind 0.0.0.0:$PORT app:app`
   - **Plan:** `Free` (Hobby)

### 3. Variáveis de Ambiente no Render:

Adicione estas variáveis:

```
FIREBIRD_HOST=db.primesoftware.com.br
FIREBIRD_DB=oficialmed1250
FIREBIRD_USER=OFICIALMED
FIREBIRD_PASS=sua_senha_aqui
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua_service_key_aqui
API_TOKEN=prime-sync-2025-xY9kL2mP4nQ8wR5t
API_VERSION=3.0.0
PORT=10000
```

### 4. Atualizar Supabase:

Execute o SQL do arquivo `atualizar_supabase.sql` no Supabase SQL Editor.

**⚠️ IMPORTANTE:** Substitua `https://prime-sync.onrender.com` pela URL real do seu serviço no Render!

### 5. Testar:

```bash
curl https://sua-url.onrender.com/health
curl -X POST https://sua-url.onrender.com/sync \
  -H "Authorization: Bearer prime-sync-2025-xY9kL2mP4nQ8wR5t"
```

## ✅ RESULTADO:

- ✅ Render.com executa a sincronização
- ✅ pg_cron do Supabase chama o Render a cada 30 minutos
- ✅ Tudo funciona automaticamente!
- ✅ Gratuito no plano Hobby!

