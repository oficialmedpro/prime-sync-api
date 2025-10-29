# Relatório de Análise do Banco de Dados PSBD.FDB

## Resumo da Análise

Foi realizada uma análise completa do banco de dados Firebird `psbd.fdb` para identificar as relações entre clientes, pedidos e fórmulas, com foco na tabela `ATENDIMENTO_A1` como centro do relacionamento.

## Estrutura das Tabelas Principais

### 1. ATENDIMENTO_A1 (Tabela Principal - Pedidos/Atendimentos)
**Campos principais identificados:**
- `CODIGO` - Código único do atendimento
- `CODIGO_CLIENTE` - Chave estrangeira para CLIENTE
- `AVIADA_DT` - Data do pedido
- `STATUS_MOV` - Status do movimento (C = Cancelado)
- `VALORVENDA` - Valor total da venda
- `ENTREGUE_DT` - Data de entrega
- `CODIGO_MEDICO` - Médico responsável
- `OBSERVACAO` - Observações do pedido

### 2. CLIENTE (Dados dos Clientes)
**Campos principais identificados:**
- `CODIGO` - Código único do cliente
- `NOMECLIENTE` - Nome do cliente
- `CPF_CNPJ` - CPF ou CNPJ
- `TELEFONEPREFIXO` + `TELEFONE1` - Telefone
- `CODIGO_CIDADEESTADO` - Chave estrangeira para CIDADEESTADO
- `ENDERECO` - Endereço
- `EMAIL1` - Email

### 3. ATENDIMENTO_A2 (Fórmulas dos Pedidos)
**Campos principais identificados:**
- `CODIGO` - Código único da fórmula
- `CODIGO_ATEND_A1` - Chave estrangeira para ATENDIMENTO_A1
- `NUMEROFORMULA` - Número da fórmula
- `POSOLOGIA` - Posologia da fórmula
- `QTDEGOTAS` - Quantidade de gotas
- `VENCIMENTO_DT` - Data de vencimento
- `VALORFORMULA_VENDA` - Valor da fórmula

### 4. CIDADEESTADO (Localização)
**Campos principais identificados:**
- `CODIGO` - Código único
- `NOMECIDADE` - Nome da cidade
- `UF` - Unidade Federativa
- `CODIGO_IBGE` - Código IBGE

## Relacionamentos Identificados

```
CLIENTE (1) ←→ (N) ATENDIMENTO_A1 (1) ←→ (N) ATENDIMENTO_A2
    ↓
CIDADEESTADO
```

- **CLIENTE → ATENDIMENTO_A1**: Um cliente pode ter vários atendimentos
- **ATENDIMENTO_A1 → ATENDIMENTO_A2**: Um atendimento pode ter várias fórmulas
- **CLIENTE → CIDADEESTADO**: Um cliente pertence a uma cidade/estado

## Consulta SQL Criada

