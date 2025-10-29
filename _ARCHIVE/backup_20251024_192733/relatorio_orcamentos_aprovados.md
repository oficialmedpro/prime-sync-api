# 📊 Relatório de Orçamentos Aprovados vs Não Aprovados

## 🎯 **Descoberta Importante**

**Campo `AVIADA_DT` = Indicador de Aprovação**
- ✅ **AVIADA_DT preenchida** = Orçamento **APROVADO** (Aviado)
- ❌ **AVIADA_DT NULL** = Orçamento **NÃO APROVADO**

---

## 📈 **Estatísticas Gerais**

| Categoria | Quantidade | Percentual | Valor Total |
|-----------|------------|------------|-------------|
| **Total de Orçamentos** | 16.448 | 100% | R$ 5.126.224,47 |
| **APROVADOS (Aviados)** | 8.704 | 52.9% | R$ 2.387.881,80 |
| **NÃO APROVADOS** | 7.744 | 47.1% | R$ 2.738.342,67 |
| **ENTREGUES** | 1.582 | 9.6% | R$ 448.542,99 |

---

## 🔍 **Análise Detalhada**

### **✅ Orçamentos APROVADOS (8.704 orçamentos)**
- **Percentual**: 52.9% do total
- **Valor Médio**: R$ 274,15
- **Valor Total**: R$ 2.387.881,80
- **Status**: AVIADA_DT preenchida

### **❌ Orçamentos NÃO APROVADOS (7.744 orçamentos)**
- **Percentual**: 47.1% do total
- **Valor Médio**: R$ 353,50
- **Valor Total**: R$ 2.738.342,67
- **Status**: AVIADA_DT NULL

### **📦 Orçamentos ENTREGUES (1.582 orçamentos)**
- **Percentual**: 9.6% do total
- **Valor Médio**: R$ 283,40
- **Valor Total**: R$ 448.542,99
- **Status**: ENTREGUE_DT preenchida

---

## 📋 **Exemplos de Orçamentos APROVADOS**

| Código | Cliente | Data Aprovação | Valor | Status |
|--------|---------|----------------|-------|--------|
| 251001890 | TATIANE VALERIA DA SILVA | 21/10/2025 18:34 | R$ 50,48 | -1 |
| 251002795 | KARINE GRECCO | 21/10/2025 18:02 | R$ 336,80 | -1 |
| 251002915 | SEBASTIAO APARECIDO | 21/10/2025 17:49 | R$ 172,17 | -1 |
| 251002898 | CRISTIANE PAULA DOS SANTOS | 21/10/2025 17:33 | R$ 563,34 | -1 |
| 251002876 | LUCIANA CORREIA PEREIRA | 21/10/2025 17:17 | R$ 50,00 | -1 |

---

## 📋 **Exemplos de Orçamentos NÃO APROVADOS**

| Código | Cliente | Data Aprovação | Valor | Status |
|--------|---------|----------------|-------|--------|
| 251002921 | DAIANE APARECIDA DE PAULA | NULL | R$ 174,79 | 0 |
| 251002920 | MARLY | NULL | R$ 219,88 | 0 |
| 251002919 | MARIO BERTTI | NULL | R$ 1.810,97 | 0 |
| 251002918 | GUILHERME AUGUSTO FARIAS CRUEL | NULL | R$ 431,78 | 0 |
| 251002917 | MARTA | NULL | R$ 166,66 | 0 |

---

## 🔄 **Consulta SQL para Exportação**

### **Orçamentos Aprovados por Cliente:**
```sql
SELECT 
    C.CODIGO as codigo_cliente,
    C.NOMECLIENTE as nome_cliente,
    C.CPF_CNPJ as cpf,
    A1.CODIGO as codigo_orcamento,
    A1.AVIADA_DT as data_aprovacao,
    A1.ENTREGUE_DT as data_entrega,
    A1.VALORVENDA as valor_total,
    A1.STATUS_MOV as status_mov,
    A1.OBSERVACAO as observacoes
FROM ATENDIMENTO_A1 A1
INNER JOIN CLIENTE C ON A1.CODIGO_CLIENTE = C.CODIGO
WHERE A1.AVIADA_DT IS NOT NULL  -- APROVADOS
ORDER BY C.NOMECLIENTE, A1.AVIADA_DT DESC;
```

### **Orçamentos Não Aprovados por Cliente:**
```sql
SELECT 
    C.CODIGO as codigo_cliente,
    C.NOMECLIENTE as nome_cliente,
    C.CPF_CNPJ as cpf,
    A1.CODIGO as codigo_orcamento,
    A1.AVIADA_DT as data_aprovacao,
    A1.ENTREGUE_DT as data_entrega,
    A1.VALORVENDA as valor_total,
    A1.STATUS_MOV as status_mov,
    A1.OBSERVACAO as observacoes
FROM ATENDIMENTO_A1 A1
INNER JOIN CLIENTE C ON A1.CODIGO_CLIENTE = C.CODIGO
WHERE A1.AVIADA_DT IS NULL  -- NÃO APROVADOS
ORDER BY C.NOMECLIENTE, A1.CODIGO DESC;
```

---

## 📊 **Distribuição por Status**

### **Status -1 (Aprovados):**
- **Quantidade**: 8.704 orçamentos
- **Característica**: AVIADA_DT preenchida
- **Significado**: Orçamento aprovado e aviado

### **Status 0 (Não Aprovados):**
- **Quantidade**: 7.744 orçamentos
- **Característica**: AVIADA_DT NULL
- **Significado**: Orçamento não aprovado

---

## 🎯 **Conclusões**

### **Taxa de Aprovação:**
- **52.9%** dos orçamentos são aprovados
- **47.1%** dos orçamentos não são aprovados

### **Valor dos Orçamentos:**
- **Orçamentos não aprovados** têm valor médio maior (R$ 353,50)
- **Orçamentos aprovados** têm valor médio menor (R$ 274,15)

### **Entrega:**
- Apenas **9.6%** dos orçamentos são entregues
- **18.2%** dos orçamentos aprovados são entregues (1.582 de 8.704)

---

## 🔧 **Recomendações para Exportação**

### **1. Incluir Status de Aprovação:**
```sql
CASE 
    WHEN A1.AVIADA_DT IS NOT NULL THEN 'APROVADO'
    ELSE 'NAO_APROVADO'
END as status_aprovacao
```

### **2. Incluir Data de Aprovação:**
```sql
A1.AVIADA_DT as data_aprovacao
```

### **3. Incluir Status de Entrega:**
```sql
CASE 
    WHEN A1.ENTREGUE_DT IS NOT NULL THEN 'ENTREGUE'
    ELSE 'NAO_ENTREGUE'
END as status_entrega
```

---

**Relatório gerado em**: 21/10/2025 18:45  
**Fonte**: Banco Prime - db.primesoftware.com.br  
**Total de registros analisados**: 16.448 orçamentos
