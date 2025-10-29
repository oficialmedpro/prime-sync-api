# 🔄 MAPEAMENTO DE DADOS FIREBIRD → SUPABASE

## 📋 Resumo do Mapeamento

Este documento detalha como os dados do banco Firebird (Prime Software) são mapeados e exportados para as tabelas do Supabase.

## 🗂️ Tabelas de Origem (Firebird)

### 1. `CLIENTE` → `prime_clientes`

| Campo Firebird | Campo Supabase | Transformação | Observações |
|---|---|---|---|
| `CODIGO` | `codigo_cliente_original` | Direto | ID original preservado |
| `NOMECLIENTE` | `nome` | Limpeza de string | Nome do cliente |
| `CPF_CNPJ` | `cpf_cnpj` | Limpeza de string | Documento |
| `DIANASCIMENTO` + `MESNASCIMENTO` + `ANONASCIMENTO` | `data_nascimento` | Concatenação → DATE | Data de nascimento |
| `SEXO` | `sexo` | Direto | 1=Masculino, 2=Feminino |
| `EMAIL1` | `email` | Limpeza de string | Email principal |
| `TELEFONEPREFIXO` + `TELEFONE1` | `telefone` | Concatenação | Telefone formatado |
| `ENDERECO` | `endereco_logradouro` | Limpeza de string | Logradouro |
| `NUMERO` | `endereco_numero` | Limpeza de string | Número |
| `CEP` | `endereco_cep` | Limpeza de string | CEP |
| `CIDADEESTADO.NOMECIDADE` | `endereco_cidade` | JOIN + limpeza | Cidade (via JOIN) |
| `CIDADEESTADO.UF` | `endereco_estado` | JOIN + limpeza | Estado (via JOIN) |
| `ATIVO` | `ativo` | `== -1` | Boolean (True se ativo) |

**Query de Origem:**
```sql
SELECT 
    C.CODIGO,
    C.NOMECLIENTE,
    C.CPF_CNPJ,
    C.DIANASCIMENTO,
    C.MESNASCIMENTO,
    C.ANONASCIMENTO,
    C.SEXO,
    C.EMAIL1,
    C.TELEFONEPREFIXO,
    C.TELEFONE1,
    C.ENDERECO,
    C.NUMERO,
    C.CEP,
    CE.NOMECIDADE,
    CE.UF,
    C.ATIVO
FROM CLIENTE C
LEFT JOIN CIDADEESTADO CE ON C.CODIGO_CIDADEESTADO = CE.CODIGO
WHERE C.ATIVO = -1
```

### 2. `ATENDIMENTO_A1` → `prime_pedidos`

| Campo Firebird | Campo Supabase | Transformação | Observações |
|---|---|---|---|
| `CODIGO` | `codigo_orcamento_original` | Direto | ID original do orçamento |
| `CODIGO_CLIENTE` | `codigo_cliente_original` | Direto | ID do cliente |
| `AVIADA_DT` | `data_aprovacao` | String → TIMESTAMP | Data de aprovação |
| `ENTREGUE_DT` | `data_entrega` | String → TIMESTAMP | Data de entrega |
| `STATUS_MOV` | `status_mov` | Direto | Status original |
| `VALORVENDA` | `valor_total` | Decimal → Float | Valor total |
| `OBSERVACAO` | `observacoes` | Limpeza de string | Observações |
| `AVIADA_DT IS NOT NULL` | `status_aprovacao` | Lógica | 'APROVADO' ou 'NAO_APROVADO' |
| `ENTREGUE_DT IS NOT NULL` | `status_entrega` | Lógica | 'ENTREGUE' ou 'NAO_ENTREGUE' |
| Lógica complexa | `status_geral` | Lógica | 'APROVADO', 'PENDENTE', 'CANCELADO', 'ENTREGUE' |

**Query de Origem:**
```sql
SELECT 
    A1.CODIGO,
    A1.CODIGO_CLIENTE,
    A1.AVIADA_DT,
    A1.ENTREGUE_DT,
    A1.STATUS_MOV,
    A1.VALORVENDA,
    A1.OBSERVACAO
FROM ATENDIMENTO_A1 A1
WHERE A1.AVIADA_DT IS NOT NULL
```

