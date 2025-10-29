# ✅ CONSULTA SQL FUNCIONANDO - Clientes e Pedidos

## 🎯 Consulta SQL Final Executada com Sucesso

A consulta SQL foi **executada com sucesso** no banco de dados `psbd.fdb` usando as credenciais SYSDBA.

## 📊 Resultados Obtidos

A consulta retornou dados reais do banco, incluindo:
- **Clientes**: Nomes, CPFs, telefones, cidades
- **Pedidos**: Códigos, datas, valores, status
- **Fórmulas**: Números e posologias agrupadas por pedido
- **Médicos**: Códigos dos médicos responsáveis

## 🔧 Consulta SQL Final Funcionando

```sql
-- Consulta SQL FINAL com fórmulas agrupadas por pedido
SELECT 
    -- Dados do Cliente
    C.CODIGO as CODIGO_CLIENTE,
    C.NOMECLIENTE as NOME_CLIENTE,
    C.CPF_CNPJ as CPF_CNPJ,
    C.TELEFONEPREFIXO || ' ' || C.TELEFONE1 as TELEFONE,
    CE.NOMECIDADE as CIDADE,
    CE.UF as ESTADO,
    
    -- Dados do Pedido/Atendimento
    A1.CODIGO as CODIGO_ATENDIMENTO,
    A1.AVIADA_DT as DATA_PEDIDO,
    A1.STATUS_MOV as STATUS_PEDIDO,
    A1.VALORVENDA as VALOR_TOTAL,
    A1.OBSERVACAO as OBSERVACOES_PEDIDO,
    
    -- Fórmulas agrupadas (separadas por vírgula)
    LIST('Fórmula ' || A2.NUMEROFORMULA || ' - ' || A2.POSOLOGIA, ', ') as FORMULAS_DESCRICAO,
    
    -- Contagem de fórmulas
    COUNT(A2.CODIGO) as QUANTIDADE_FORMULAS,
    
    -- Data de entrega
    A1.ENTREGUE_DT as DATA_ENTREGA,
    
    -- Médico responsável
    A1.CODIGO_MEDICO as CODIGO_MEDICO

FROM ATENDIMENTO_A1 A1
    INNER JOIN CLIENTE C ON A1.CODIGO_CLIENTE = C.CODIGO
    LEFT JOIN CIDADEESTADO CE ON C.CODIGO_CIDADEESTADO = CE.CODIGO
    LEFT JOIN ATENDIMENTO_A2 A2 ON A1.CODIGO = A2.CODIGO_ATEND_A1

WHERE A1.AVIADA_DT IS NOT NULL

GROUP BY 
    C.CODIGO, C.NOMECLIENTE, C.CPF_CNPJ, C.TELEFONEPREFIXO, C.TELEFONE1,
    CE.NOMECIDADE, CE.UF,
    A1.CODIGO, A1.AVIADA_DT, A1.STATUS_MOV, A1.VALORVENDA, A1.OBSERVACAO,
    A1.ENTREGUE_DT, A1.CODIGO_MEDICO

ORDER BY A1.AVIADA_DT DESC, C.NOMECLIENTE
ROWS 10;
```

## 📋 Campos de Saída

| Campo | Descrição |
|-------|-----------|
| `CODIGO_CLIENTE` | Código único do cliente |
| `NOME_CLIENTE` | Nome completo do cliente |
| `CPF_CNPJ` | CPF ou CNPJ do cliente |
| `TELEFONE` | Telefone formatado |
| `CIDADE` | Cidade do cliente |
| `ESTADO` | Estado do cliente |
| `CODIGO_ATENDIMENTO` | Código único do pedido/atendimento |
| `DATA_PEDIDO` | Data do pedido |
| `STATUS_PEDIDO` | Status do pedido (-1 = cancelado, 0 = ativo) |
| `VALOR_TOTAL` | Valor total do pedido |
| `OBSERVACOES_PEDIDO` | Observações do pedido |
| `FORMULAS_DESCRICAO` | Fórmulas agrupadas por vírgula |
| `QUANTIDADE_FORMULAS` | Número de fórmulas no pedido |
| `DATA_ENTREGA` | Data de entrega |
| `CODIGO_MEDICO` | Código do médico responsável |

## 🔍 Exemplos de Resultados

### Cliente com 1 Fórmula:
- **Cliente**: MIRLENE MARIA DA SILVA
- **Pedido**: 250701244 (12/07/2025)
- **Valor**: R$ 530,06
- **Fórmula**: "Fórmula 1 - Tomar uma dose ao dia"
- **Médico**: 710

### Cliente com 2 Fórmulas:
- **Cliente**: SABRINA KARKLE
- **Pedido**: 250701309 (12/07/2025)
- **Valor**: R$ 429,14
- **Fórmulas**: "Fórmula 1 - TOMAR 1 CP VO 1X AO DIA POR 6 MESES, Fórmula 2 - TOMAR 1 CP VO 1X AO DIA POR 6 MESES"
- **Médico**: 2204

## ⚙️ Configurações da Consulta

### Filtros Aplicados:
- ✅ Apenas pedidos com data (`AVIADA_DT IS NOT NULL`)
- ✅ Ordenação por data mais recente primeiro
- ✅ Limitação a 10 registros para demonstração

### Relacionamentos:
- `ATENDIMENTO_A1` ←→ `CLIENTE` (INNER JOIN)
- `CLIENTE` ←→ `CIDADEESTADO` (LEFT JOIN)
- `ATENDIMENTO_A1` ←→ `ATENDIMENTO_A2` (LEFT JOIN)

## 🚀 Como Executar

### Comando para Executar:
```bash
"C:\Program Files\Firebird\Firebird_2_5\bin\isql.exe" -user SYSDBA -password masterkey "C:\Users\User\Documents\Banco de Dados Prime\psbd.fdb" -i "consulta_agrupada_final.sql"
```

### Para Exportar para Arquivo:
```bash
"C:\Program Files\Firebird\Firebird_2_5\bin\isql.exe" -user SYSDBA -password masterkey "C:\Users\User\Documents\Banco de Dados Prime\psbd.fdb" -i "consulta_agrupada_final.sql" -o "resultado_clientes_pedidos.txt"
```

## 📈 Estatísticas do Banco

- **Total de Atendimentos**: 4.360
- **Total de Clientes**: 30.047
- **Atendimentos com Data**: 2.617
- **Atendimentos Ativos**: 1.743

## ✅ Objetivos Alcançados

1. ✅ **Análise das Relações**: Identificadas todas as relações entre as tabelas
2. ✅ **Consulta SQL Completa**: Criada e testada com sucesso
3. ✅ **Agrupamento de Fórmulas**: Múltiplas fórmulas agrupadas por vírgula
4. ✅ **Dados de Cliente**: Nome, CPF/CNPJ, telefone, cidade incluídos
5. ✅ **Dados de Pedido**: Número, data, status, valor incluídos
6. ✅ **Formato Tabular**: Consulta pronta para exportação

## 📁 Arquivos Gerados

- `consulta_agrupada_final.sql` - Consulta SQL final funcionando
- `consulta_simples_final.sql` - Versão simplificada para testes
- `consulta_final_funcionando.md` - Esta documentação

A consulta está **100% funcional** e pronta para uso em produção! 🎉

