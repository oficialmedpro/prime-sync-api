# ✅ Correção Aplicada - 27/10/2025

## 🔍 Problema Identificado

**Cliente 9999999 EXISTE no Firebird e é LEGÍTIMO!**

```
Código: 9999999
Nome: VENDA AO CONSUMIDOR
Status: Ativo
```

- É um **cliente especial** do sistema Prime
- Usado para vendas sem cadastro completo de cliente
- **NÃO deve ser deletado** do Supabase!

### **Clientes Reais:**
- Total: **37.366 clientes** ativos
- Faixa normal: **1 até 37.457**
- Cliente especial: **9999999** (VENDA AO CONSUMIDOR)

---

## ❌ Problema na Lógica Antiga

```python
# ANTES (ERRADO):
ultimo_codigo = MAX(codigo_cliente_original)  # Retorna 9999999
WHERE CODIGO > 9999999  # Não encontra nada! ❌
```

**Resultado:** Nenhum cliente novo sincronizado

---

## ✅ Correção Aplicada

### **Alteração 1: Função `get_ultimo_id_supabase()`**

**Arquivo:** `app.py` (linhas 70-104)

```python
# DEPOIS (CORRETO):
def get_ultimo_id_supabase(tabela, campo_id='codigo_cliente_original'):
    """Pega o maior ID já migrado (ignorando códigos especiais > 500000)"""
    params = {
        'select': campo_id,
        'order': f'{campo_id}.desc',
        'limit': 1
    }
    
    # Para clientes, ignorar códigos especiais (> 500000)
    if tabela == 'prime_clientes':
        params[campo_id] = 'lt.500000'  # Busca apenas códigos < 500000
    
    # ... resto do código
```

**O que faz:**
- Busca o último código **IGNORANDO** códigos > 500000
- Retorna 37457 (último cliente real) em vez de 9999999
- Adiciona log informativo sobre códigos especiais

---

### **Alteração 2: Query Firebird em `sync_clientes_novos()`**

**Arquivo:** `app.py` (linha 146)

```sql
-- ANTES:
WHERE C.ATIVO = -1
AND C.CODIGO > {ultimo_codigo}

-- DEPOIS:
WHERE C.ATIVO = -1
AND C.CODIGO > {ultimo_codigo}
AND C.CODIGO < 500000  -- ← NOVO: Ignora códigos especiais
```

**O que faz:**
- Garante que só busca clientes com códigos normais
- Evita sincronizar o cliente especial 9999999 repetidamente
- Mantém a sincronização incremental funcionando

---

## 📊 Resultado Esperado

### **Antes da Correção:**
```
📊 Clientes - Último código: 9999999 ❌
📋 Clientes: {'inseridos': 0, 'mensagem': 'Nenhum cliente novo'} ❌
```

### **Depois da Correção:**
```
📊 Clientes - Último código: 37457 ✅
   (Ignorando códigos especiais > 500000)
✅ Encontrados X clientes novos
📋 Clientes: {'inseridos': X, 'mensagem': 'X clientes sincronizados'} ✅
```

---

## 🚀 Próximos Passos

### **1️⃣ Testar Localmente (RECOMENDADO)**

```bash
cd "C:\Banco de Dados Prime\sync-api"

# Configurar variáveis
$env:FIREBIRD_PASS="Lt-@=waIh))Ql3~"
$env:SUPABASE_URL="sua-url"
$env:SUPABASE_KEY="sua-key"

# Testar
py app.py
```

**Aguardar 30 segundos** e verificar se sincroniza clientes.

---

### **2️⃣ Build da Imagem Docker**

```bash
cd "C:\Banco de Dados Prime\sync-api"

# Build
docker build -t oficialmedpro/prime-sync-api:latest .

# Push para registry
docker push oficialmedpro/prime-sync-api:latest
```

---

### **3️⃣ Update no Portainer**

**Via Interface:**
1. Acesse: https://portainer.oficialmed.com.br
2. Navegue: **Stacks** → **prime-sync-api**
3. Clique: **Editor** (botão azul)
4. **NÃO altere nada**, apenas clique: **Update the stack** (no final da página)
5. Aguarde o container reiniciar (~30 segundos)

**Via SSH:**
```bash
docker service update --force prime-sync-api_prime-sync-api
```

---

### **4️⃣ Verificar Logs**

```bash
# Aguardar 2 minutos (para cronjob executar)

# Ver logs
docker service logs prime-sync-api_prime-sync-api --tail 100

# Procurar por:
# "📊 Clientes - Último código: 37457"
# "✅ Encontrados X clientes novos"
```

---

### **5️⃣ Validar no Supabase**

```sql
SELECT 
    COUNT(*) as total,
    MAX(codigo_cliente_original) as ultimo_codigo,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '1 hour') as ultima_hora,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as ultimas_24h
FROM api.prime_clientes
WHERE codigo_cliente_original < 500000;  -- Apenas clientes normais
```

