# 🚨 ESTRUTURA DO BANCO FIREBIRD - LEIA ANTES DE FAZER QUALQUER ALTERAÇÃO 🚨

## ⚠️ AVISO CRÍTICO ⚠️

**Este documento é FUNDAMENTAL para qualquer desenvolvedor que trabalhe com o banco Firebird do sistema Prime.**

**SE VOCÊ NÃO LER ISSO, VAI SINCRONIZAR DADOS INCOMPLETOS E QUEBRAR O SISTEMA!**

---

## 📋 ESTRUTURA DE DADOS - CLIENTES

### ❌ ERRO COMUM (NÃO FAZER ISSO):

```sql
-- ERRADO! Isso NÃO traz telefone e endereço!
SELECT * FROM CLIENTE WHERE CODIGO = 37479;
-- Resultado: telefone = NULL, endereço = NULL ❌
```

### ✅ FORMA CORRETA (SEMPRE FAZER ASSIM):

```sql
-- 1. DADOS BÁSICOS DO CLIENTE
SELECT 
    C.CODIGO,
    C.NOMECLIENTE,
    C.CPF_CNPJ,
    C.DIANASCIMENTO,
    C.MESNASCIMENTO,
    C.ANONASCIMENTO,
    C.SEXO,
    C.EMAIL1,
    C.ATIVO
FROM CLIENTE C
WHERE C.CODIGO = 37479;

-- 2. TELEFONES DO CLIENTE (tabela separada!)
SELECT 
    CT.TELEFONEPREFIXO,
    CT.TELEFONE,
    CT.OBSERVACAO
FROM CADASTRO_TELEFONE CT
WHERE CT.TIPO_CADASTRO = 1  -- 1 = Cliente
AND CT.CODIGO_CADASTRO = 37479;

-- 3. ENDEREÇOS DO CLIENTE (tabela separada!)
SELECT 
    CE.DESCRICAO,
    CE.ENDERECO,
    CE.NUMERO,
    CE.CEP
FROM CADASTRO_ENDERECO CE
WHERE CE.TIPO_CADASTRO = 1  -- 1 = Cliente
AND CE.CODIGO_CADASTRO = 37479;

-- 4. PEDIDOS DO CLIENTE
SELECT 
    A.CODIGO,
    A.CADASTRO_DT,
    A.AVIADA_DT,
    A.ENTREGUE_DT,
    A.VALORVENDA
FROM ATENDIMENTO_A1 A
WHERE A.CODIGO_CLIENTE = 37479;
```

---

## 🏗️ ARQUITETURA DO BANCO

### CLIENTE (Tabela Principal)
- **Tabela:** `CLIENTE`
- **Campos principais:**
  - `CODIGO` - ID único do cliente
  - `NOMECLIENTE` - Nome completo
  - `CPF_CNPJ` - CPF ou CNPJ
  - `DIANASCIMENTO`, `MESNASCIMENTO`, `ANONASCIMENTO` - Data nascimento em 3 campos separados
  - `SEXO` - Código do sexo
  - `EMAIL1` - E-mail (frequentemente NULL)
  - `ATIVO` - -1 = Ativo, 0 = Inativo

### TELEFONES (Tabela Relacionada)
- **Tabela:** `CADASTRO_TELEFONE`
- **Relacionamento:** `TIPO_CADASTRO = 1 AND CODIGO_CADASTRO = [ID_CLIENTE]`
- **Campos:**
  - `TELEFONEPREFIXO` - DDD
  - `TELEFONE` - Número do telefone
  - `OBSERVACAO` - Tipo (RES, CEL, COM, etc)
- **Importante:** Um cliente pode ter MÚLTIPLOS telefones!

### ENDEREÇOS (Tabela Relacionada)
- **Tabela:** `CADASTRO_ENDERECO`
- **Relacionamento:** `TIPO_CADASTRO = 1 AND CODIGO_CADASTRO = [ID_CLIENTE]`
- **Campos:**
  - `DESCRICAO` - Tipo do endereço (CASA, TRABALHO, etc)
  - `ENDERECO` - Logradouro completo
  - `NUMERO` - Número
  - `CEP` - CEP
