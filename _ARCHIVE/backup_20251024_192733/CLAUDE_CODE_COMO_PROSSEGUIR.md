# DOCUMENTAÇÃO - Como Prosseguir com a Migração COMPLETA

## STATUS ATUAL (22/10/2025 - 20:35)

### ✅ SCRIPTS CRIADOS E PRONTOS

1. ✅ **Clientes** - `exportar_clientes_rapido_batch.py` (RODANDO)
2. ✅ **Pedidos** - `exportar_pedidos_otimizado.py` (PRONTO)
3. ✅ **Fórmulas** - `exportar_formulas_otimizado.py` (PRONTO)
4. ✅ **Rastreabilidade** - `exportar_rastreabilidade_otimizado.py` (PRONTO)

---

## 🚀 ORDEM DE EXECUÇÃO (IMPORTANTE!)

### 1️⃣ CLIENTES (em andamento)
```bash
# JÁ ESTÁ RODANDO - Aguardar terminar (~25 min restantes)
```
- Total: 37.137 clientes
- Progresso atual: ~18.000 (48%)
- Tempo restante: ~25 minutos

### 2️⃣ PEDIDOS (executar após clientes)
```bash
py "C:\Banco de Dados Prime\exportar_pedidos_otimizado.py"
```
- Total: 16.604 pedidos
- Tempo estimado: ~30-40 minutos
- **IMPORTANTE**: Pedidos precisam dos clientes prontos (FK)

### 3️⃣ FÓRMULAS (executar após pedidos)
```bash
py "C:\Banco de Dados Prime\exportar_formulas_otimizado.py"
```
- Total: ~50.000 fórmulas
- Tempo estimado: ~1 hora
- **IMPORTANTE**: Fórmulas precisam dos pedidos prontos (FK)

### 4️⃣ RASTREABILIDADE (executar após pedidos)
```bash
py "C:\Banco de Dados Prime\exportar_rastreabilidade_otimizado.py"
```
- Total: ~100.000 registros
- Tempo estimado: ~2 horas
- **IMPORTANTE**: Rastreabilidade precisa dos pedidos prontos (FK)

---

## ⚠️ REGRAS IMPORTANTES

### NÃO executar em paralelo:
❌ Clientes + Pedidos juntos
❌ Pedidos + Fórmulas juntos
❌ Qualquer combinação junto

### PODE executar em paralelo (após pedidos):
✅ Fórmulas + Rastreabilidade (ambos dependem de pedidos, não entre si)

---

## 📊 MAPEAMENTO DAS TABELAS

### 1. Clientes
**Firebird**: CLIENTE → **Supabase**: api.prime_clientes
- Total: 37.137 registros
- Campos: nome, cpf_cnpj, telefone, endereço, email, data_nascimento

### 2. Pedidos
**Firebird**: ATENDIMENTO_A1 → **Supabase**: api.prime_pedidos
- Total: 16.604 registros
- Campos: codigo_orcamento_original, cliente_id (FK), valor_total, status_aprovacao, status_entrega, status_geral

### 3. Fórmulas
**Firebird**: ATENDIMENTO_A2 → **Supabase**: api.prime_formulas
- Total: ~50.000 registros
- FK: codigo_pedido_original
- Campos: numero_formula_original, codigo_pedido_original, descricao, posologia, valor

### 4. Rastreabilidade
**Firebird**: PROCESSO_MANIPULACAO → **Supabase**: api.prime_rastreabilidade
- Total: ~100.000 registros
- FK: codigo_pedido_original
- Campos: codigo_rastreabilidade_original, codigo_pedido_original, codigo_processo, data_inicio, data_fim, status, observacoes

---

## 🔧 CONFIGURAÇÕES (Todos os scripts)

```python
FIREBIRD_CONFIG = {
    'host': 'db.primesoftware.com.br',
    'database': 'oficialmed1250',
    'user': 'OFICIALMED',
    'password': 'Lt-@=waIh))Ql3~',
    'charset': 'UTF8'
}

SUPABASE_URL = "https://agdffspstbxeqhqtltvb.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbG..."  # Service role key

BATCH_SIZE = 500  # Todos os scripts usam lotes de 500
```

---

## 🎯 ESTIMATIVA TOTAL DE TEMPO

| Etapa | Registros | Tempo Estimado | Status |
|-------|-----------|----------------|--------|
| Clientes | 37.137 | ~1h | ⏳ Rodando (25 min restantes) |
| Pedidos | 16.604 | ~30-40 min | ⏸️ Aguardando |
| Fórmulas | ~50.000 | ~1h | ⏸️ Aguardando |
| Rastreabilidade | ~100.000 | ~2h | ⏸️ Aguardando |
| **TOTAL** | **~204.000** | **~4-5 horas** | - |

---

## 🔍 COMANDOS DE VERIFICAÇÃO

