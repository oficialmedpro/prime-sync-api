# 📘 DOCUMENTAÇÃO FIREBIRD - ESTRUTURA COMPLETA

**Data:** 28/10/2025  
**Sistema:** Prime Software → Supabase  
**Desenvolvedor:** [Seu Nome]

---

## ⚠️ **LEIA ANTES DE QUALQUER ALTERAÇÃO NO CÓDIGO** ⚠️

Esta documentação explica **EXATAMENTE** como buscar dados do Firebird e sincronizar com Supabase.

**❌ ERRO COMUM:** Buscar só da tabela principal (dados virão `NULL`!)  
**✅ CORRETO:** Buscar das **tabelas relacionadas** (estrutura normalizada)

---

# 📋 1. CLIENTES (`prime_clientes`)

## 🔍 Estrutura no Firebird

### 1.1. DADOS BÁSICOS DO CLIENTE
**Tabela:** `CLIENTE`

| Campo Firebird | Tipo | Campo Supabase | Observação |
|---|---|---|---|
| `CODIGO` | INT | `codigo_cliente_original` | PK, sequencial |
| `NOMECLIENTE` | VARCHAR | `nome` | Nome completo |
| `CPF_CNPJ` | VARCHAR | `cpf_cnpj` | CPF ou CNPJ |
| `EMAIL1` | VARCHAR | `email` | E-mail principal |
| `SEXO` | CHAR(1) | `sexo` | **0 = Não informado, 1 = Masculino, 2 = Feminino** |
| `ATIVO` | SMALLINT | `ativo` | -1=Ativo, 0=Inativo |
| `DIANASCIMENTO` | INT | ↓ | Combinar para `data_nascimento` |
| `MESNASCIMENTO` | INT | ↓ | Combinar para `data_nascimento` |
| `ANONASCIMENTO` | INT | `data_nascimento` | Formato: YYYY-MM-DD |
| `CODIGO_CIDADEESTADO` | INT | → JOIN | FK para CIDADEESTADO |

**⚠️ IMPORTANTE:**
- Data de nascimento vem em **3 campos separados** (DIA, MES, ANO)
- Precisa **COMBINAR** antes de inserir no Supabase

```python
# Exemplo de combinação:
data_nasc = f"{ANONASCIMENTO}-{MESNASCIMENTO:02d}-{DIANASCIMENTO:02d}"
```

---

### 1.2. TELEFONES DO CLIENTE ⚠️ **TABELA SEPARADA**
**Tabela:** `CADASTRO_TELEFONE`

| Campo Firebird | Tipo | Campo Supabase | Observação |
|---|---|---|---|
| `TIPO_CADASTRO` | INT | - | **FILTRO: = 1 (cliente)** |
| `CODIGO_CADASTRO` | INT | - | FK = `CLIENTE.CODIGO` |
| `TELEFONEPREFIXO` | VARCHAR | ↓ | DDD |
| `TELEFONE` | VARCHAR | `telefone` | PREFIXO + TELEFONE |
| `OBSERVACAO` | VARCHAR | - | Descrição (ex: "Celular") |

**⚠️ RELACIONAMENTO:**
```sql
WHERE TIPO_CADASTRO = 1
AND CODIGO_CADASTRO = [CODIGO_CLIENTE]
```

**⚠️ ATENÇÃO:**
- `TIPO_CADASTRO = 1` significa **CLIENTE**
- `TIPO_CADASTRO = 2` significa FORNECEDOR (não pegar!)
- Telefone vem em **2 campos**: `TELEFONEPREFIXO` + `TELEFONE`
- Pode haver **múltiplos telefones** → pegar o primeiro

```python
# Exemplo correto:
cursor.execute("""
    SELECT CT.TELEFONEPREFIXO, CT.TELEFONE
    FROM CADASTRO_TELEFONE CT
    WHERE CT.TIPO_CADASTRO = 1
    AND CT.CODIGO_CADASTRO = ?
""", (codigo_cliente,))
```

---