- **Importante:** Um cliente pode ter MÚLTIPLOS endereços!

### PEDIDOS/ORÇAMENTOS
- **Tabela:** `ATENDIMENTO_A1`
- **Relacionamento:** `CODIGO_CLIENTE = [ID_CLIENTE]`
- **Campos importantes:**
  - `CODIGO` - ID do orçamento/pedido
  - `CADASTRO_DT` - Data de criação
  - `AVIADA_DT` - Data de aprovação (NULL = não aprovado)
  - `ENTREGUE_DT` - Data de entrega (NULL = não entregue)
  - `VALORVENDA` - Valor total do pedido

---

## 🔑 CAMPO TIPO_CADASTRO

O campo `TIPO_CADASTRO` indica o tipo de entidade:
- **1** = Cliente
- **2** = Fornecedor
- **3** = Funcionário
- etc.

**SEMPRE use `TIPO_CADASTRO = 1` quando buscar dados de CLIENTES!**

---

## ⚠️ PROBLEMAS QUE ACONTECEM SE ESQUECER ISSO:

1. ❌ **Clientes sincronizados SEM telefone** (mesmo tendo no Firebird)
2. ❌ **Clientes sincronizados SEM endereço** (mesmo tendo no Firebird)
3. ❌ **Impossível entregar pedidos** (não tem endereço)
4. ❌ **Impossível contatar cliente** (não tem telefone)
5. ❌ **Dados incompletos nas análises de CRM**

---

## 📚 EXEMPLO REAL - CLIENTE NELSON MORENO

### ❌ Buscando ERRADO (só tabela CLIENTE):
```
Nome: NELSON MORENO
Telefone: NULL ❌
Endereço: NULL ❌
```

### ✅ Buscando CORRETO (3 tabelas):
```
Nome: NELSON MORENO
Telefone: (43) 999729678 ✅ (da tabela CADASTRO_TELEFONE)
Endereço: RUA 15 DE NOVEMBRO, 696 - CEP: 88801330 ✅ (da tabela CADASTRO_ENDERECO)
```

---

## 🔧 QUANDO CRIAR/ATUALIZAR SCRIPTS DE SINCRONIZAÇÃO:

### ✅ CHECKLIST OBRIGATÓRIO:

- [ ] Estou buscando da tabela `CLIENTE`?
- [ ] Estou buscando da tabela `CADASTRO_TELEFONE` com `TIPO_CADASTRO = 1`?
- [ ] Estou buscando da tabela `CADASTRO_ENDERECO` com `TIPO_CADASTRO = 1`?
- [ ] Estou tratando múltiplos telefones?
- [ ] Estou tratando múltiplos endereços?
- [ ] Estou montando a data de nascimento corretamente (DIA/MES/ANO)?

---

## 📁 ARQUIVOS QUE DEVEM SEGUIR ESTA ESTRUTURA:

- `sync-api/app.py` - Sincronização principal
- `sync-api/sincronizar_*.py` - Todos os scripts de sincronização
- Qualquer script que faça `SELECT` em `CLIENTE`
- Qualquer script que exporte dados para Supabase
- Qualquer script de migração de dados

---

## 🆘 SE TIVER DÚVIDA:

1. Veja o arquivo: `sync-api/verificar_cliente_firebird.py`
2. Ele tem a estrutura CORRETA de como buscar todos os dados
3. Use como referência SEMPRE!

---

**ÚLTIMA ATUALIZAÇÃO:** 28/10/2025  
**MOTIVO:** Cliente Nelson Moreno (37479) foi sincronizado SEM telefone e endereço, causando impossibilidade de entrega do pedido 251003542.

---

# 🚨 NUNCA ESQUEÇA: 3 TABELAS = DADOS COMPLETOS! 🚨