**Resultado esperado:**
- `ultima_hora > 0` ✅
- `ultimo_codigo` crescendo (37458, 37459, etc)

---

## 🔧 Correção Adicional: tipos_processo

### **Problema:**
- HTTP 409 ao tentar inserir tipos duplicados
- Tipos de processo são **configurações** (não dados transacionais)

### **Solução Recomendada:**

#### **A) Adicionar UNIQUE CONSTRAINT no Supabase**

```sql
ALTER TABLE api.prime_tipos_processo
ADD CONSTRAINT unique_codigo_tipo_original 
UNIQUE (codigo_tipo_original);
```

#### **B) Modificar app.py para usar UPSERT**

```python
# Alterar linha ~758 (headers)
headers_upsert = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Accept-Profile': 'api',
    'Content-Profile': 'api',
    'Prefer': 'resolution=merge-duplicates,return=representation'  # ← UPSERT
}

# Usar headers_upsert no POST
response = requests.post(url, headers=headers_upsert, json=tipos_dados, timeout=60)
```

#### **C) Otimizar: Sincronizar apenas se necessário**

```python
def sync_tipos_processo_novos():
    # Buscar total no Firebird
    cursor.execute("SELECT COUNT(*) FROM FORMAFARMACEUTICA_PROCESSO_TIPO WHERE ATIVO = -1")
    total_firebird = cursor.fetchone()[0]
    
    # Buscar total no Supabase
    total_supabase = get_total_supabase('prime_tipos_processo')
    
    # Se iguais, não sincronizar
    if total_firebird == total_supabase:
        return {'inseridos': 0, 'mensagem': 'Tipos já sincronizados'}
    
    # Se diferentes, fazer UPSERT completo
    ...
```

---

## 📝 Arquivos Modificados

| Arquivo | Alteração | Linhas |
|---------|-----------|--------|
| `app.py` | Função `get_ultimo_id_supabase()` | 70-104 |
| `app.py` | Query `sync_clientes_novos()` | 146 |

---

## 📁 Arquivos Criados

| Arquivo | Descrição |
|---------|-----------|
| `verificar_cliente_9999999_simples.py` | Script que verificou o Firebird |
| `correcao_logica_clientes.py` | Documentação da correção |
| `CORRECAO_APLICADA_27-10-2025.md` | Este documento |

---

## ✅ Checklist de Deploy

- [x] Identificado problema (cliente 9999999 é legítimo)
- [x] Modificado `app.py` (ignorar códigos > 500000)
- [ ] Testar localmente (executar `py app.py`)
- [ ] Build Docker (`docker build`)
- [ ] Push para registry (`docker push`)
- [ ] Update no Portainer
- [ ] Verificar logs (aguardar 2 minutos)
- [ ] Validar no Supabase (inserções na última hora > 0)
- [ ] Aplicar correção de tipos_processo (UPSERT)
- [ ] Documentar data/hora da correção

---

## 🎯 Validação de Sucesso

**A correção funcionou se você ver nos logs:**

```
📊 Clientes - Último código: 37457
   (Ignorando códigos especiais > 500000)
✅ Encontrados 5 clientes novos
📋 Clientes: {'inseridos': 5, 'mensagem': '5 clientes sincronizados'}
```

**E no Supabase:**

```sql
SELECT COUNT(*) FROM api.prime_clientes 
WHERE created_at > NOW() - INTERVAL '1 hour';
-- Resultado: > 0 ✅
```

---

## 📞 Troubleshooting

### ❌ Ainda mostra código 9999999

**Causa:** Imagem Docker não foi atualizada

**Solução:**
1. Verificar se fez `docker build` e `docker push`
2. Forçar pull da nova imagem:
```bash
docker service update --image oficialmedpro/prime-sync-api:latest prime-sync-api_prime-sync-api
```

---

### ❌ Mostra código 37457 mas inseridos: 0

**Causa:** Pode não haver clientes novos realmente

**Verificar:**
```sql
-- No Firebird
SELECT COUNT(*) FROM CLIENTE 
WHERE ATIVO = -1 
AND CODIGO > 37457 
AND CODIGO < 500000;
```

Se retornar 0 → Realmente não há clientes novos ✅

---

## 🎉 Conclusão

**Sua análise estava 100% correta!**

- ✅ Verificar ANTES de deletar
- ✅ Cliente 9999999 é legítimo
- ✅ Solução foi ajustar a lógica, não deletar dados
- ✅ tipos_processo precisa de UPSERT, não INSERT

**Próxima ação:** Build e deploy da correção! 🚀

---

_Correção documentada em: 27/10/2025_
_Aplicada por: Assistente IA_
_Aprovada por: Usuário (após validação no Firebird)_