### 1.3. ENDEREÇOS DO CLIENTE ⚠️ **TABELA SEPARADA**
**Tabela:** `CADASTRO_ENDERECO`

| Campo Firebird | Tipo | Campo Supabase | Observação |
|---|---|---|---|
| `TIPO_CADASTRO` | INT | - | **FILTRO: = 1 (cliente)** |
| `CODIGO_CADASTRO` | INT | - | FK = `CLIENTE.CODIGO` |
| `DESCRICAO` | VARCHAR | - | Ex: "Casa", "Trabalho" |
| `ENDERECO` | VARCHAR | `endereco_logradouro` | Rua, Avenida, etc |
| `NUMERO` | VARCHAR | `endereco_numero` | Número |
| `CEP` | VARCHAR | `endereco_cep` | CEP |

**⚠️ RELACIONAMENTO:**
```sql
WHERE TIPO_CADASTRO = 1
AND CODIGO_CADASTRO = [CODIGO_CLIENTE]
```

```python
# Exemplo correto:
cursor.execute("""
    SELECT CE.ENDERECO, CE.NUMERO, CE.CEP
    FROM CADASTRO_ENDERECO CE
    WHERE CE.TIPO_CADASTRO = 1
    AND CE.CODIGO_CADASTRO = ?
""", (codigo_cliente,))
```

---

### 1.4. CIDADE/ESTADO
**Tabela:** `CIDADEESTADO` (JOIN)

| Campo Firebird | Tipo | Campo Supabase | Observação |
|---|---|---|---|
| `CODIGO` | INT | - | PK |
| `NOMECIDADE` | VARCHAR | `endereco_cidade` | Nome da cidade |
| `UF` | CHAR(2) | `endereco_estado` | Sigla do estado |

**⚠️ JOIN:**
```sql
LEFT JOIN CIDADEESTADO CE ON C.CODIGO_CIDADEESTADO = CE.CODIGO
```

---

### 1.5. TOTALIZADORES DE PEDIDOS ⚠️ **CALCULADOS**
**Tabela:** `ATENDIMENTO_A1` (agregação)

Estes campos **NÃO existem** no Firebird → precisam ser **calculados**:

| Campo Supabase | Cálculo | Observação |
|---|---|---|
| `total_orcamentos` | `COUNT(*)` | Total de pedidos |
| `total_orcamentos_aprovados` | `COUNT(AVIADA_DT)` | Pedidos aprovados |
| `total_orcamentos_entregues` | `COUNT(ENTREGUE_DT)` | Pedidos entregues |
| `valor_total_orcamentos` | `SUM(VALORVENDA)` | Soma de todos |
| `valor_total_aprovados` | `SUM(VALORVENDA WHERE AVIADA_DT)` | Soma dos aprovados |
| `valor_total_entregues` | `SUM(VALORVENDA WHERE ENTREGUE_DT)` | Soma dos entregues |
| `valor_medio_orcamento` | `valor_total / total` | Média geral |
| `valor_medio_aprovado` | `valor_aprovado / total_aprov` | Média aprovados |
| `valor_medio_entregue` | `valor_entregue / total_entreg` | Média entregues |
| `primeira_compra` | `MIN(CADASTRO_DT)` | Data do primeiro pedido |
| `ultima_compra` | `MAX(CADASTRO_DT)` | Data do último pedido |

```python
# Exemplo de cálculo:
cursor.execute("""
    SELECT 
        A.CODIGO_CLIENTE,
        COUNT(*) as total,
        COUNT(A.AVIADA_DT) as aprovados,
        COUNT(A.ENTREGUE_DT) as entregues,
        COALESCE(SUM(A.VALORVENDA), 0) as valor_total,
        MIN(A.CADASTRO_DT) as primeira_compra,
        MAX(A.CADASTRO_DT) as ultima_compra
    FROM ATENDIMENTO_A1 A
    WHERE A.CODIGO_CLIENTE = ?
    GROUP BY A.CODIGO_CLIENTE
""", (codigo_cliente,))
```

---

## 📝 Código Correto para Sincronizar Clientes