**Lógica de Status:**
```python
# Status de aprovação
status_aprovacao = "APROVADO" if aviada_dt else "NAO_APROVADO"

# Status de entrega
status_entrega = "ENTREGUE" if entregue_dt else "NAO_ENTREGUE"

# Status geral
if status_mov == -1:
    status_geral = "CANCELADO"
elif aviada_dt and entregue_dt:
    status_geral = "ENTREGUE"
elif aviada_dt:
    status_geral = "APROVADO"
else:
    status_geral = "PENDENTE"
```

### 3. `FORMAFARMACEUTICA_PROCESSO_TIPO` → `prime_tipos_processo`

| Campo Firebird | Campo Supabase | Transformação | Observações |
|---|---|---|---|
| `CODIGO` | `codigo_tipo_original` | Direto | ID original |
| `NOMETIPO` | `nome_processo` | Limpeza de string | Nome do processo |
| `NOMEFICHA` | `nome_ficha` | Limpeza de string | Nome da ficha |
| `TIPO_PRODUCAO` | `tipo_producao` | Direto | Tipo de produção |
| `SEQUENCIA` | `sequencia` | Direto | Ordem de execução |
| `ATIVO` | `ativo` | `== -1` | Boolean |
| `PROCESSO_OPCIONAL` | `processo_opcional` | `== -1` | Boolean |
| `PAGARCOMISSAO` | `pagar_comissao` | `== -1` | Boolean |
| `REGISTRAR_BAIXA` | `registrar_baixa` | `== -1` | Boolean |
| `BLOQUEAR_CALCULO` | `bloquear_calculo` | `== -1` | Boolean |
| `LIBERAR_ENTREGA` | `liberar_entrega` | `== -1` | Boolean |
| `BLOQUEAR_RECEITA` | `bloquear_receita` | `== -1` | Boolean |
| `OBSERVACAO` | `observacao` | Limpeza de string | Observações |

**Query de Origem:**
```sql
SELECT 
    CODIGO,
    NOMETIPO,
    NOMEFICHA,
    TIPO_PRODUCAO,
    SEQUENCIA,
    ATIVO,
    PROCESSO_OPCIONAL,
    PAGARCOMISSAO,
    REGISTRAR_BAIXA,
    BLOQUEAR_CALCULO,
    LIBERAR_ENTREGA,
    BLOQUEAR_RECEITA,
    OBSERVACAO
FROM FORMAFARMACEUTICA_PROCESSO_TIPO
ORDER BY SEQUENCIA
```

### 4. `PROCESSO_MANIPULACAO` → `prime_rastreabilidade`

| Campo Firebird | Campo Supabase | Transformação | Observações |
|---|---|---|---|
| `CODIGO` | `codigo_processo_original` | Direto | ID original |
| `TIPO_MOV` | `tipo_movimento` | Direto | Tipo de movimento |
| `CODIGO_MOV` | `codigo_orcamento_original` | Direto | ID do orçamento |
| `CODIGO_PROCESSO_TIPO` | `codigo_tipo_original` | Direto | ID do tipo de processo |
| `CODIGO_FUNCIONARIO` | `codigo_funcionario` | Direto | ID do funcionário |
| `DATA_PROCESSO` | `data_processo` | String → DATE | Data do processo |
| `HORA_PROCESSO` | `hora_processo` | String → TIME | Hora do processo |
| `SEQUENCIA` | `sequencia` | Direto | Sequência de execução |
| - | `status_processo` | Constante | 'CONCLUIDO' (todos os registros) |

**Query de Origem:**
```sql
SELECT 
    PM.CODIGO,
    PM.TIPO_MOV,
    PM.CODIGO_MOV,
    PM.CODIGO_PROCESSO_TIPO,
    PM.CODIGO_FUNCIONARIO,
    PM.DATA_PROCESSO,
    PM.HORA_PROCESSO,
    PM.SEQUENCIA
FROM PROCESSO_MANIPULACAO PM
ORDER BY PM.CODIGO_MOV, PM.SEQUENCIA
```

