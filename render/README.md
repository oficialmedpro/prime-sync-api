# 🚀 API de Sincronização - Render.com

## 📋 Configuração no Render.com

### 1. Criar Web Service

1. Acesse: https://dashboard.render.com
2. Clique em **"New +"** → **"Web Service"**
3. Conecte ao seu repositório GitHub
4. Configure:
   - **Name:** `prime-sync`
   - **Region:** Escolha a região mais próxima
   - **Branch:** `master` (ou sua branch)
   - **Root Directory:** `render` (ou `.` se estiver na raiz)
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn --bind 0.0.0.0:$PORT app:app`
   - **Plan:** `Free` (Hobby)

### 2. Configurar Variáveis de Ambiente

No Render, vá em **Environment** e adicione:

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

### 3. Deploy

Clique em **"Create Web Service"** e aguarde o deploy (2-5 minutos).

### 4. Testar

Após o deploy, você receberá uma URL tipo: `https://prime-sync.onrender.com`

Teste:
```bash
curl https://prime-sync.onrender.com/health
```

Deve retornar:
```json
{
  "status": "healthy",
  "version": "3.0.0",
  "service": "render.com"
}
```

### 5. Atualizar Supabase (pg_cron)

Execute este SQL no Supabase:

```sql
-- Atualizar função para chamar Render.com
CREATE OR REPLACE FUNCTION api.sync_prime_incremental()
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  v_response http_response;
  v_result json;
BEGIN
  -- Chamar Render.com ao invés de Portainer
  SELECT * INTO v_response
  FROM http((
    'POST',
    'https://prime-sync.onrender.com/sync',  -- URL do Render (substitua pela sua)
    ARRAY[
      http_header('Content-Type', 'application/json'),
      http_header('Authorization', 'Bearer prime-sync-2025-xY9kL2mP4nQ8wR5t')
    ],
    'application/json',
    '{}'
  )::http_request);

  IF v_response.status = 200 THEN
    RETURN v_response.content::json;
  ELSE
    RETURN json_build_object(
      'sucesso', false,
      'erro', 'Falha no Render',
      'status_code', v_response.status
    );
  END IF;
EXCEPTION WHEN OTHERS THEN
  RETURN json_build_object(
    'sucesso', false,
    'erro', SQLERRM,
    'timestamp', now()
  );
END;
$$;
```

## ✅ Pronto!

O pg_cron do Supabase vai chamar o Render.com a cada 30 minutos automaticamente.

## 📊 Monitoramento

- **Logs do Render:** https://dashboard.render.com → Seu serviço → Logs
- **Logs do Supabase:** Execute `SELECT * FROM api.sync_logs ORDER BY timestamp DESC LIMIT 10;`