```python
def sync_clientes_novos():
    """
    ⚠️ IMPORTANTE: Busca dados de 4 FONTES:
    1. CLIENTE (dados básicos)
    2. CADASTRO_TELEFONE (WHERE TIPO_CADASTRO = 1)
    3. CADASTRO_ENDERECO (WHERE TIPO_CADASTRO = 1)
    4. ATENDIMENTO_A1 (totalizadores calculados)
    """
    
    # 1. Buscar clientes básicos
    cursor.execute("""
        SELECT 
            C.CODIGO,
            C.NOMECLIENTE,
            C.CPF_CNPJ,
            C.DIANASCIMENTO,
            C.MESNASCIMENTO,
            C.ANONASCIMENTO,
            C.SEXO,
            C.EMAIL1,
            CE.NOMECIDADE,
            CE.UF,
            C.ATIVO
        FROM CLIENTE C
        LEFT JOIN CIDADEESTADO CE ON C.CODIGO_CIDADEESTADO = CE.CODIGO
        WHERE C.ATIVO = -1
        AND C.CODIGO > ?
        ORDER BY C.CODIGO
    """)
    
    # 2. Buscar telefones (tabela separada!)
    cursor.execute("""
        SELECT 
            CT.CODIGO_CADASTRO,
            CT.TELEFONEPREFIXO,
            CT.TELEFONE
        FROM CADASTRO_TELEFONE CT
        WHERE CT.TIPO_CADASTRO = 1
        AND CT.CODIGO_CADASTRO IN (...)
    """)
    
    # 3. Buscar endereços (tabela separada!)
    cursor.execute("""
        SELECT 
            CE.CODIGO_CADASTRO,
            CE.ENDERECO,
            CE.NUMERO,
            CE.CEP
        FROM CADASTRO_ENDERECO CE
        WHERE CE.TIPO_CADASTRO = 1
        AND CE.CODIGO_CADASTRO IN (...)
    """)
    
    # 4. Buscar totalizadores (calculados!)
    cursor.execute("""
        SELECT 
            A.CODIGO_CLIENTE,
            COUNT(*) as total_orcamentos,
            SUM(A.VALORVENDA) as valor_total,
            MIN(A.CADASTRO_DT) as primeira_compra,
            MAX(A.CADASTRO_DT) as ultima_compra
        FROM ATENDIMENTO_A1 A
        WHERE A.CODIGO_CLIENTE IN (...)
        GROUP BY A.CODIGO_CLIENTE
    """)
    
    # 5. COMBINAR os 4 antes de inserir no Supabase!
    cliente = {
        'codigo_cliente_original': codigo,
        'nome': nome,
        'telefone': telefones_dict.get(codigo),  # Da tabela CADASTRO_TELEFONE
        'endereco_logradouro': enderecos_dict.get(codigo),  # Da tabela CADASTRO_ENDERECO
        'total_orcamentos': totalizadores_dict.get(codigo, 0),  # Calculado
        # ... outros campos
    }
```

---

# 📋 2. PEDIDOS/ORÇAMENTOS (`prime_pedidos`)

## 🔍 Estrutura no Firebird

### 2.1. DADOS DO PEDIDO
**Tabela:** `ATENDIMENTO_A1`

| Campo Firebird | Tipo | Campo Supabase | Observação |
|---|---|---|---|
| `CODIGO` | INT | `codigo_orcamento_original` | PK, sequencial |
| `CODIGO_CLIENTE` | INT | `codigo_cliente_original` + `cliente_id` | FK cliente |
| `CADASTRO_DT` | TIMESTAMP | `data_criacao` | ⚠️ Data de criação |
| `AVIADA_DT` | TIMESTAMP | `data_aprovacao` | Data de aprovação |
| `ENTREGUE_DT` | TIMESTAMP | `data_entrega` | Data de entrega |
| `CANCELADO_DT` | TIMESTAMP | `data_cancelamento` | ⚠️ **VERIFICAR SE EXISTE** |
| `VALORVENDA` | DECIMAL | `valor_total` | Valor total do pedido |
| `OBSERVACAO` | VARCHAR | `observacoes` | Observações |

