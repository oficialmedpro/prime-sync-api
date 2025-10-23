# 🔄 API de Sincronização Incremental - Prime → Supabase

Sistema automatizado de sincronização incremental entre Firebird (Prime) e Supabase PostgreSQL.

## 📋 Características

- ✅ **Sincronização Incremental** - Apenas novos registros
- ✅ **API REST** - Endpoint HTTP fácil de chamar
- ✅ **Docker** - Deploy fácil com Portainer
- ✅ **Failover Automático** - beta.oficialmed.com.br → bi.oficialmed.com.br
- ✅ **Health Check** - Monitoramento automático
- ✅ **Cronjob Supabase** - Execução automática agendada

---

## 🚀 Deploy no Portainer

### 1. Fazer Upload dos Arquivos

Copie toda a pasta `sync-api` para o servidor.

### 2. Deploy via Portainer

1. Acesse Portainer
2. Vá em **Stacks** → **Add Stack**
3. Nome: `prime-sync-api`
4. **Build method**: Repository ou Upload
5. Cole o conteúdo do `docker-compose.yml`
6. Clique em **Deploy the stack**

### 3. Verificar se Está Rodando

```bash
curl http://beta.oficialmed.com.br/health
# ou
curl http://bi.oficialmed.com.br/health
```

Resposta esperada:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-23T17:00:00",
  "version": "1.0.0"
}
```

---

## 🔧 Configuração do Cronjob no Supabase

### Opção 1: Usando pg_cron (Recomendado)

1. Acesse o **SQL Editor** do Supabase
2. Execute este SQL:

```sql
-- Habilitar pg_cron (apenas uma vez)
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Criar função que chama a API com failover
CREATE OR REPLACE FUNCTION sync_prime_data()
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
  response_beta TEXT;
  response_bi TEXT;
BEGIN
  -- Tentar beta.oficialmed.com.br primeiro
  BEGIN
    SELECT content INTO response_beta
    FROM http_post(
      'https://beta.oficialmed.com.br/sync',
      '{}',
      'application/json'
    );

    -- Se chegou aqui, sucesso!
    RAISE NOTICE 'Sincronização via beta.oficialmed.com.br: %', response_beta;
    RETURN;

  EXCEPTION WHEN OTHERS THEN
    -- Falhou, tentar bi.oficialmed.com.br
    RAISE NOTICE 'Falha em beta, tentando bi.oficialmed.com.br...';

    SELECT content INTO response_bi
    FROM http_post(
      'https://bi.oficialmed.com.br/sync',
      '{}',
      'application/json'
    );

    RAISE NOTICE 'Sincronização via bi.oficialmed.com.br: %', response_bi;
  END;
END;
$$;

-- Agendar execução a cada 15 minutos
SELECT cron.schedule(
  'sync-prime-incremental',
  '*/15 * * * *',  -- A cada 15 minutos
  'SELECT sync_prime_data();'
);
```

### Opção 2: Usando Supabase Edge Functions

Crie uma Edge Function que chama a API:

```typescript
// supabase/functions/sync-prime/index.ts
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

serve(async (req) => {
  const urls = [
    'https://beta.oficialmed.com.br/sync',
    'https://bi.oficialmed.com.br/sync'
  ];

  for (const url of urls) {
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer prime-sync-2025'
        }
      });

      const data = await response.json();

      return new Response(
        JSON.stringify({ success: true, url, data }),
        { headers: { "Content-Type": "application/json" } }
      );

    } catch (error) {
      console.error(`Falha em ${url}:`, error);
      continue; // Tenta próximo
    }
  }

  return new Response(
    JSON.stringify({ success: false, error: 'Todos os endpoints falharam' }),
    { status: 500, headers: { "Content-Type": "application/json" } }
  );
})
```

Depois agende via cron:
```bash
cron: "*/15 * * * *"  # A cada 15 minutos
```

### Opção 3: Webhook Externo (Make/Zapier)

Configure um webhook no Make.com ou Zapier:

1. **Trigger**: Schedule (a cada 15 min)
2. **Action**: HTTP Request
   - URL 1: `https://beta.oficialmed.com.br/sync`
   - URL 2 (fallback): `https://bi.oficialmed.com.br/sync`
   - Method: POST
   - Headers: `Authorization: Bearer prime-sync-2025`

---

## 📊 Endpoints Disponíveis

### GET/POST `/sync`

Executa sincronização incremental.

**Request:**
```bash
curl -X POST https://beta.oficialmed.com.br/sync \
  -H "Authorization: Bearer prime-sync-2025"
```

**Response:**
```json
{
  "sucesso": true,
  "timestamp": "2025-10-23T17:00:00",
  "tempo_execucao_segundos": 2.5,
  "clientes": {
    "inseridos": 15,
    "mensagem": "15 clientes novos sincronizados"
  },
  "pedidos": {
    "inseridos": 8,
    "mensagem": "8 pedidos novos sincronizados"
  },
  "total_inseridos": 23
}
```

### GET `/health`

Health check do serviço.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-23T17:00:00",
  "version": "1.0.0"
}
```

---

## 🔒 Segurança

### Token de API

O endpoint está protegido por token. Configure no `.env`:

```env
API_TOKEN=seu-token-super-secreto-aqui
```

Envie no header:
```
Authorization: Bearer seu-token-super-secreto-aqui
```

### Firewall

Recomenda-se configurar firewall para aceitar apenas:
- IP do Supabase
- IPs conhecidos da sua rede

---

## 🐛 Troubleshooting

### Container não inicia

```bash
# Ver logs
docker logs prime-sync-api

# Verificar status
docker ps -a | grep prime-sync
```

### Endpoint não responde

```bash
# Testar localmente
curl http://localhost:5000/health

# Ver logs em tempo real
docker logs -f prime-sync-api
```

### Firebird não conecta

Verifique as variáveis de ambiente no `docker-compose.yml`:
- `FIREBIRD_HOST`
- `FIREBIRD_USER`
- `FIREBIRD_PASS`

---

## 📈 Monitoramento

### Logs

```bash
# Ver logs
docker logs prime-sync-api

# Seguir logs em tempo real
docker logs -f prime-sync-api
```

### Métricas

O endpoint `/sync` retorna:
- Tempo de execução
- Quantidade de registros inseridos
- Eventuais erros

---

## 🔄 Atualizar a Aplicação

```bash
# 1. Fazer pull das mudanças
cd sync-api

# 2. Rebuild
docker-compose build

# 3. Restart
docker-compose up -d
```

---

## 📝 Notas

- **Frequência recomendada**: 15 minutos
- **Timeout**: 300 segundos (5 min)
- **Workers**: 2 (configurável no Dockerfile)
- **Performance**: ~100-500 registros/segundo

---

## 🆘 Suporte

Em caso de problemas:
1. Verificar logs: `docker logs prime-sync-api`
2. Testar health: `curl http://localhost:5000/health`
3. Testar sync manual: `curl -X POST http://localhost:5000/sync`

---

**Criado em**: 23/10/2025
**Versão**: 1.0.0
