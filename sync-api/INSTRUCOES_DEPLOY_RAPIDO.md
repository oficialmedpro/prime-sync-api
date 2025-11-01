# 🚀 INSTRUÇÕES RÁPIDAS - DEPLOY v2.0.1

## 📍 No Portainer

### 1. Abrir Stack
- **Vá para:** Stacks → `prime-sync-api` → **Editor**

### 2. Atualizar Imagem
**Trocar APENAS esta linha:**

```yaml
# ANTES (versão antiga com bugs):
image: oficialmedpro/prime-sync-api:master-7c02624

# DEPOIS (versão nova corrigida):
image: oficialmedpro/prime-sync-api:master-b3ebc8a
```

### 3. Salvar e Atualizar
- Clique em **Update the stack**
- Aguarde o deploy (30-60 segundos)

### 4. Verificar
```bash
curl https://sincro.oficialmed.com.br/health
```

Deve retornar:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-01T...",
  "version": "2.0.1"  ← DEVE SER 2.0.1
}
```

---

## ✅ O que foi corrigido

- ❌ Antes: Erro `clientes_mestre` não existe  
- ✅ Agora: Usa `prime_clientes` corretamente

- ❌ Antes: Erros quebravam todo o fluxo  
- ✅ Agora: Try-catch individual, continua mesmo com erros

- ❌ Antes: Logging confuso  
- ✅ Agora: Logging numerado e organizado

---

**Qualquer dúvida:** Verifique os logs no Portainer após o deploy