**⚠️ DATAS IMPORTANTES:**

| Data | Campo Firebird | Status |
|---|---|---|
| **Data de Criação** | `CADASTRO_DT` | ✅ Existe (descoberto 27/10) |
| **Data de Aprovação** | `AVIADA_DT` | ✅ Existe |
| **Data de Entrega** | `ENTREGUE_DT` | ✅ Existe |
| **Data de Cancelamento** | `CANCELADO_DT`? | ⚠️ **VERIFICAR** |

**⚠️ STATUS CALCULADOS:**

```python
# Status de aprovação
if aviada_dt:
    status_aprovacao = 'APROVADO'
else:
    status_aprovacao = 'NAO_APROVADO'

# Status de entrega
if entregue_dt:
    status_entrega = 'ENTREGUE'
else:
    status_entrega = 'NAO_ENTREGUE'

# Status geral (hierárquico)
if entregue_dt:
    status_geral = 'ENTREGUE'
elif aviada_dt:
    status_geral = 'APROVADO'
else:
    status_geral = 'PENDENTE'
```

---

## 📝 Código Correto para Sincronizar Pedidos

```python
def sync_pedidos_novos():
    """
    ⚠️ IMPORTANTE: Relacionar com prime_clientes (cliente_id)
    """
    
    # 1. Buscar pedidos do Firebird
    cursor.execute("""
        SELECT 
            A.CODIGO,
            A.CODIGO_CLIENTE,
            A.CADASTRO_DT,      -- Data de criação
            A.AVIADA_DT,        -- Data de aprovação
            A.ENTREGUE_DT,      -- Data de entrega
            A.VALORVENDA,
            A.OBSERVACAO
        FROM ATENDIMENTO_A1 A
        WHERE A.CODIGO_CLIENTE IS NOT NULL
        AND A.CODIGO > ?
        ORDER BY A.CODIGO
    """)
    
    # 2. Buscar cliente_id do Supabase (relacionamento)
    # NUNCA inserir sem cliente_id!
    url_clientes = f"{SUPABASE_URL}/rest/v1/prime_clientes"
    response = requests.get(url_clientes, params={
        'select': 'id,codigo_cliente_original',
        'codigo_cliente_original': f'in.({codigos_cliente})'
    })
    
    cache_clientes = {
        cli['codigo_cliente_original']: cli['id']
        for cli in response.json()
    }
    
    # 3. Montar pedido com cliente_id
    pedido = {
        'codigo_orcamento_original': codigo,
        'codigo_cliente_original': codigo_cliente,
        'cliente_id': cache_clientes.get(codigo_cliente),  # ⚠️ FK obrigatória!
        'data_criacao': cadastro_dt.isoformat() if cadastro_dt else None,
        'data_aprovacao': aviada_dt.isoformat() if aviada_dt else None,
        'data_entrega': entregue_dt.isoformat() if entregue_dt else None,
        'valor_total': float(valor_venda) if valor_venda else 0.0,
        'status_geral': status_geral  # Calculado
    }
```

---

# 📋 3. FÓRMULAS (`prime_formulas`)

## 🔍 Estrutura no Firebird

### 3.1. DADOS DA FÓRMULA
**Tabela:** `ATENDIMENTO_A2`

| Campo Firebird | Tipo | Campo Supabase | Observação |
|---|---|---|---|
| `CODIGO_ATEND_A1` | INT | `codigo_orcamento_original` + `pedido_id` | FK pedido |
| `NUMEROFORMULA` | INT | `numero_formula` | Número sequencial |
| `TEXTOROTULO` | TEXT | `descricao` | ⚠️ **NOME DO PRODUTO** |
| `POSOLOGIA` | VARCHAR | `posologia` | Instruções de uso |
| `VALORFORMULA_VENDA` | DECIMAL | `valor_formula` | Valor da fórmula |

**⚠️ CAMPO IMPORTANTE:**
- `TEXTOROTULO` contém o **nome completo do produto/fórmula**
- **NÃO** buscar de `ESTOQUE` (pode não ter relação)
- Este campo já tem tudo que precisa!