### Verificar progresso no Supabase:

```sql
-- Contar registros
SELECT COUNT(*) FROM api.prime_clientes;       -- Deve: 37.137
SELECT COUNT(*) FROM api.prime_pedidos;        -- Deve: 16.604
SELECT COUNT(*) FROM api.prime_formulas;       -- Deve: ~50.000
SELECT COUNT(*) FROM api.prime_rastreabilidade; -- Deve: ~100.000

-- Verificar relacionamentos Pedidos
SELECT
    p.codigo_orcamento_original,
    COUNT(f.id) as total_formulas,
    COUNT(r.id) as total_rastreabilidade
FROM api.prime_pedidos p
LEFT JOIN api.prime_formulas f ON p.codigo_orcamento_original = f.codigo_pedido_original
LEFT JOIN api.prime_rastreabilidade r ON p.codigo_orcamento_original = r.codigo_pedido_original
GROUP BY p.codigo_orcamento_original
LIMIT 10;

-- Verificar se todos os pedidos têm cliente
SELECT COUNT(*)
FROM api.prime_pedidos
WHERE cliente_id IS NULL;
-- Deve retornar: 0

-- Verificar status dos pedidos
SELECT status_geral, COUNT(*)
FROM api.prime_pedidos
GROUP BY status_geral;
```

---

## 🐛 PROBLEMAS COMUNS E SOLUÇÕES

### Erro: Foreign Key violation (cliente_id ou codigo_pedido_original)
**Causa**: Tentou executar fora de ordem
**Solução**:
1. Executar na ordem: Clientes → Pedidos → Fórmulas/Rastreabilidade
2. Aguardar cada script terminar antes do próximo

### Erro: "The schema must be one of the following: api"
**Solução**: Headers já configurados corretamente em todos os scripts

### Erro: Unicode characters
**Solução**: Função `limpar_string()` já implementada em todos os scripts

### Script muito lento
**Verificar**: BATCH_SIZE = 500 em todos os scripts

---

## 📝 COMO CONTINUAR AMANHÃ

### Se interromper no meio:

1. **Verificar qual script terminou:**
```bash
# Ver contagens no Supabase
SELECT COUNT(*) FROM api.prime_clientes;
SELECT COUNT(*) FROM api.prime_pedidos;
SELECT COUNT(*) FROM api.prime_formulas;
SELECT COUNT(*) FROM api.prime_rastreabilidade;
```

2. **Continuar de onde parou:**
- Clientes completo (37.137)? → Executar Pedidos
- Pedidos completo (16.604)? → Executar Fórmulas E/OU Rastreabilidade
- Todos completos? → ✅ Migração finalizada!

3. **Scripts usam UPSERT:**
- Pode executar novamente sem problemas
- Atualiza registros existentes
- Insere apenas os que faltam

---

## 🆘 COMANDOS DE EMERGÊNCIA

### Parar script em execução:
```
Ctrl + C no terminal
```

### Limpar tabela e recomeçar (CUIDADO!):
```sql
-- Ordem inversa por causa das FKs
DELETE FROM api.prime_rastreabilidade;
DELETE FROM api.prime_formulas;
DELETE FROM api.prime_pedidos;
DELETE FROM api.prime_clientes;
```

### Ver processos Python rodando:
```bash
tasklist | findstr python
```

---

## 📞 COMO PEDIR AJUDA AO CLAUDE

### Para verificar status:
> "Verifique o status da migração. Quantos clientes/pedidos/fórmulas/rastreabilidade foram migrados?"

### Para continuar:
> "O script de [NOME] terminou. Posso executar o próximo?"

### Para resolver erro:
> "O script [NOME] deu erro: [COLAR ERRO AQUI]. Como resolver?"

---

## ✅ CHECKLIST DE MIGRAÇÃO COMPLETA

- [ ] Clientes (37.137) - em andamento
- [ ] Pedidos (16.604) - aguardando
- [ ] Fórmulas (~50.000) - aguardando
- [ ] Rastreabilidade (~100.000) - aguardando
- [ ] Verificar contagens no Supabase
- [ ] Verificar relacionamentos (FKs)
- [ ] Verificar status dos pedidos
- [ ] Confirmar 0 erros de Unicode
- [ ] ✅ MIGRAÇÃO COMPLETA!

---

## 🎉 APÓS MIGRAÇÃO COMPLETA

1. Fazer backup do Supabase
2. Validar integridade dos dados
3. Testar aplicação com dados migrados
4. Celebrar! 🎊

---

**Última atualização**: 22/10/2025 20:35
**Criado por**: Claude Code
**Scripts**:
- exportar_clientes_rapido_batch.py
- exportar_pedidos_otimizado.py
- exportar_formulas_otimizado.py
- exportar_rastreabilidade_otimizado.py
