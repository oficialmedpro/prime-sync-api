# DOCUMENTAÇÃO - Como Prosseguir com a Migração

## STATUS ATUAL (22/10/2025 - 20:30)

### ✅ CONCLUÍDO

1. **Script de Clientes (`exportar_clientes_rapido_batch.py`)**
   - Status: RODANDO EM SEGUNDO PLANO
   - Progresso: 18.000/37.137 clientes (48.5%)
   - Tempo restante estimado: ~35 minutos
   - Velocidade: 9.1 clientes/segundo
   - Erros: 0 (zero)
   - Previsão de término: 20:58

2. **Script de Pedidos (`exportar_pedidos_otimizado.py`)**
   - Status: PRONTO PARA EXECUTAR
   - TESTADO com sucesso (inseriu pedidos corretamente)
   - BATCH_SIZE configurado para 500 pedidos por lote
   - Total a migrar: 16.604 pedidos

### 🔧 CORREÇÕES IMPLEMENTADAS

#### No script de Clientes:
- Adicionado limpeza de caracteres Unicode inválidos (\x00, \u0000)
- Configurado headers corretos para schema API do Supabase
- Implementado inserção em lotes de 500

#### No script de Pedidos:
- Adicionado função `buscar_cliente_id()` para resolver foreign key
- Adicionado campos `status_aprovacao` e `status_entrega` (NOT NULL)
- Lógica de status:
  - `status_aprovacao`: 'APROVADO' se AVIADA_DT existe, senão 'NAO_APROVADO'
  - `status_entrega`: 'ENTREGUE' se ENTREGUE_DT existe, senão 'NAO_ENTREGUE'
  - `status_geral`: 'ENTREGUE' > 'APROVADO' > 'PENDENTE'

---

## 🚀 COMO PROSSEGUIR AMANHÃ

### PASSO 1: Verificar se o script de Clientes terminou

Execute no terminal:
```bash
py "C:\Banco de Dados Prime\exportar_clientes_rapido_batch.py"
```

Se já terminou, você verá a mensagem final com estatísticas.

### PASSO 2: Executar o script de Pedidos

**IMPORTANTE**: Só execute DEPOIS que o script de clientes terminar!

```bash
py "C:\Banco de Dados Prime\exportar_pedidos_otimizado.py"
```

**Tempo estimado**: ~30-40 minutos para 16.604 pedidos em lotes de 500

---

## 📂 ARQUIVOS IMPORTANTES

### Scripts Principais (USE ESTES):

1. **`exportar_clientes_rapido_batch.py`**
   - Exporta TODOS os clientes com telefone, endereço, email, data nascimento
   - Lotes de 500 clientes
   - Schema: api.prime_clientes

2. **`exportar_pedidos_otimizado.py`**
   - Exporta TODOS os pedidos
   - Lotes de 500 pedidos
   - Schema: api.prime_pedidos
   - Resolve cliente_id automaticamente

### Scripts Auxiliares (NÃO USE):

- `exportar_clientes_corrigido_schema.py` - Versão antiga (1 por vez)
- `exportar_pedidos.py` - Versão antiga (usa biblioteca supabase-py)
- `contar_clientes_disponiveis.py` - Apenas para análise

---

## ⚙️ CONFIGURAÇÕES

### Firebird (PRIME Software)
```python
FIREBIRD_CONFIG = {
    'host': 'db.primesoftware.com.br',
    'database': 'oficialmed1250',
    'user': 'OFICIALMED',
    'password': 'Lt-@=waIh))Ql3~',
    'charset': 'UTF8'
}
```

### Supabase
```python
SUPABASE_URL = "https://agdffspstbxeqhqtltvb.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFnZGZmc3BzdGJ4ZXFocXRsdHZiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MDQ1MzY2NiwiZXhwIjoyMDY2MDI5NjY2fQ.grInwGHFAH2WYvYerwfHkUsM08wXCJASg4CPMD2cTaA"

# Headers corretos para schema API
headers = {
    'apikey': SUPABASE_SERVICE_KEY,
    'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'resolution=merge-duplicates',
    'Accept-Profile': 'api',   # IMPORTANTE!
    'Content-Profile': 'api'    # IMPORTANTE!
}
```