---

## 📝 Código Correto para Sincronizar Fórmulas

```python
def sync_formulas_novas():
    """
    ⚠️ IMPORTANTE: 
    - TEXTOROTULO já contém nome do produto
    - Relacionar com prime_pedidos (pedido_id)
    """
    
    # 1. Buscar fórmulas do Firebird
    cursor.execute("""
        SELECT
            A2.CODIGO_ATEND_A1,
            A2.NUMEROFORMULA,
            A2.TEXTOROTULO,        -- Nome do produto (completo!)
            A2.POSOLOGIA,
            A2.VALORFORMULA_VENDA
        FROM ATENDIMENTO_A2 A2
        WHERE A2.CODIGO_ATEND_A1 > ?
        ORDER BY A2.CODIGO_ATEND_A1, A2.NUMEROFORMULA
    """)
    
    # 2. Buscar pedido_id do Supabase (relacionamento)
    url_pedidos = f"{SUPABASE_URL}/rest/v1/prime_pedidos"
    response = requests.get(url_pedidos, params={
        'select': 'id,codigo_orcamento_original',
        'codigo_orcamento_original': f'in.({codigos_orcamento})'
    })
    
    cache_pedidos = {
        ped['codigo_orcamento_original']: ped['id']
        for ped in response.json()
    }
    
    # 3. Montar fórmula com pedido_id
    formula = {
        'pedido_id': cache_pedidos.get(codigo_atend),  # ⚠️ FK obrigatória!
        'codigo_orcamento_original': codigo_atend,
        'numero_formula': num_formula,
        'descricao': textorotulo,  # ⚠️ Nome do produto está aqui!
        'posologia': posologia,
        'valor_formula': float(valor)
    }
```

---

# 📋 4. ITENS DAS FÓRMULAS (`prime_formulas_itens`)

## 🔍 Estrutura no Firebird

### 4.1. DADOS DO ITEM
**Tabela:** `ATENDIMENTO_A3`

| Campo Firebird | Tipo | Campo Supabase | Observação |
|---|---|---|---|
| `CODIGO_ATEND_A1` | INT | `codigo_orcamento_original` | FK pedido |
| `NUMEROFORMULA` | INT | `numero_formula` | FK fórmula |
| `CODIGO_ESTOQUE` | INT | `codigo_produto_original` | FK produto |
| `DESCRICAO` | VARCHAR | - | Descrição do item |
| `QUANTIDADE` | DECIMAL | `quantidade` | Quantidade usada |
| `VALOR_CUSTO` | DECIMAL | `valor_custo` | Custo unitário |
| `VALOR_VENDA` | DECIMAL | `valor_venda` | Preço unitário |

**⚠️ RELACIONAMENTO COM ESTOQUE:**
- `CODIGO_ESTOQUE` → buscar nome do produto em `ESTOQUE.NOME`
- Cada item é um **ingrediente** da fórmula

---

### 4.2. NOME DO PRODUTO ⚠️ **TABELA SEPARADA**
**Tabela:** `ESTOQUE` (JOIN)

| Campo Firebird | Tipo | Campo Supabase | Observação |
|---|---|---|---|
| `CODIGO` | INT | - | PK |
| `NOME` | VARCHAR | `nome_produto` | Nome do ingrediente |

**⚠️ JOIN:**
```sql
LEFT JOIN ESTOQUE E ON A3.CODIGO_ESTOQUE = E.CODIGO
```

---

## 📝 Código Correto para Sincronizar Itens

