# 🔐 Secrets para Criar no Portainer

## Passo a Passo

1. Acesse Portainer → **Secrets**
2. Clique em **+ Add secret** para cada um abaixo
3. Cole o valor exato (sem espaços ou quebras de linha extras)

---

## Secrets Necessários

### 1. FIREBIRD_PASS
**Nome**: `FIREBIRD_PASS`
**Valor**: `[senha do usuário OFICIALMED no Firebird]`

```
Exemplo: SenhaFirebird123
```

---

### 2. SUPABASE_URL
**Nome**: `SUPABASE_URL`
**Valor**: URL do seu projeto Supabase

```
Exemplo: https://xxxxxxxxxxxxx.supabase.co
```

**Como encontrar:**
- Supabase Dashboard → Project Settings → API → Project URL

---

### 3. SUPABASE_SERVICE_KEY
**Nome**: `SUPABASE_SERVICE_KEY`
**Valor**: Service Role Key (chave secreta do Supabase)

```
Exemplo: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ey...
```

**Como encontrar:**
- Supabase Dashboard → Project Settings → API → `service_role` secret

⚠️ **IMPORTANTE**: Use a `service_role` key, NÃO a `anon` key!

---

### 4. PRIME_SYNC_API_TOKEN
**Nome**: `PRIME_SYNC_API_TOKEN`
**Valor**: Token de segurança para proteger o endpoint `/sync`

```
Sugestão: prime-sync-2025-TOKEN-ALEATORIO-SEGURO
```

**Gere um token seguro:**
```bash
# Opção 1: Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Opção 2: OpenSSL
openssl rand -base64 32

# Opção 3: Use qualquer senha forte
```

⚠️ **Guarde este token!** Será usado no cronjob do Supabase.

---

## Checklist de Criação

- [ ] `FIREBIRD_PASS` - Senha do Firebird
- [ ] `SUPABASE_URL` - URL do projeto Supabase
- [ ] `SUPABASE_SERVICE_KEY` - Service role key do Supabase
- [ ] `PRIME_SYNC_API_TOKEN` - Token de segurança (você cria)

---

## Verificar Secrets

Após criar, liste os secrets no Portainer:

```bash
docker secret ls
```

Deve mostrar:
```
ID          NAME                       CREATED
xxxxx       FIREBIRD_PASS              About a minute ago
xxxxx       SUPABASE_URL               About a minute ago
xxxxx       SUPABASE_SERVICE_KEY       About a minute ago
xxxxx       PRIME_SYNC_API_TOKEN       About a minute ago
```

---

## Usar no Stack

Os secrets já estão configurados no `stack-portainer.yml`:

```yaml
secrets:
  - FIREBIRD_PASS
  - SUPABASE_URL
  - SUPABASE_SERVICE_KEY
  - PRIME_SYNC_API_TOKEN
```

A API lê automaticamente de `/run/secrets/NOME_DO_SECRET`

---

## Atualizar Secret

Se precisar mudar algum valor:

1. **Remover o secret antigo**:
   ```bash
   docker secret rm NOME_DO_SECRET
   ```

2. **Criar novo secret**:
   - Portainer → Secrets → + Add secret

3. **Atualizar o stack**:
   - Portainer → Stacks → prime-sync-api → Update the stack

⚠️ **Nota**: Não é possível editar secrets existentes, apenas remover e recriar.

---

## Segurança

✅ **Boas práticas:**
- Secrets só ficam disponíveis dentro do container
- Não aparecem em logs ou variáveis de ambiente
- Acessíveis em `/run/secrets/` (somente leitura)
- Deletados quando container é removido

❌ **NÃO faça:**
- Não commite secrets no Git
- Não exponha em logs
- Não compartilhe publicamente
- Não use a mesma senha em produção e desenvolvimento

---

**Criado**: 23/10/2025
**Versão**: 1.0.0