### 5. `ATENDIMENTO_A2` → `prime_formulas`

| Campo Firebird | Campo Supabase | Transformação | Observações |
|---|---|---|---|
| `CODIGO_ATEND_A1` | `codigo_orcamento_original` | Direto | ID do orçamento |
| `NUMEROFORMULA` | `numero_formula` | Direto | Número da fórmula |
| `DESCRICAO` | `descricao` | Limpeza de string | Descrição da fórmula |
| `POSOLOGIA` | `posologia` | Limpeza de string | Posologia |
| `VALOR` | `valor_formula` | Decimal → Float | Valor da fórmula |

**Query de Origem:**
```sql
SELECT 
    A2.CODIGO_ATEND_A1,
    A2.NUMEROFORMULA,
    A2.DESCRICAO,
    A2.POSOLOGIA,
    A2.VALOR
FROM ATENDIMENTO_A2 A2
INNER JOIN ATENDIMENTO_A1 A1 ON A2.CODIGO_ATEND_A1 = A1.CODIGO
WHERE A1.AVIADA_DT IS NOT NULL
```

## 🔧 Funções de Transformação

### 1. Conversão de Data
```python
def converter_data(data_str: str) -> Optional[str]:
    """Converte string de data para ISO format"""
    if not data_str:
        return None
    try:
        if isinstance(data_str, str):
            return datetime.strptime(data_str, '%Y-%m-%d').date().isoformat()
        return data_str.isoformat() if hasattr(data_str, 'isoformat') else str(data_str)
    except:
        return None
```

### 2. Conversão de Timestamp
```python
def converter_timestamp(data_str: str) -> Optional[str]:
    """Converte string de timestamp para ISO format"""
    if not data_str:
        return None
    try:
        if isinstance(data_str, str):
            return datetime.strptime(data_str, '%Y-%m-%d %H:%M:%S').isoformat()
        return data_str.isoformat() if hasattr(data_str, 'isoformat') else str(data_str)
    except:
        return None
```

### 3. Conversão de Decimal
```python
def converter_decimal(valor) -> Optional[float]:
    """Converte Decimal para float"""
    if valor is None:
        return None
    try:
        return float(valor)
    except:
        return None
```

### 4. Limpeza de String
```python
def limpar_string(texto: str) -> Optional[str]:
    """Limpa e valida string"""
    if not texto:
        return None
    return str(texto).strip() if str(texto).strip() else None
```

## 📊 Ordem de Exportação

1. **`prime_tipos_processo`** - Primeiro (referência para rastreabilidade)
2. **`prime_clientes`** - Segundo (referência para pedidos)
3. **`prime_pedidos`** - Terceiro (referência para rastreabilidade e fórmulas)
4. **`prime_rastreabilidade`** - Quarto (depende de pedidos e tipos)
5. **`prime_formulas`** - Quinto (depende de pedidos)

## 🔄 Estratégia de Upsert

Todos os dados são inseridos usando **UPSERT** para evitar duplicatas:
```python
result = self.supabase.table(tabela).upsert(dados).execute()
```

## 📈 Paginação

Para grandes volumes de dados, usa-se paginação:
```python
cursor.execute(f"""
    SELECT ...
    FROM tabela
    ORDER BY campo
    ROWS {limite} TO {offset + limite}
""")
```

## 🎯 Objetivos do Mapeamento

1. **Preservar IDs Originais:** Manter referências ao banco Prime
2. **Limpar Dados:** Remover espaços e caracteres inválidos
3. **Converter Tipos:** Adaptar tipos Firebird para PostgreSQL
4. **Manter Relacionamentos:** Preservar integridade referencial
5. **Adicionar Metadados:** Timestamps de criação e atualização
6. **Enriquecer Dados:** Adicionar campos calculados (RFV, status, etc.)