---

## 🐛 PROBLEMAS COMUNS E SOLUÇÕES

### Erro: "The schema must be one of the following: api"
**Solução**: Verificar se os headers `Accept-Profile` e `Content-Profile` estão configurados como 'api'

### Erro: "unsupported Unicode escape sequence"
**Solução**: Função `limpar_string()` já implementada nos scripts atuais

### Erro: "null value in column violates not-null constraint"
**Solução**:
- Para `cliente_id`: função `buscar_cliente_id()` já resolve
- Para `status_aprovacao/status_entrega`: já implementado no script

### Script muito lento (1 por vez)
**Solução**: Usar BATCH_SIZE = 500 (já configurado nos scripts atuais)

---

## 📊 DADOS DA MIGRAÇÃO

### Clientes (prime_clientes)
- **Total**: 37.137 clientes ativos
- **Com telefone**: ~33.000 (89%)
- **Com endereço**: ~7.900 (21%)
- **Campos**: codigo_cliente_original, nome, cpf_cnpj, data_nascimento, sexo, email, telefone, endereço completo, ativo

### Pedidos (prime_pedidos)
- **Total**: 16.604 pedidos
- **Origem**: ATENDIMENTO_A1
- **Campos**: codigo_orcamento_original, cliente_id (FK), codigo_cliente_original, data_aprovacao, data_entrega, valor_total, observacoes, status_aprovacao, status_entrega, status_geral

---

## 🔍 COMO VERIFICAR SE DEU CERTO

### No Supabase (via SQL):

```sql
-- Contar clientes
SELECT COUNT(*) FROM api.prime_clientes;
-- Deve retornar: 37.137

-- Contar pedidos
SELECT COUNT(*) FROM api.prime_pedidos;
-- Deve retornar: 16.604

-- Verificar pedidos com status
SELECT
    status_geral,
    COUNT(*) as total
FROM api.prime_pedidos
GROUP BY status_geral;
-- Deve mostrar: PENDENTE, APROVADO, ENTREGUE

-- Verificar se todos os pedidos têm cliente
SELECT COUNT(*)
FROM api.prime_pedidos
WHERE cliente_id IS NULL;
-- Deve retornar: 0
```

---

## ⏱️ ESTIMATIVAS DE TEMPO

- **Clientes** (37.137): ~60-70 minutos
- **Pedidos** (16.604): ~30-40 minutos
- **Total**: ~1h30min - 2h

---

## 📝 PRÓXIMOS PASSOS (APÓS MIGRAÇÃO)

1. Validar dados no Supabase
2. Verificar integridade das foreign keys (cliente_id)
3. Confirmar que todos os status estão corretos
4. Verificar se não há caracteres inválidos nos textos

---

## 🆘 SE ALGO DER ERRADO

### Se o script parar no meio:
Os scripts usam `on_conflict` para fazer UPSERT, então você pode executar novamente sem problemas. Ele vai:
- Pular registros já inseridos
- Atualizar registros existentes
- Inserir apenas os que faltam

### Se precisar recomeçar do zero:
```sql
-- Limpar tabelas (CUIDADO!)
DELETE FROM api.prime_pedidos;
DELETE FROM api.prime_clientes;
```

---

## 📞 COMANDO PARA CONTINUAR NO CLAUDE CODE

Se precisar continuar amanhã, pode dizer:

> "Continue a migração dos pedidos. O script de clientes já terminou."

Ou para verificar status:

> "Verifique o status da migração de clientes e me diga se posso começar a migração de pedidos."

---

**Última atualização**: 22/10/2025 20:30
**Criado por**: Claude Code
**Scripts**: exportar_clientes_rapido_batch.py, exportar_pedidos_otimizado.py