```sql
-- Consulta SQL completa para reunir informações de clientes e pedidos
SELECT 
    -- Dados do Cliente
    C.CODIGO as CODIGO_CLIENTE,
    TRIM(C.NOMECLIENTE) as NOME_CLIENTE,
    TRIM(C.CPF_CNPJ) as CPF_CNPJ,
    CASE 
        WHEN C.TELEFONEPREFIXO IS NOT NULL AND C.TELEFONE1 IS NOT NULL 
        THEN TRIM(C.TELEFONEPREFIXO) || ' ' || TRIM(C.TELEFONE1)
        ELSE TRIM(C.TELEFONE1)
    END as TELEFONE,
    TRIM(CE.NOMECIDADE) as CIDADE,
    TRIM(CE.UF) as ESTADO,
    
    -- Dados do Pedido/Atendimento
    A1.CODIGO as CODIGO_ATENDIMENTO,
    A1.AVIADA_DT as DATA_PEDIDO,
    A1.STATUS_MOV as STATUS_PEDIDO,
    A1.VALORVENDA as VALOR_TOTAL,
    TRIM(A1.OBSERVACAO) as OBSERVACOES_PEDIDO,
    
    -- Fórmulas associadas (agrupadas por vírgula)
    LIST(
        'Fórmula ' || TRIM(A2.NUMEROFORMULA) || 
        CASE 
            WHEN A2.POSOLOGIA IS NOT NULL THEN ' - ' || TRIM(A2.POSOLOGIA)
            ELSE ''
        END,
        ', '
    ) as FORMULAS_DESCRICAO,
    
    -- Contagem de fórmulas
    COUNT(A2.CODIGO) as QUANTIDADE_FORMULAS,
    
    -- Data de entrega
    A1.ENTREGUE_DT as DATA_ENTREGA,
    
    -- Médico responsável
    CASE 
        WHEN A1.CODIGO_MEDICO IS NOT NULL THEN 'Médico: ' || CAST(A1.CODIGO_MEDICO AS VARCHAR(10))
        ELSE 'Sem médico associado'
    END as MEDICO_RESPONSAVEL

FROM ATENDIMENTO_A1 A1
    INNER JOIN CLIENTE C ON A1.CODIGO_CLIENTE = C.CODIGO
    LEFT JOIN CIDADEESTADO CE ON C.CODIGO_CIDADEESTADO = CE.CODIGO
    LEFT JOIN ATENDIMENTO_A2 A2 ON A1.CODIGO = A2.CODIGO_ATEND_A1

WHERE A1.STATUS_MOV <> 'C' -- Excluir pedidos cancelados
  AND A1.AVIADA_DT IS NOT NULL -- Apenas pedidos com data

GROUP BY 
    C.CODIGO, C.NOMECLIENTE, C.CPF_CNPJ, C.TELEFONEPREFIXO, C.TELEFONE1,
    CE.NOMECIDADE, CE.UF,
    A1.CODIGO, A1.AVIADA_DT, A1.STATUS_MOV, A1.VALORVENDA, A1.OBSERVACAO,
    A1.ENTREGUE_DT, A1.CODIGO_MEDICO

ORDER BY A1.AVIADA_DT DESC, C.NOMECLIENTE;
```

## Observações Importantes

### Restrições de Permissão
- O usuário `OFICIALMED_TESTE` possui **permissões limitadas** no banco de dados
- Não foi possível executar consultas nas tabelas principais devido a restrições de acesso
- Recomenda-se solicitar permissões de leitura (SELECT) para as tabelas:
  - `ATENDIMENTO_A1`
  - `CLIENTE`
  - `ATENDIMENTO_A2`
  - `CIDADEESTADO`

### Funcionalidades da Consulta
1. **Agrupamento de Fórmulas**: Múltiplas fórmulas por pedido são agrupadas em uma única linha, separadas por vírgula
2. **Filtros Aplicados**: Exclui pedidos cancelados e pedidos sem data
3. **Formatação de Dados**: Telefone formatado, textos limpos com TRIM()
4. **Ordenação**: Por data de pedido (mais recentes primeiro) e nome do cliente

### Campos de Saída
- **Identificação do Cliente**: Código, nome, CPF/CNPJ, telefone, cidade, estado
- **Dados do Pedido**: Código, data, status, valor total, observações
- **Fórmulas**: Descrição agrupada e quantidade
- **Informações Adicionais**: Data de entrega, médico responsável

## Recomendações

1. **Solicitar Permissões**: Contatar o administrador do banco para conceder permissões de leitura
2. **Testar Consulta**: Após obter permissões, executar a consulta para validar os resultados
3. **Ajustes Finais**: Possíveis ajustes na consulta baseados nos dados reais encontrados
4. **Exportação**: A consulta está pronta para exportar dados em formato tabular

## Arquivos Gerados

- `consulta_completa_clientes_pedidos.sql` - Consulta SQL principal
- `analisar_atendimento_a1.sql` - Análise da estrutura da tabela principal
- `analisar_clientes.sql` - Análise da estrutura da tabela de clientes
- `analisar_atendimento_a2.sql` - Análise da estrutura da tabela de fórmulas
- `analisar_cidadeestado.sql` - Análise da estrutura da tabela de localização
