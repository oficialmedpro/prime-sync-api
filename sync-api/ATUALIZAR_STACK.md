# 🔄 ATUALIZAR IMAGEM DO STACK

**Data:** 01/11/2025  
**Versão nova:** 2.0.1 (commit `b3ebc8a`)  
**Versão antiga:** commit `7c02624`

---

## 📋 Passo a Passo

### 1. **No Portainer**

Vá em **Stacks** → `prime-sync-api` → **Editor**

### 2. **Atualizar Tag da Imagem**

**Antes:**
```yaml
image: oficialmedpro/prime-sync-api:master-7c02624
```

**Depois:**
```yaml
image: oficialmedpro/prime-sync-api:master-b3ebc8a
```

### 3. **Salvar e Atualizar**

1. Clique em **Update the stack**
2. Confirme a atualização
3. Aguarde o deploy (30-60 segundos)

### 4. **Verificar**

```bash
curl https://sincro.oficialmed.com.br/health
```

**Resposta esperada:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-29T...",
  "version": "2.0.1"
}
```

---

## 🔍 Diferenças da Versão

### v2.0.1 (commit b3ebc8a)

✅ **Melhorias implementadas:**

1. **Try-catch individual** por etapa
2. **Logs numerados** (1/6, 2/6, etc)
3. **Tratamento de erros** não quebra o fluxo
4. **Avisos na resposta** da API
5. **Logging visual** com separadores

---

## ⚠️ Importante

**NÃO MEXER** em:
- Secrets (já configurados)
- Networks (já configuradas)
- Traefik labels (já configuradas)
- Environment variables (já configuradas)
- Health check (já configurado)

**APENAS ALTERAR:**
- Tag da imagem: `master-7c02624` → `master-b3ebc8a`

---

## 🧪 Teste Completo

Após o deploy, execute:

```bash
# 1. Health check
curl https://sincro.oficialmed.com.br/health

# 2. Trigger manual de sync
curl -X POST https://sincro.oficialmed.com.br/sync

# 3. Ver última sincronização
curl https://sincro.oficialmed.com.br/auditoria/historico?limite=1
```

---

**✅ Pronto para deploy!**

