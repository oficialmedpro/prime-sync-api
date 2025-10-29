# 🚨🚨🚨 ALERTA CRÍTICO - LEIA ANTES DE MODIFICAR QUALQUER CÓDIGO 🚨🚨🚨

## ⛔ PARE E LEIA ISSO AGORA ⛔

Se você está prestes a modificar qualquer script de sincronização, migração ou consulta ao Firebird:

## **DADOS DE CLIENTES ESTÃO EM 3 TABELAS SEPARADAS!**

```
❌ ERRADO:
SELECT * FROM CLIENTE WHERE CODIGO = X
Resultado: telefone = NULL, endereço = NULL

✅ CORRETO:
1. SELECT * FROM CLIENTE WHERE CODIGO = X
2. SELECT * FROM CADASTRO_TELEFONE WHERE TIPO_CADASTRO = 1 AND CODIGO_CADASTRO = X
3. SELECT * FROM CADASTRO_ENDERECO WHERE TIPO_CADASTRO = 1 AND CODIGO_CADASTRO = X
Resultado: TODOS os dados completos!
```

## 📋 AS 3 TABELAS OBRIGATÓRIAS:

### 1️⃣ CLIENTE (Dados básicos)
```sql
SELECT 
    C.CODIGO,
    C.NOMECLIENTE,
    C.CPF_CNPJ,
    C.DIANASCIMENTO,
    C.MESNASCIMENTO,
    C.ANONASCIMENTO,
    C.SEXO,
    C.EMAIL1
FROM CLIENTE C
WHERE C.CODIGO = ?
```

### 2️⃣ CADASTRO_TELEFONE (Telefones)
```sql
SELECT 
    CT.TELEFONEPREFIXO,
    CT.TELEFONE,
    CT.OBSERVACAO
FROM CADASTRO_TELEFONE CT
WHERE CT.TIPO_CADASTRO = 1  -- 1 = Cliente
AND CT.CODIGO_CADASTRO = ?
```

### 3️⃣ CADASTRO_ENDERECO (Endereços)
```sql
SELECT 
    CE.DESCRICAO,
    CE.ENDERECO,
    CE.NUMERO,
    CE.CEP
FROM CADASTRO_ENDERECO CE
WHERE CE.TIPO_CADASTRO = 1  -- 1 = Cliente
AND CE.CODIGO_CADASTRO = ?
```

## 🔴 O QUE ACONTECE SE VOCÊ ESQUECER:

1. Clientes sincronizados SEM telefone
2. Clientes sincronizados SEM endereço
3. Impossível entregar pedidos
4. Impossível contatar clientes
5. CRM com dados incompletos
6. Retrabalho e perda de tempo

## ✅ ARQUIVO DE REFERÊNCIA:

Veja: `sync-api/verificar_cliente_firebird.py`

Este arquivo tem a estrutura CORRETA. Use como base para qualquer modificação!

## 📝 CHECKLIST ANTES DE COMMITAR:

- [ ] Busquei dados da tabela CLIENTE?
- [ ] Busquei dados da tabela CADASTRO_TELEFONE?
- [ ] Busquei dados da tabela CADASTRO_ENDERECO?
- [ ] Usei TIPO_CADASTRO = 1 nas tabelas relacionadas?
- [ ] Testei com um cliente real (ex: código 37479)?

---

**Data do alerta:** 28/10/2025  
**Motivo:** Sincronização incompleta causou perda de dados de telefone e endereço

🚨 **NÃO IGNORE ESTE AVISO!** 🚨