```python
def sync_formulas_itens_novos():
    """
    ⚠️ IMPORTANTE: 
    - Buscar nome do produto da tabela ESTOQUE (JOIN)
    - Relacionar com prime_formulas (formula_id)
    """
    
    # 1. Buscar itens do Firebird COM JOIN no ESTOQUE
    cursor.execute("""
        SELECT 
            A3.CODIGO_ATEND_A1,
            A3.NUMEROFORMULA,
            A3.CODIGO_ESTOQUE,
            E.NOME,               -- Nome do produto (JOIN!)
            A3.QUANTIDADE,
            A3.VALOR_CUSTO,
            A3.VALOR_VENDA
        FROM ATENDIMENTO_A3 A3
        LEFT JOIN ESTOQUE E ON A3.CODIGO_ESTOQUE = E.CODIGO
        WHERE A3.CODIGO_ATEND_A1 > ?
        ORDER BY A3.CODIGO_ATEND_A1, A3.NUMEROFORMULA
    """)
    
    # 2. Buscar formula_id do Supabase (relacionamento)
    url_formulas = f"{SUPABASE_URL}/rest/v1/prime_formulas"
    response = requests.get(url_formulas, params={
        'select': 'id,codigo_orcamento_original,numero_formula'
    })
    
    cache_formulas = {}
    for form in response.json():
        chave = (form['codigo_orcamento_original'], form['numero_formula'])
        cache_formulas[chave] = form['id']
    
    # 3. Montar item com formula_id
    item = {
        'formula_id': cache_formulas.get((codigo_atend, num_formula)),
        'codigo_orcamento_original': codigo_atend,
        'numero_formula': num_formula,
        'codigo_produto_original': codigo_estoque,
        'nome_produto': nome_produto,  # ⚠️ Do JOIN com ESTOQUE!
        'quantidade': float(quantidade),
        'valor_custo': float(valor_custo),
        'valor_venda': float(valor_venda)
    }
```

---

# ⚠️ ORDEM DE SINCRONIZAÇÃO (IMPORTANTÍSSIMO!)

**NUNCA SINCRONIZAR FORA DE ORDEM!** As tabelas têm relacionamento em cascata:

```
1. CLIENTES (prime_clientes)
   ↓ (gera cliente_id)
   
2. PEDIDOS (prime_pedidos)  
   ↓ (gera pedido_id)
   
3. FÓRMULAS (prime_formulas)
   ↓ (gera formula_id)
   
4. ITENS (prime_formulas_itens)
```

**❌ SE SINCRONIZAR FORA DE ORDEM:**
- Pedidos sem `cliente_id` → **ERRO FK**
- Fórmulas sem `pedido_id` → **ERRO FK**
- Itens sem `formula_id` → **ERRO FK**

**✅ ORDEM CORRETA:**

```python
# 1º Clientes (independente)
sync_clientes_novos()

# 2º Pedidos (depende de clientes)
sync_pedidos_novos()

# 3º Fórmulas (depende de pedidos)
sync_formulas_novas()

# 4º Itens (depende de fórmulas)
sync_formulas_itens_novos()
```

---

# 🔄 UPSERT vs INSERT

## Quando usar INSERT (novos registros):
```python
# Somente registros novos (CODIGO > ultimo_codigo)
cursor.execute(f"""
    SELECT * FROM CLIENTE
    WHERE CODIGO > {ultimo_codigo}
    ORDER BY CODIGO
""")

# Inserir no Supabase
response = requests.post(url, json=dados)
```

## Quando usar UPSERT (atualizar existentes):
```python
# Todos os registros (ou lista específica)
cursor.execute(f"""
    SELECT * FROM CLIENTE
    WHERE CODIGO IN ({codigos})
""")

# Upsert no Supabase (merge-duplicates)
response = requests.post(url, 
    headers={**headers, 'Prefer': 'resolution=merge-duplicates'},
    json=dados
)
```

**⚠️ IMPORTANTE:**
- **INSERT**: Mais rápido, mas falha se registro já existe
- **UPSERT**: Mais lento, mas atualiza registros existentes
- Use **INSERT** para sincronização incremental diária
- Use **UPSERT** para correções e atualizações retroativas

---

# 📊 RESUMO VISUAL

```
FIREBIRD                           SUPABASE
========================================================================================================

┌─────────────────────────────────────────────────────────────────────────────────┐
│ CLIENTES (4 fontes!)                                                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  CLIENTE (básico)                    ─┐                                         │
│  CADASTRO_TELEFONE (TIPO=1)          ─┼─→  prime_clientes (1 registro)         │
│  CADASTRO_ENDERECO (TIPO=1)          ─┤                                         │
│  ATENDIMENTO_A1 (totalizadores)      ─┘                                         │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│ PEDIDOS                                                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ATENDIMENTO_A1  ──→  prime_pedidos (+ relacionar cliente_id)                   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│ FÓRMULAS                                                                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ATENDIMENTO_A2  ──→  prime_formulas (+ relacionar pedido_id)                   │
│  (TEXTOROTULO = nome do produto!)                                               │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│ ITENS DAS FÓRMULAS (2 fontes!)                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ATENDIMENTO_A3       ─┐                                                        │
│  ESTOQUE (JOIN nome)  ─┼─→  prime_formulas_itens (+ relacionar formula_id)     │
│                        ─┘                                                        │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

# ✅ CHECKLIST ANTES DE MODIFICAR CÓDIGO

Antes de alterar qualquer código de sincronização, verifique:

- [ ] Estou buscando de **TODAS** as tabelas relacionadas?
- [ ] Para clientes: `CLIENTE`, `CADASTRO_TELEFONE`, `CADASTRO_ENDERECO`, `ATENDIMENTO_A1`?
- [ ] Para itens: `ATENDIMENTO_A3` + JOIN `ESTOQUE`?
- [ ] Estou usando `TIPO_CADASTRO = 1` para clientes?
- [ ] Estou combinando `TELEFONEPREFIXO` + `TELEFONE`?
- [ ] Estou combinando `DIANASCIMENTO` + `MESNASCIMENTO` + `ANONASCIMENTO`?
- [ ] Estou convertendo datas para `.isoformat()` (JSON)?
- [ ] Estou respeitando a **ordem de sincronização** (clientes → pedidos → fórmulas → itens)?
- [ ] Estou buscando `cliente_id` antes de inserir pedidos?
- [ ] Estou buscando `pedido_id` antes de inserir fórmulas?
- [ ] Estou buscando `formula_id` antes de inserir itens?
- [ ] Estou usando `UPSERT` (merge-duplicates) para atualizações?
- [ ] Testei com 1 registro antes de rodar em lote?

---

# 🆘 PROBLEMAS COMUNS E SOLUÇÕES

## Problema 1: Cliente sem telefone no Supabase
**Causa:** Não buscou da tabela `CADASTRO_TELEFONE`  
**Solução:** Fazer query separada com `WHERE TIPO_CADASTRO = 1`

## Problema 2: Fórmula sem nome do produto
**Causa:** Não usou `TEXTOROTULO` (tentou buscar de ESTOQUE)  
**Solução:** Usar `ATENDIMENTO_A2.TEXTOROTULO` diretamente

## Problema 3: Item sem nome do produto
**Causa:** Não fez JOIN com tabela `ESTOQUE`  
**Solução:** `LEFT JOIN ESTOQUE E ON A3.CODIGO_ESTOQUE = E.CODIGO`

## Problema 4: Pedido sem cliente_id (FK error)
**Causa:** Inseriu pedido antes de buscar `cliente_id` do Supabase  
**Solução:** Sempre buscar cache de clientes ANTES de inserir pedidos

## Problema 5: Totalizadores zerados
**Causa:** Não calculou/atualizou após inserir pedidos  
**Solução:** Executar query de agregação e fazer UPSERT nos clientes

## Problema 6: Data não serializa (JSON error)
**Causa:** Passou objeto `date` direto para `requests.post`  
**Solução:** Converter para string ISO: `data.isoformat()`

---

# 📞 SUPORTE

Se encontrar problemas:

1. **Leia esta documentação primeiro**
2. Verifique o **checklist**
3. Execute scripts de validação:
   - `verificar_cliente_firebird.py`
   - `comparar_dados_faltantes.py`
4. Verifique logs do `app.py`
5. Entre em contato com time de desenvolvimento

---

**Última atualização:** 28/10/2025  
**Versão:** 2.0  
**Status:** ✅ Validado e testado


