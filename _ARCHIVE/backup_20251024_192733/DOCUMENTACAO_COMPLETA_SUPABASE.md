# 📘 Documentação Completa - Integração Firebird → Supabase
## Sistema de Exportação e Análise RFV - Prime Farmacêutica

**Data de criação:** 21 de Outubro de 2025  
**Versão:** 2.0  
**Status:** Produção

---

## 📑 Índice

1. [Visão Geral do Sistema](#1-visão-geral-do-sistema)
2. [Arquitetura da Solução](#2-arquitetura-da-solução)
3. [Estrutura do Banco Supabase](#3-estrutura-do-banco-supabase)
4. [Dados Exportados do Firebird](#4-dados-exportados-do-firebird)
5. [Estrutura de Código Python](#5-estrutura-de-código-python)
6. [Views e Consultas Analíticas](#6-views-e-consultas-analíticas)
7. [Permissões e Segurança](#7-permissões-e-segurança)
8. [Fluxo de Exportação](#8-fluxo-de-exportação)
9. [Análise RFV Implementada](#9-análise-rfv-implementada)
10. [Exemplos de Uso](#10-exemplos-de-uso)
11. [Manutenção e Troubleshooting](#11-manutenção-e-troubleshooting)

---

## 1. Visão Geral do Sistema

### 1.1 Objetivo

Este sistema foi desenvolvido para integrar o banco de dados **Firebird** (sistema ERP Prime) com o **Supabase** (PostgreSQL na nuvem), permitindo:

- ✅ **Análise RFV** (Recência, Frequência e Valor) de clientes
- ✅ **Rastreabilidade completa** de pedidos e processos de produção
- ✅ **Dashboards e relatórios** em tempo real
- ✅ **APIs modernas** para aplicações web e mobile
- ✅ **Histórico centralizado** de clientes e pedidos

### 1.2 Tecnologias Utilizadas

| Tecnologia | Versão | Finalidade |
|------------|--------|------------|
| **Firebird** | 3.0+ | Banco de dados ERP (origem) |
| **Supabase** | PostgreSQL 15 | Banco de dados na nuvem (destino) |
| **Python** | 3.11+ | Scripts de exportação |
| **fdb** | 2.0+ | Driver Python para Firebird |
| **supabase-py** | 2.0+ | Cliente Python para Supabase |

### 1.3 Benefícios

- 🚀 **Desempenho**: Consultas rápidas com índices otimizados
- 🔒 **Segurança**: Controle de acesso com RLS (Row Level Security)
- 📊 **Análises**: Views prontas para Business Intelligence
- 🌐 **API REST**: Acesso via HTTP para qualquer plataforma
- ☁️ **Escalabilidade**: Infraestrutura gerenciada pelo Supabase

---

## 2. Arquitetura da Solução

### 2.1 Diagrama de Arquitetura

```
┌──────────────────────────────────────────────────────────────┐
│                    FIREBIRD ERP (psbd.fdb)                    │
│                    Host: 72.60.13.173:3050                    │
│                                                               │
│  ┌─────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │   CLIENTE   │  │ ATENDIMENTO_A1   │  │ ATENDIMENTO_A2  │ │
│  │  (Clientes) │  │   (Orçamentos)   │  │   (Fórmulas)    │ │
│  └─────────────┘  └──────────────────┘  └─────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────┐  ┌──────────────────┐  │
│  │ FORMAFARMACEUTICA_PROCESSO_TIPO │  │ PROCESSO_        │  │
│  │      (Tipos de Processo)        │  │ MANIPULACAO      │  │
│  └─────────────────────────────────┘  └──────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                            │
                            │ 🔄 exportar_firebird_supabase_final.py
                            │    (Execução manual ou agendada)
                            ▼
┌──────────────────────────────────────────────────────────────┐
│              SUPABASE (PostgreSQL na Nuvem)                   │
│              URL: https://agdffspstbxeqhqtltvb.supabase.co   │
│                                                               │
│  Schema: api                                                  │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │ prime_clientes   │◄─│ prime_pedidos    │                 │
│  │   (Clientes)     │  │   (Orçamentos)   │                 │
│  └──────────────────┘  └──────────────────┘                 │
│                                │                              │
│  ┌──────────────────────────┐  │  ┌────────────────────┐    │
│  │ prime_tipos_processo     │◄─┼──│ prime_             │    │
│  │  (Tipos Produção)        │  │  │ rastreabilidade    │    │
│  └──────────────────────────┘  │  └────────────────────┘    │
│                                 │                             │
│  ┌──────────────────────────┐  │                             │
│  │ prime_formulas           │◄─┘                             │
│  │  (Fórmulas)              │                                │
│  └──────────────────────────┘                                │
│                                                               │
│  Views Analíticas:                                            │
│  • vw_prime_clientes_rfv                                      │
│  • vw_prime_rastreabilidade_completa                          │
│  • vw_prime_pedidos_status                                    │
└──────────────────────────────────────────────────────────────┘
                            │
                            │ 🌐 API REST / SDK
                            ▼
            ┌────────────────────────────────┐
            │  Aplicações (Frontend/Mobile)  │
            │  • Dashboards                  │
            │  • Relatórios                  │
            │  • Apps Mobile                 │
            └────────────────────────────────┘
```

### 2.2 Fluxo de Dados

1. **Extração** → Python conecta ao Firebird e executa queries SQL
2. **Transformação** → Dados são validados, formatados e preparados
3. **Carga** → Dados são enviados ao Supabase via API REST
4. **Disponibilização** → Dados ficam disponíveis via views e API

---

## 3. Estrutura do Banco Supabase

### 3.1 Schema: `api`

Todas as tabelas foram criadas no schema `api` (não no `public`) para:
- ✅ Melhor organização
- ✅ Separação de dados do sistema Prime de outros dados
- ✅ Facilitar permissões e políticas de acesso

### 3.2 Tabela: `prime_clientes`

**Finalidade:** Armazena dados cadastrais dos clientes do sistema Prime com métricas RFV agregadas.

#### Estrutura Completa

| Coluna | Tipo | Obrigatório | Descrição | Origem Firebird |
|--------|------|-------------|-----------|-----------------|
| `id` | BIGSERIAL | ✅ PK | ID sequencial interno | (gerado) |
| `codigo_cliente_original` | INTEGER | ✅ UNIQUE | Código do cliente no Prime | `CLIENTE.CODIGO` |
| `nome` | VARCHAR(255) | ✅ | Nome completo | `CLIENTE.NOMECLIENTE` |
| `cpf_cnpj` | VARCHAR(20) | ❌ | CPF ou CNPJ | `CLIENTE.CPF_CNPJ` |
| `data_nascimento` | DATE | ❌ | Data de nascimento | `CLIENTE.DIA/MES/ANONASCIMENTO` |
| `sexo` | INTEGER | ❌ | Sexo (1=M, 2=F) | `CLIENTE.SEXO` |
| `email` | VARCHAR(255) | ❌ | E-mail principal | `CLIENTE.EMAIL1` |
| `telefone` | VARCHAR(20) | ❌ | Telefone com DDD | `CLIENTE.TELEFONE1` |
| `endereco_logradouro` | VARCHAR(255) | ❌ | Rua/Avenida | `CLIENTE.ENDERECO` |
| `endereco_numero` | VARCHAR(20) | ❌ | Número | `CLIENTE.NUMERO` |
| `endereco_cep` | VARCHAR(10) | ❌ | CEP | `CLIENTE.CEP` |
| `endereco_cidade` | VARCHAR(100) | ❌ | Cidade | `CIDADEESTADO.NOMECIDADE` |
| `endereco_estado` | VARCHAR(2) | ❌ | UF | `CIDADEESTADO.UF` |
| `endereco_observacao` | TEXT | ❌ | Complemento | - |
| **Métricas RFV** | | | | |
| `total_orcamentos` | INTEGER | ✅ | Total de orçamentos | (calculado) |
| `total_orcamentos_aprovados` | INTEGER | ✅ | Orçamentos aprovados | (calculado) |
| `total_orcamentos_entregues` | INTEGER | ✅ | Orçamentos entregues | (calculado) |
| `valor_total_orcamentos` | DECIMAL(15,2) | ✅ | Valor total geral | (calculado) |
| `valor_total_aprovados` | DECIMAL(15,2) | ✅ | Valor aprovados | (calculado) |
| `valor_total_entregues` | DECIMAL(15,2) | ✅ | Valor entregues | (calculado) |
| `valor_medio_orcamento` | DECIMAL(15,2) | ✅ | Ticket médio geral | (calculado) |
| `valor_medio_aprovado` | DECIMAL(15,2) | ✅ | Ticket médio aprovados | (calculado) |
| `valor_medio_entregue` | DECIMAL(15,2) | ✅ | Ticket médio entregues | (calculado) |
| `primeira_compra` | DATE | ❌ | Data da 1ª compra | (calculado) |
| `ultima_compra` | DATE | ❌ | Data da última compra | (calculado) |
| `ultima_atualizacao` | TIMESTAMP | ✅ | Última atualização dos dados | (auto) |
| `ativo` | BOOLEAN | ✅ | Cliente ativo? | `CLIENTE.ATIVO` |
| `score_rfv` | INTEGER | ✅ | Score RFV calculado | (calculado) |
| `created_at` | TIMESTAMP | ✅ | Data de criação do registro | (auto) |
| `updated_at` | TIMESTAMP | ✅ | Data de atualização | (auto - trigger) |

#### Índices Criados

```sql
idx_prime_clientes_codigo_original  -- Busca por código do Prime
idx_prime_clientes_cpf              -- Busca por CPF
idx_prime_clientes_email            -- Busca por e-mail
idx_prime_clientes_nome             -- Busca por nome
idx_prime_clientes_score_rfv        -- Ordenação por score RFV
idx_prime_clientes_ultima_compra    -- Ordenação por recência
```

---

### 3.3 Tabela: `prime_pedidos`

**Finalidade:** Armazena orçamentos/pedidos do sistema Prime com status de aprovação, entrega e rastreabilidade de produção.

#### Estrutura Completa

| Coluna | Tipo | Obrigatório | Descrição | Origem Firebird |
|--------|------|-------------|-----------|-----------------|
| `id` | BIGSERIAL | ✅ PK | ID sequencial interno | (gerado) |
| `codigo_orcamento_original` | INTEGER | ✅ UNIQUE | Código do orçamento no Prime | `ATENDIMENTO_A1.CODIGO` |
| `cliente_id` | BIGINT | ✅ FK | Referência ao cliente | (relacionamento) |
| `codigo_cliente_original` | INTEGER | ✅ | Código do cliente (desnormalizado) | `ATENDIMENTO_A1.CODIGO_CLIENTE` |
| **Datas** | | | | |
| `data_criacao` | TIMESTAMP | ❌ | Data de criação do orçamento | `ATENDIMENTO_A1.DATA_CRIACAO` |
| `data_aprovacao` | TIMESTAMP | ❌ | Data de aprovação (aviada) | `ATENDIMENTO_A1.AVIADA_DT` |
| `data_entrega` | TIMESTAMP | ❌ | Data de entrega | `ATENDIMENTO_A1.ENTREGUE_DT` |
| `data_cancelamento` | TIMESTAMP | ❌ | Data de cancelamento | `ATENDIMENTO_A1.CANCELADO_DT` |
| **Valores** | | | | |
| `valor_total` | DECIMAL(15,2) | ✅ | Valor total do pedido | `ATENDIMENTO_A1.VALORVENDA` |
| `valor_desconto` | DECIMAL(15,2) | ❌ | Valor de desconto | `ATENDIMENTO_A1.DESCONTO` |
| `valor_final` | DECIMAL(15,2) | ❌ | Valor final | (calculado) |
| **Status** | | | | |
| `status_aprovacao` | VARCHAR(20) | ✅ | APROVADO / NAO_APROVADO | (calculado de AVIADA_DT) |
| `status_entrega` | VARCHAR(20) | ✅ | ENTREGUE / NAO_ENTREGUE | (calculado de ENTREGUE_DT) |
| `status_geral` | VARCHAR(20) | ✅ | Status consolidado | (calculado) |
| `status_mov` | INTEGER | ❌ | Status original do banco | `ATENDIMENTO_A1.STATUS_MOV` |
| **Produção e Logística** | | | | |
| `data_inicio_producao` | TIMESTAMP | ❌ | Início da produção | (calculado da rastreabilidade) |
| `data_fim_producao` | TIMESTAMP | ❌ | Fim da produção | (calculado da rastreabilidade) |
| `data_prevista_entrega` | TIMESTAMP | ❌ | Previsão de entrega | - |
| `laboratorio_iniciado` | BOOLEAN | ✅ | Laboratório iniciou? | (calculado) |
| `laboratorio_finalizado` | BOOLEAN | ✅ | Laboratório finalizou? | (calculado) |
| `data_laboratorio_inicio` | TIMESTAMP | ❌ | Início laboratório | (calculado) |
| `data_laboratorio_fim` | TIMESTAMP | ❌ | Fim laboratório | (calculado) |
| `transporte_iniciado` | BOOLEAN | ✅ | Transporte iniciou? | (calculado) |
| `transporte_finalizado` | BOOLEAN | ✅ | Transporte finalizado? | (calculado) |
| `data_transporte_inicio` | TIMESTAMP | ❌ | Início transporte | (calculado) |
| `data_transporte_fim` | TIMESTAMP | ❌ | Fim transporte | (calculado) |
| **Observações** | | | | |
| `observacoes` | TEXT | ❌ | Observações gerais | `ATENDIMENTO_A1.OBSERVACAO` |
| `observacao_cancelamento` | TEXT | ❌ | Motivo cancelamento | - |
| `observacao_descarte` | TEXT | ❌ | Motivo descarte | - |
| `observacao_producao` | TEXT | ❌ | Observações produção | - |
| **Métricas Temporais** | | | | |
| `dias_para_aprovacao` | INTEGER | ❌ | Dias até aprovação | (calculado) |
| `dias_para_entrega` | INTEGER | ❌ | Dias até entrega | (calculado) |
| `dias_total_processo` | INTEGER | ❌ | Dias totais | (calculado) |
| `dias_producao` | INTEGER | ❌ | Dias em produção | (calculado) |
| `dias_transporte` | INTEGER | ❌ | Dias em transporte | (calculado) |
| `created_at` | TIMESTAMP | ✅ | Data de criação | (auto) |
| `updated_at` | TIMESTAMP | ✅ | Data de atualização | (auto - trigger) |

#### Status Possíveis

**status_aprovacao:**
- `APROVADO` - Orçamento foi aviado (AVIADA_DT preenchida)
- `NAO_APROVADO` - Orçamento ainda não foi aviado

**status_entrega:**
- `ENTREGUE` - Pedido foi entregue (ENTREGUE_DT preenchida)
- `NAO_ENTREGUE` - Pedido ainda não entregue

**status_geral:**
- `ENTREGUE` - Aprovado e entregue
- `APROVADO` - Aprovado mas não entregue
- `PENDENTE` - Aguardando aprovação
- `CANCELADO` - Cancelado (STATUS_MOV = -1)
- `DESCARTADO` - Descartado

#### Índices Criados

```sql
idx_prime_pedidos_codigo_original        -- Busca por código
idx_prime_pedidos_cliente_id             -- Busca por cliente
idx_prime_pedidos_codigo_cliente_original -- Busca por código do cliente
idx_prime_pedidos_data_aprovacao         -- Ordenação por data de aprovação
idx_prime_pedidos_data_entrega           -- Ordenação por data de entrega
idx_prime_pedidos_status_aprovacao       -- Filtro por status
idx_prime_pedidos_status_geral           -- Filtro por status geral
idx_prime_pedidos_valor_total            -- Ordenação por valor
```

---

### 3.4 Tabela: `prime_tipos_processo`

**Finalidade:** Cadastro dos tipos de processos de produção (pesagem, manipulação, conferência, etc).

#### Estrutura Completa

| Coluna | Tipo | Obrigatório | Descrição | Origem Firebird |
|--------|------|-------------|-----------|-----------------|
| `id` | BIGSERIAL | ✅ PK | ID sequencial interno | (gerado) |
| `codigo_tipo_original` | INTEGER | ✅ UNIQUE | Código do tipo no Prime | `FORMAFARMACEUTICA_PROCESSO_TIPO.CODIGO` |
| `nome_processo` | VARCHAR(100) | ✅ | Nome do processo | `FORMAFARMACEUTICA_PROCESSO_TIPO.NOMETIPO` |
| `nome_ficha` | VARCHAR(100) | ❌ | Nome na ficha | `FORMAFARMACEUTICA_PROCESSO_TIPO.NOMEFICHA` |
| `tipo_producao` | INTEGER | ❌ | Tipo (1=Prod, 3=Conf, 4=Logística) | `FORMAFARMACEUTICA_PROCESSO_TIPO.TIPO_PRODUCAO` |
| `sequencia` | INTEGER | ✅ | Ordem de execução | `FORMAFARMACEUTICA_PROCESSO_TIPO.SEQUENCIA` |
| `ativo` | BOOLEAN | ✅ | Processo ativo? | `FORMAFARMACEUTICA_PROCESSO_TIPO.ATIVO` |
| **Configurações** | | | | |
| `processo_opcional` | BOOLEAN | ✅ | Opcional? | `FORMAFARMACEUTICA_PROCESSO_TIPO.PROCESSO_OPCIONAL` |
| `pagar_comissao` | BOOLEAN | ✅ | Paga comissão? | `FORMAFARMACEUTICA_PROCESSO_TIPO.PAGARCOMISSAO` |
| `registrar_baixa` | BOOLEAN | ✅ | Registra baixa? | `FORMAFARMACEUTICA_PROCESSO_TIPO.REGISTRAR_BAIXA` |
| `bloquear_calculo` | BOOLEAN | ✅ | Bloqueia cálculo? | `FORMAFARMACEUTICA_PROCESSO_TIPO.BLOQUEAR_CALCULO` |
| `liberar_entrega` | BOOLEAN | ✅ | Libera entrega? | `FORMAFARMACEUTICA_PROCESSO_TIPO.LIBERAR_ENTREGA` |
| `bloquear_receita` | BOOLEAN | ✅ | Bloqueia receita? | `FORMAFARMACEUTICA_PROCESSO_TIPO.BLOQUEAR_RECEITA` |
| `observacao` | TEXT | ❌ | Observações | `FORMAFARMACEUTICA_PROCESSO_TIPO.OBSERVACAO` |
| `created_at` | TIMESTAMP | ✅ | Data de criação | (auto) |
| `updated_at` | TIMESTAMP | ✅ | Data de atualização | (auto - trigger) |

#### Exemplos de Tipos de Processo

```
1 - CONF. INICIAL       (sequencia: 1, tipo: 3 - Conferência)
2 - PESAGEM             (sequencia: 2, tipo: 1 - Produção)
3 - HOMOGENEIZAÇÃO      (sequencia: 3, tipo: 1 - Produção)
4 - MANIPULAÇÃO         (sequencia: 4, tipo: 1 - Produção)
5 - ENVASE              (sequencia: 5, tipo: 1 - Produção)
6 - CONF. FINAL         (sequencia: 6, tipo: 3 - Conferência)
7 - ROTULAGEM           (sequencia: 7, tipo: 4 - Logística)
8 - ENTREGA             (sequencia: 8, tipo: 4 - Logística)
```

---

### 3.5 Tabela: `prime_rastreabilidade`

**Finalidade:** Rastreamento completo de todos os processos de produção executados em cada pedido.

#### Estrutura Completa

| Coluna | Tipo | Obrigatório | Descrição | Origem Firebird |
|--------|------|-------------|-----------|-----------------|
| `id` | BIGSERIAL | ✅ PK | ID sequencial interno | (gerado) |
| `codigo_processo_original` | INTEGER | ✅ UNIQUE | Código do processo no Prime | `PROCESSO_MANIPULACAO.CODIGO` |
| `pedido_id` | BIGINT | ✅ FK | Referência ao pedido | (relacionamento) |
| `codigo_orcamento_original` | INTEGER | ✅ | Código do orçamento (desnormalizado) | `PROCESSO_MANIPULACAO.CODIGO_MOV` |
| `tipo_processo_id` | BIGINT | ✅ FK | Referência ao tipo de processo | (relacionamento) |
| `codigo_tipo_original` | INTEGER | ✅ | Código do tipo (desnormalizado) | `PROCESSO_MANIPULACAO.CODIGO_PROCESSO_TIPO` |
| `tipo_movimento` | INTEGER | ✅ | Tipo (1=Orçamento) | `PROCESSO_MANIPULACAO.TIPO_MOV` |
| `codigo_funcionario` | INTEGER | ❌ | Funcionário responsável | `PROCESSO_MANIPULACAO.CODIGO_FUNCIONARIO` |
| `nome_funcionario` | VARCHAR(255) | ❌ | Nome do funcionário | (via JOIN com FUNCIONARIO) |
| `data_processo` | DATE | ✅ | Data de execução | `PROCESSO_MANIPULACAO.DATA_PROCESSO` |
| `hora_processo` | TIME | ✅ | Hora de execução | `PROCESSO_MANIPULACAO.HORA_PROCESSO` |
| `sequencia` | INTEGER | ✅ | Sequência no pedido | `PROCESSO_MANIPULACAO.SEQUENCIA` |
| `status_processo` | VARCHAR(50) | ❌ | Status atual | (calculado) |
| `data_inicio` | TIMESTAMP | ❌ | Data/hora de início | (calculado) |
| `data_fim` | TIMESTAMP | ❌ | Data/hora de término | (calculado) |
| `pagar_comissao` | BOOLEAN | ✅ | Paga comissão? | `PROCESSO_MANIPULACAO.PAGARCOMISSAO` |
| `created_at` | TIMESTAMP | ✅ | Data de criação | (auto) |
| `updated_at` | TIMESTAMP | ✅ | Data de atualização | (auto - trigger) |

#### Status de Processo

- `PENDENTE` - Processo aguardando execução
- `EM_ANDAMENTO` - Processo sendo executado
- `CONCLUIDO` - Processo finalizado

---

### 3.6 Tabela: `prime_formulas`

**Finalidade:** Detalhes das fórmulas/produtos de cada pedido.

#### Estrutura Completa

| Coluna | Tipo | Obrigatório | Descrição | Origem Firebird |
|--------|------|-------------|-----------|-----------------|
| `id` | BIGSERIAL | ✅ PK | ID sequencial interno | (gerado) |
| `pedido_id` | BIGINT | ✅ FK | Referência ao pedido | (relacionamento) |
| `codigo_orcamento_original` | INTEGER | ✅ | Código do orçamento (desnormalizado) | `ATENDIMENTO_A2.CODIGO_ATEND_A1` |
| `numero_formula` | INTEGER | ✅ | Número da fórmula | `ATENDIMENTO_A2.NUMEROFORMULA` |
| `descricao` | TEXT | ❌ | Descrição completa | `ATENDIMENTO_A2.DESCRICAO` |
| `posologia` | TEXT | ❌ | Posologia/modo de usar | `ATENDIMENTO_A2.POSOLOGIA` |
| `valor_formula` | DECIMAL(15,2) | ✅ | Valor da fórmula | `ATENDIMENTO_A2.VALOR` |
| `data_inicio_producao` | TIMESTAMP | ❌ | Início produção da fórmula | (calculado) |
| `data_fim_producao` | TIMESTAMP | ❌ | Fim produção da fórmula | (calculado) |
| `created_at` | TIMESTAMP | ✅ | Data de criação | (auto) |
| `updated_at` | TIMESTAMP | ✅ | Data de atualização | (auto - trigger) |

#### Exemplo de Fórmula

```
numero_formula: 1
descricao: "60 CÁPSULAS - Hidroxicloroquina 150mg, Diacereína 50mg, Colágeno Tipo II 40mg"
posologia: "Tomar 1 cápsula 2 vezes ao dia"
valor_formula: 269.04
```

---

## 4. Dados Exportados do Firebird

### 4.1 Tabelas de Origem no Firebird

#### CLIENTE
- **Finalidade:** Cadastro de clientes
- **Dados extraídos:** Nome, CPF, endereço, telefone, data de nascimento, sexo, email
- **Filtro:** `ATIVO = -1` (apenas clientes ativos)

#### ATENDIMENTO_A1
- **Finalidade:** Cabeçalho dos orçamentos/pedidos
- **Dados extraídos:** Código, cliente, datas (criação, aprovação, entrega), valores, status
- **Filtro:** `AVIADA_DT IS NOT NULL` (apenas orçamentos aprovados)

#### ATENDIMENTO_A2
- **Finalidade:** Itens (fórmulas) dos orçamentos
- **Dados extraídos:** Número da fórmula, descrição, posologia, valor
- **Relacionamento:** `CODIGO_ATEND_A1` → `ATENDIMENTO_A1.CODIGO`

#### FORMAFARMACEUTICA_PROCESSO_TIPO
- **Finalidade:** Tipos de processos de produção
- **Dados extraídos:** Nome, sequência, configurações
- **Filtro:** Todos os registros

#### PROCESSO_MANIPULACAO
- **Finalidade:** Rastreabilidade de produção
- **Dados extraídos:** Processo, data/hora, funcionário, sequência
- **Relacionamento:** `CODIGO_MOV` → `ATENDIMENTO_A1.CODIGO`

#### CIDADEESTADO
- **Finalidade:** Cadastro de cidades e estados
- **Dados extraídos:** Nome da cidade, UF
- **Relacionamento:** `CLIENTE.CODIGO_CIDADEESTADO` → `CIDADEESTADO.CODIGO`

### 4.2 Mapeamento de Campos

#### De CLIENTE para prime_clientes

```
CLIENTE.CODIGO                    → codigo_cliente_original
CLIENTE.NOMECLIENTE              → nome
CLIENTE.CPF_CNPJ                 → cpf_cnpj
CLIENTE.DIANASCIMENTO/MES/ANO    → data_nascimento
CLIENTE.SEXO                     → sexo
CLIENTE.EMAIL1                   → email
CLIENTE.TELEFONE1 + PREFIXO      → telefone
CLIENTE.ENDERECO                 → endereco_logradouro
CLIENTE.NUMERO                   → endereco_numero
CLIENTE.CEP                      → endereco_cep
CIDADEESTADO.NOMECIDADE          → endereco_cidade
CIDADEESTADO.UF                  → endereco_estado
CLIENTE.ATIVO                    → ativo
```

#### De ATENDIMENTO_A1 para prime_pedidos

```
ATENDIMENTO_A1.CODIGO            → codigo_orcamento_original
ATENDIMENTO_A1.CODIGO_CLIENTE    → codigo_cliente_original
ATENDIMENTO_A1.DATA_CRIACAO      → data_criacao
ATENDIMENTO_A1.AVIADA_DT         → data_aprovacao
ATENDIMENTO_A1.ENTREGUE_DT       → data_entrega
ATENDIMENTO_A1.CANCELADO_DT      → data_cancelamento
ATENDIMENTO_A1.VALORVENDA        → valor_total
ATENDIMENTO_A1.STATUS_MOV        → status_mov
ATENDIMENTO_A1.OBSERVACAO        → observacoes
```

#### Cálculo de Status

```python
# status_aprovacao
if AVIADA_DT IS NOT NULL:
    status_aprovacao = "APROVADO"
else:
    status_aprovacao = "NAO_APROVADO"

# status_entrega
if ENTREGUE_DT IS NOT NULL:
    status_entrega = "ENTREGUE"
else:
    status_entrega = "NAO_ENTREGUE"

# status_geral
if STATUS_MOV == -1:
    status_geral = "CANCELADO"
elif AVIADA_DT AND ENTREGUE_DT:
    status_geral = "ENTREGUE"
elif AVIADA_DT:
    status_geral = "APROVADO"
else:
    status_geral = "PENDENTE"
```

---

## 5. Estrutura de Código Python

### 5.1 Arquivo: `exportar_firebird_supabase_final.py`

**Localização:** Raiz do projeto  
**Linguagem:** Python 3.11+  
**Linhas de código:** ~579 linhas

#### 5.1.1 Configurações

```python
# Supabase
SUPABASE_URL = "https://agdffspstbxeqhqtltvb.supabase.co"
SUPABASE_SERVICE_KEY = "eyJh..."  # Service Role Key
SCHEMA = "api"

# Firebird
FIREBIRD_CONFIG = {
    'host': '72.60.13.173',
    'port': 3050,
    'database': 'psbd.FDB',
    'user': 'SYSDBA',
    'password': 'd94b434ab7e328590bb8',
    'charset': 'WIN1252'
}
```

#### 5.1.2 Classe Principal: `FirebirdSupabaseExporter`

##### Atributos

```python
self.firebird_conn: fdb.Connection     # Conexão com Firebird
self.supabase: Client                  # Cliente Supabase
self.stats: Dict[str, int]             # Estatísticas da exportação
```

##### Métodos de Conexão

**`conectar_firebird()`**
- Estabelece conexão com banco Firebird
- Retorna `True` em sucesso, `False` em erro
- Usa configurações de `FIREBIRD_CONFIG`

**`conectar_supabase()`**
- Estabelece conexão com Supabase via SDK
- Configura headers para usar schema `api`
- Retorna `True` em sucesso, `False` em erro

**`testar_conexoes()`**
- Testa ambas as conexões
- Executa query de teste no Firebird
- Executa query de teste no Supabase
- Retorna `True` se ambos OK

##### Métodos Utilitários

**`converter_data(data_str: str) → str`**
- Converte data para formato ISO (YYYY-MM-DD)
- Trata `None` e diferentes formatos
- Retorna string ISO ou `None`

**`converter_timestamp(data_str: str) → str`**
- Converte timestamp para formato ISO com hora
- Formato: YYYY-MM-DDTHH:MM:SS
- Retorna string ISO ou `None`

**`converter_decimal(valor) → float`**
- Converte Decimal para float
- Trata `None` e erros de conversão
- Usado para valores monetários

**`limpar_string(texto: str) → str`**
- Remove espaços em branco extras
- Retorna `None` se string vazia
- Evita strings vazias no banco

**`inserir_com_retry(tabela, dados, max_tentativas=3)`**
- Insere dados com retry automático
- Usa `upsert` para evitar duplicatas
- Backoff exponencial: 1s, 2s, 4s
- Lança exceção após max_tentativas

##### Métodos de Exportação

**`exportar_tipos_processo()`**

```python
# Query SQL executada
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

- Exporta todos os tipos de processo
- Sem paginação (poucos registros)
- Insere em `prime_tipos_processo`
- Atualiza `stats['tipos_processo']`

**`exportar_clientes(limite=1000)`**

```python
# Query SQL executada (com paginação)
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
ORDER BY C.CODIGO
ROWS {limite} TO {offset + limite}
```

- Paginação de 1000 em 1000 registros
- Apenas clientes ativos (`ATIVO = -1`)
- Monta data de nascimento de 3 campos
- Concatena telefone com DDD
- Insere em `prime_clientes`
- Loop até não haver mais registros

**`exportar_pedidos(limite=1000)`**

```python
# Query SQL executada (com paginação)
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
ORDER BY A1.CODIGO
ROWS {limite} TO {offset + limite}
```

- Paginação de 1000 em 1000 registros
- Apenas orçamentos aprovados (`AVIADA_DT IS NOT NULL`)
- Calcula status automático
- Insere em `prime_pedidos`
- Requer que clientes já estejam exportados

**`exportar_rastreabilidade(limite=1000)`**

```python
# Query SQL executada (com paginação)
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
ROWS {limite} TO {offset + limite}
```

- Paginação de 1000 em 1000 registros
- Todos os processos de manipulação
- Ordenado por orçamento e sequência
- Insere em `prime_rastreabilidade`
- Status padrão: `CONCLUIDO`

**`exportar_formulas(limite=1000)`**

```python
# Query SQL executada (com paginação)
SELECT 
    A2.CODIGO_ATEND_A1,
    A2.NUMEROFORMULA,
    A2.DESCRICAO,
    A2.POSOLOGIA,
    A2.VALOR
FROM ATENDIMENTO_A2 A2
INNER JOIN ATENDIMENTO_A1 A1 ON A2.CODIGO_ATEND_A1 = A1.CODIGO
WHERE A1.AVIADA_DT IS NOT NULL
ORDER BY A2.CODIGO_ATEND_A1, A2.NUMEROFORMULA
ROWS {limite} TO {offset + limite}
```

- Paginação de 1000 em 1000 registros
- Apenas fórmulas de orçamentos aprovados
- JOIN com ATENDIMENTO_A1 para filtro
- Insere em `prime_formulas`

**`executar_exportacao_completa()`**

```python
# Fluxo de execução
1. conectar_firebird()
2. conectar_supabase()
3. testar_conexoes()
4. exportar_tipos_processo()    # 1º - não tem dependências
5. exportar_clientes()           # 2º - pedidos dependem de clientes
6. exportar_pedidos()            # 3º - rastreabilidade depende de pedidos
7. exportar_rastreabilidade()    # 4º - requer tipos e pedidos
8. exportar_formulas()           # 5º - requer pedidos
9. imprimir_estatisticas()
10. fechar_conexoes()
```

- Ordem respeitando foreign keys
- Tratamento de erros em cada etapa
- Log detalhado de progresso
- Retorna `True` em sucesso

#### 5.1.3 Função Principal

```python
def main():
    exporter = FirebirdSupabaseExporter()
    sucesso = exporter.executar_exportacao_completa()
    sys.exit(0 if sucesso else 1)
```

### 5.2 Arquivo: `config_supabase.py`

**Finalidade:** Centralizar configurações do projeto

```python
# Supabase
SUPABASE_URL = "https://agdffspstbxeqhqtltvb.supabase.co"
SUPABASE_SERVICE_KEY = "eyJh..."
SUPABASE_SCHEMA = "api"

# Firebird
FIREBIRD_CONFIG = {
    'host': '72.60.13.173',
    'port': 3050,
    'database': 'psbd.FDB',
    'user': 'SYSDBA',
    'password': 'd94b434ab7e328590bb8',
    'charset': 'WIN1252'
}

# Configurações de Exportação
EXPORT_CONFIG = {
    'batch_size': 1000,
    'max_retries': 3,
    'retry_delay': 2,
    'log_level': 'INFO'
}
```

### 5.3 Dependências: `requirements_export_supabase.txt`

```
fdb>=2.0.0           # Driver Firebird para Python
supabase>=2.0.0      # Cliente Supabase para Python
python-dotenv>=1.0.0 # Gerenciamento de variáveis de ambiente
```

### 5.4 Execução

#### Modo Manual

```bash
# Windows
cd "C:\Users\User\Documents\Banco de Dados Prime"
python exportar_firebird_supabase_final.py

# Linux/Mac
cd /caminho/do/projeto
python3 exportar_firebird_supabase_final.py
```

#### Modo Agendado (Windows)

```batch
# agendar_exportacao.bat
schtasks /create ^
  /tn "Exportacao Prime Supabase" ^
  /tr "python exportar_firebird_supabase_final.py" ^
  /sc daily ^
  /st 23:00 ^
  /f
```

---

## 6. Views e Consultas Analíticas

### 6.1 View: `vw_prime_clientes_rfv`

**Finalidade:** Análise RFV completa de clientes com scores calculados

#### Estrutura

```sql
CREATE OR REPLACE VIEW api.vw_prime_clientes_rfv AS
SELECT 
    c.id,
    c.codigo_cliente_original,
    c.nome,
    c.cpf_cnpj,
    c.email,
    c.telefone,
    c.endereco_cidade,
    c.endereco_estado,
    
    -- Score de Recência (R): 0-5
    CASE 
        WHEN c.ultima_compra IS NULL THEN 0
        WHEN c.ultima_compra >= CURRENT_DATE - INTERVAL '30 days' THEN 5
        WHEN c.ultima_compra >= CURRENT_DATE - INTERVAL '60 days' THEN 4
        WHEN c.ultima_compra >= CURRENT_DATE - INTERVAL '90 days' THEN 3
        WHEN c.ultima_compra >= CURRENT_DATE - INTERVAL '180 days' THEN 2
        ELSE 1
    END as recencia_score,
    
    -- Score de Frequência (F): 0-5
    CASE 
        WHEN c.total_orcamentos_aprovados = 0 THEN 0
        WHEN c.total_orcamentos_aprovados = 1 THEN 1
        WHEN c.total_orcamentos_aprovados <= 3 THEN 2
        WHEN c.total_orcamentos_aprovados <= 5 THEN 3
        WHEN c.total_orcamentos_aprovados <= 10 THEN 4
        ELSE 5
    END as frequencia_score,
    
    -- Score de Valor (V): 0-5
    CASE 
        WHEN c.valor_total_aprovados = 0 THEN 0
        WHEN c.valor_total_aprovados <= 100 THEN 1
        WHEN c.valor_total_aprovados <= 500 THEN 2
        WHEN c.valor_total_aprovados <= 1000 THEN 3
        WHEN c.valor_total_aprovados <= 2500 THEN 4
        ELSE 5
    END as valor_score,
    
    -- Score RFV Combinado (ponderado)
    (CASE WHEN c.ultima_compra IS NULL THEN 0
          WHEN c.ultima_compra >= CURRENT_DATE - INTERVAL '30 days' THEN 5
          WHEN c.ultima_compra >= CURRENT_DATE - INTERVAL '60 days' THEN 4
          WHEN c.ultima_compra >= CURRENT_DATE - INTERVAL '90 days' THEN 3
          WHEN c.ultima_compra >= CURRENT_DATE - INTERVAL '180 days' THEN 2
          ELSE 1
    END * 100) + 
    (CASE WHEN c.total_orcamentos_aprovados = 0 THEN 0
          WHEN c.total_orcamentos_aprovados = 1 THEN 1
          WHEN c.total_orcamentos_aprovados <= 3 THEN 2
          WHEN c.total_orcamentos_aprovados <= 5 THEN 3
          WHEN c.total_orcamentos_aprovados <= 10 THEN 4
          ELSE 5
    END * 10) + 
    (CASE WHEN c.valor_total_aprovados = 0 THEN 0
          WHEN c.valor_total_aprovados <= 100 THEN 1
          WHEN c.valor_total_aprovados <= 500 THEN 2
          WHEN c.valor_total_aprovados <= 1000 THEN 3
          WHEN c.valor_total_aprovados <= 2500 THEN 4
          ELSE 5
    END) as score_rfv_calculado,
    
    -- Dados originais
    c.total_orcamentos,
    c.total_orcamentos_aprovados,
    c.total_orcamentos_entregues,
    c.valor_total_orcamentos,
    c.valor_total_aprovados,
    c.valor_total_entregues,
    c.valor_medio_orcamento,
    c.valor_medio_aprovado,
    c.valor_medio_entregue,
    c.primeira_compra,
    c.ultima_compra,
    c.ativo
FROM api.prime_clientes c;
```

#### Exemplos de Uso

```sql
-- Top 10 clientes por score RFV
SELECT nome, score_rfv_calculado, valor_total_aprovados, ultima_compra
FROM api.vw_prime_clientes_rfv
ORDER BY score_rfv_calculado DESC
LIMIT 10;

-- Clientes "Campeões" (R≥4, F≥4, V≥4)
SELECT nome, recencia_score, frequencia_score, valor_score
FROM api.vw_prime_clientes_rfv
WHERE recencia_score >= 4 
  AND frequencia_score >= 4 
  AND valor_score >= 4;

-- Clientes em risco de churn (R≤2, F≥3)
SELECT nome, ultima_compra, total_orcamentos_aprovados
FROM api.vw_prime_clientes_rfv
WHERE recencia_score <= 2 
  AND frequencia_score >= 3;
```

### 6.2 View: `vw_prime_rastreabilidade_completa`

**Finalidade:** Rastreamento detalhado de processos por pedido

```sql
CREATE OR REPLACE VIEW api.vw_prime_rastreabilidade_completa AS
SELECT 
    p.id as pedido_id,
    p.codigo_orcamento_original,
    c.nome as nome_cliente,
    p.status_aprovacao,
    p.status_geral,
    
    -- Dados da rastreabilidade
    r.id as rastreabilidade_id,
    r.sequencia,
    tp.nome_processo,
    r.nome_funcionario,
    r.data_processo,
    r.hora_processo,
    r.status_processo,
    
    -- Análise temporal
    r.data_inicio,
    r.data_fim,
    CASE 
        WHEN r.data_inicio IS NOT NULL AND r.data_fim IS NOT NULL 
        THEN EXTRACT(EPOCH FROM (r.data_fim - r.data_inicio))/3600 
        ELSE NULL 
    END as horas_processo
    
FROM api.prime_pedidos p
INNER JOIN api.prime_clientes c ON p.cliente_id = c.id
LEFT JOIN api.prime_rastreabilidade r ON p.id = r.pedido_id
LEFT JOIN api.prime_tipos_processo tp ON r.tipo_processo_id = tp.id
ORDER BY p.codigo_orcamento_original, r.sequencia;
```

#### Exemplos de Uso

```sql
-- Rastreamento completo de um pedido específico
SELECT sequencia, nome_processo, nome_funcionario, 
       data_processo, hora_processo, status_processo
FROM api.vw_prime_rastreabilidade_completa
WHERE codigo_orcamento_original = 251002809
ORDER BY sequencia;

-- Tempo médio por tipo de processo
SELECT nome_processo, 
       AVG(horas_processo) as media_horas,
       COUNT(*) as total_processos
FROM api.vw_prime_rastreabilidade_completa
WHERE horas_processo IS NOT NULL
GROUP BY nome_processo
ORDER BY media_horas DESC;
```

### 6.3 View: `vw_prime_pedidos_status`

**Finalidade:** Análise de status e contagem de processos por pedido

```sql
CREATE OR REPLACE VIEW api.vw_prime_pedidos_status AS
SELECT 
    p.id,
    p.codigo_orcamento_original,
    p.cliente_id,
    c.nome as nome_cliente,
    p.status_aprovacao,
    p.status_entrega,
    p.status_geral,
    p.data_criacao,
    p.data_aprovacao,
    p.data_entrega,
    p.data_inicio_producao,
    p.data_fim_producao,
    p.data_prevista_entrega,
    p.laboratorio_iniciado,
    p.laboratorio_finalizado,
    p.transporte_iniciado,
    p.transporte_finalizado,
    p.valor_total,
    p.dias_para_aprovacao,
    p.dias_para_entrega,
    p.dias_total_processo,
    p.dias_producao,
    p.dias_transporte,
    
    -- Contagem de processos
    COUNT(r.id) as total_processos,
    COUNT(CASE WHEN r.status_processo = 'CONCLUIDO' THEN 1 END) as processos_concluidos,
    COUNT(CASE WHEN r.status_processo = 'EM_ANDAMENTO' THEN 1 END) as processos_em_andamento,
    COUNT(CASE WHEN r.status_processo = 'PENDENTE' THEN 1 END) as processos_pendentes
    
FROM api.prime_pedidos p
INNER JOIN api.prime_clientes c ON p.cliente_id = c.id
LEFT JOIN api.prime_rastreabilidade r ON p.id = r.pedido_id
GROUP BY p.id, p.codigo_orcamento_original, p.cliente_id, c.nome, 
         p.status_aprovacao, p.status_entrega, p.status_geral,
         p.data_criacao, p.data_aprovacao, p.data_entrega, p.data_inicio_producao,
         p.data_fim_producao, p.data_prevista_entrega, p.laboratorio_iniciado,
         p.laboratorio_finalizado, p.transporte_iniciado, p.transporte_finalizado,
         p.valor_total, p.dias_para_aprovacao, p.dias_para_entrega, p.dias_total_processo,
         p.dias_producao, p.dias_transporte;
```

#### Exemplos de Uso

```sql
-- Pedidos com processos pendentes
SELECT codigo_orcamento_original, nome_cliente,
       total_processos, processos_concluidos, processos_pendentes
FROM api.vw_prime_pedidos_status
WHERE processos_pendentes > 0
ORDER BY processos_pendentes DESC;

-- Tempo médio de produção por status
SELECT status_geral,
       AVG(dias_producao) as media_dias_producao,
       AVG(dias_transporte) as media_dias_transporte,
       COUNT(*) as total_pedidos
FROM api.vw_prime_pedidos_status
GROUP BY status_geral;
```

---

## 7. Permissões e Segurança

### 7.1 Row Level Security (RLS)

Todas as tabelas têm RLS habilitado:

```sql
ALTER TABLE api.prime_clientes ENABLE ROW LEVEL SECURITY;
ALTER TABLE api.prime_pedidos ENABLE ROW LEVEL SECURITY;
ALTER TABLE api.prime_tipos_processo ENABLE ROW LEVEL SECURITY;
ALTER TABLE api.prime_rastreabilidade ENABLE ROW LEVEL SECURITY;
ALTER TABLE api.prime_formulas ENABLE ROW LEVEL SECURITY;
```

### 7.2 Políticas de Acesso

#### Leitura Pública (anon)

```sql
CREATE POLICY "Allow select for authenticated users (prime_clientes)" 
ON api.prime_clientes
FOR SELECT
USING (true);  -- Permite leitura para todos
```

#### Escrita Autenticada (authenticated)

```sql
CREATE POLICY "Allow insert for authenticated users (prime_clientes)" 
ON api.prime_clientes
FOR INSERT
WITH CHECK (true);  -- Permite inserção para usuários autenticados

CREATE POLICY "Allow update for authenticated users (prime_clientes)" 
ON api.prime_clientes
FOR UPDATE
USING (true)
WITH CHECK (true);  -- Permite atualização
```

### 7.3 GRANTs de Permissão

#### Role: anon (usuário anônimo)

```sql
GRANT SELECT ON api.prime_clientes TO anon;
GRANT SELECT ON api.prime_pedidos TO anon;
GRANT SELECT ON api.prime_tipos_processo TO anon;
GRANT SELECT ON api.prime_rastreabilidade TO anon;
GRANT SELECT ON api.prime_formulas TO anon;
```

#### Role: authenticated (usuário logado)

```sql
GRANT SELECT, INSERT, UPDATE, DELETE ON api.prime_clientes TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON api.prime_pedidos TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON api.prime_tipos_processo TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON api.prime_rastreabilidade TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON api.prime_formulas TO authenticated;
```

#### Role: service_role (chave do servidor)

```sql
GRANT ALL ON api.prime_clientes TO service_role;
GRANT ALL ON api.prime_pedidos TO service_role;
GRANT ALL ON api.prime_tipos_processo TO service_role;
GRANT ALL ON api.prime_rastreabilidade TO service_role;
GRANT ALL ON api.prime_formulas TO service_role;
```

**⚠️ Importante:** O script Python usa a chave `service_role` para bypass de RLS e permissões totais.

### 7.4 Triggers de Auditoria

#### Trigger: updated_at

Atualiza automaticamente o campo `updated_at` em todas as tabelas:

```sql
CREATE OR REPLACE FUNCTION api.update_prime_clientes_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_prime_clientes_updated_at
    BEFORE UPDATE ON api.prime_clientes
    FOR EACH ROW
    EXECUTE FUNCTION api.update_prime_clientes_updated_at();
```

---

## 8. Fluxo de Exportação

### 8.1 Diagrama de Sequência

```
┌─────────┐                ┌──────────┐              ┌──────────┐
│ Python  │                │ Firebird │              │ Supabase │
│ Script  │                │   ERP    │              │   API    │
└────┬────┘                └────┬─────┘              └────┬─────┘
     │                          │                         │
     │ 1. Conectar              │                         │
     │ ────────────────────────►│                         │
     │                          │                         │
     │ 2. OK                    │                         │
     │ ◄────────────────────────│                         │
     │                          │                         │
     │ 3. Conectar              │                         │
     │ ──────────────────────────────────────────────────►│
     │                          │                         │
     │ 4. OK                    │                         │
     │ ◄──────────────────────────────────────────────────│
     │                          │                         │
     │ 5. SELECT tipos_processo │                         │
     │ ────────────────────────►│                         │
     │                          │                         │
     │ 6. [Dados]               │                         │
     │ ◄────────────────────────│                         │
     │                          │                         │
     │ 7. POST /prime_tipos_processo                      │
     │ ──────────────────────────────────────────────────►│
     │                          │                         │
     │ 8. OK [ids]              │                         │
     │ ◄──────────────────────────────────────────────────│
     │                          │                         │
     │ 9. SELECT clientes (pág 1)                         │
     │ ────────────────────────►│                         │
     │                          │                         │
     │ 10. [1000 registros]     │                         │
     │ ◄────────────────────────│                         │
     │                          │                         │
     │ 11. POST /prime_clientes (batch)                   │
     │ ──────────────────────────────────────────────────►│
     │                          │                         │
     │ 12. OK [ids]             │                         │
     │ ◄──────────────────────────────────────────────────│
     │                          │                         │
     │ [... Loop paginação clientes ...]                  │
     │                          │                         │
     │ [... Pedidos ...]        │                         │
     │ [... Rastreabilidade ...] │                        │
     │ [... Fórmulas ...]       │                         │
     │                          │                         │
     │ 13. Fechar               │                         │
     │ ────────────────────────►│                         │
     │                          │                         │
     │ 14. Log de sucesso       │                         │
     └──────────────────────────┘                         │
```

### 8.2 Etapas Detalhadas

#### Etapa 1: Conexão Firebird

```python
self.firebird_conn = fdb.connect(
    host='72.60.13.173',
    port=3050,
    database='psbd.FDB',
    user='SYSDBA',
    password='...',
    charset='WIN1252'
)
```

**Charset:** `WIN1252` é usado porque o Firebird no Windows usa essa codificação por padrão.

#### Etapa 2: Conexão Supabase

```python
self.supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY, {
    'auth': {
        'autoRefreshToken': False,
        'persistSession': False
    },
    'db': {
        'schema': SCHEMA  # 'api'
    },
    'global': {
        'headers': {
            'Accept-Profile': SCHEMA,
            'Content-Profile': SCHEMA
        }
    }
})
```

**Headers:** `Accept-Profile` e `Content-Profile` são necessários para usar schema `api` em vez do `public`.

#### Etapa 3: Exportação de Tipos de Processo

```python
tipos = []
for row in cursor.fetchall():
    tipo = {
        'codigo_tipo_original': row[0],
        'nome_processo': self.limpar_string(row[1]),
        'sequencia': row[4],
        'ativo': row[5] == -1,  # Firebird usa -1 para TRUE
        ...
    }
    tipos.append(tipo)

# Upsert em batch
self.supabase.table('prime_tipos_processo').upsert(tipos).execute()
```

**Upsert:** Insere novos registros ou atualiza existentes baseado em `codigo_tipo_original` (unique).

#### Etapa 4: Exportação de Clientes (com paginação)

```python
offset = 0
limite = 1000

while True:
    # Query com ROWS (paginação Firebird)
    cursor.execute(f"""
        SELECT ... FROM CLIENTE
        ORDER BY CODIGO
        ROWS {limite} TO {offset + limite}
    """)
    
    rows = cursor.fetchall()
    if not rows:
        break  # Fim da paginação
    
    clientes = [processar_row(row) for row in rows]
    self.supabase.table('prime_clientes').upsert(clientes).execute()
    
    offset += limite
```

**Paginação Firebird:** Usa sintaxe `ROWS x TO y` (diferente de LIMIT/OFFSET do PostgreSQL).

#### Etapa 5: Relacionamentos (Foreign Keys)

```python
# Primeiro: exportar clientes
exportar_clientes()

# Depois: exportar pedidos (requer clientes)
pedido = {
    'codigo_orcamento_original': 251002809,
    'codigo_cliente_original': 12345,  # FK para prime_clientes
    ...
}

# Supabase resolve automaticamente o relacionamento
# codigo_cliente_original → busca prime_clientes.codigo_cliente_original
#                        → pega o id interno
#                        → insere em prime_pedidos.cliente_id
```

**Importante:** Os códigos `original` são usados para relacionamento, mas o Supabase cria seus próprios IDs sequenciais.

#### Etapa 6: Retry com Backoff

```python
def inserir_com_retry(self, tabela, dados, max_tentativas=3):
    for tentativa in range(max_tentativas):
        try:
            return self.supabase.table(tabela).upsert(dados).execute()
        except Exception as e:
            if tentativa < max_tentativas - 1:
                time.sleep(2 ** tentativa)  # 1s, 2s, 4s
            else:
                raise e
```

**Backoff Exponencial:** Aguarda progressivamente mais tempo entre tentativas para evitar sobrecarga.

### 8.3 Tratamento de Erros

```python
try:
    self.exportar_clientes()
except Exception as e:
    logger.error(f"❌ Erro ao exportar clientes: {e}")
    self.stats['erros'] += 1
    raise  # Re-lança para parar a exportação
```

**Estratégia:** Qualquer erro crítico para a exportação completa para manter integridade dos dados.

### 8.4 Logs Gerados

```
2025-10-21 09:30:00 - INFO - 🚀 Iniciando exportação Firebird → Supabase...
2025-10-21 09:30:01 - INFO - 🔌 Conectando ao Firebird...
2025-10-21 09:30:02 - INFO - ✅ Conectado ao Firebird com sucesso!
2025-10-21 09:30:03 - INFO - 🔌 Conectando ao Supabase...
2025-10-21 09:30:04 - INFO - ✅ Conectado ao Supabase com sucesso!
2025-10-21 09:30:05 - INFO - 🧪 Testando conexões...
2025-10-21 09:30:06 - INFO - ✅ Firebird: 30245 clientes encontrados
2025-10-21 09:30:07 - INFO - ✅ Supabase: Conexão testada com sucesso
2025-10-21 09:30:08 - INFO - 🔄 Exportando tipos de processo...
2025-10-21 09:30:10 - INFO - ✅ 25 tipos de processo exportados!
2025-10-21 09:30:11 - INFO - 🔄 Exportando clientes...
2025-10-21 09:30:25 - INFO - ✅ 1000 clientes exportados (total: 1000)
2025-10-21 09:30:38 - INFO - ✅ 1000 clientes exportados (total: 2000)
...
2025-10-21 09:45:12 - INFO - ✅ 245 clientes exportados (total: 30245)
2025-10-21 09:45:13 - INFO - 🔄 Exportando pedidos...
...
2025-10-21 10:30:00 - INFO - 🎉 Exportação concluída com sucesso!
2025-10-21 10:30:00 - INFO - 📊 Estatísticas:
2025-10-21 10:30:00 - INFO -    tipos_processo: 25
2025-10-21 10:30:00 - INFO -    clientes: 30245
2025-10-21 10:30:00 - INFO -    pedidos: 85432
2025-10-21 10:30:00 - INFO -    rastreabilidade: 342156
2025-10-21 10:30:00 - INFO -    formulas: 125678
2025-10-21 10:30:00 - INFO - 🔌 Conexão Firebird fechada
```

---

## 9. Análise RFV Implementada

### 9.1 Conceito RFV

**RFV** = Recência + Frequência + Valor

Metodologia para segmentar clientes baseado em:
- **R (Recency)**: Quão recente foi a última compra?
- **F (Frequency)**: Com que frequência o cliente compra?
- **V (Value)**: Quanto o cliente gasta?

### 9.2 Cálculo dos Scores

#### Recência (peso 100)

| Última Compra | Score | Valor no Score RFV |
|---------------|-------|-------------------|
| < 30 dias | 5 | 500 |
| 30-60 dias | 4 | 400 |
| 60-90 dias | 3 | 300 |
| 90-180 dias | 2 | 200 |
| > 180 dias | 1 | 100 |
| Nunca comprou | 0 | 0 |

#### Frequência (peso 10)

| Total de Compras | Score | Valor no Score RFV |
|------------------|-------|-------------------|
| 10+ compras | 5 | 50 |
| 5-9 compras | 4 | 40 |
| 2-4 compras | 3 | 30 |
| 1 compra | 2 | 20 |
| 0 compras | 0 | 0 |

#### Valor (peso 1)

| Valor Total Gasto | Score | Valor no Score RFV |
|-------------------|-------|-------------------|
| > R$ 2.500 | 5 | 5 |
| R$ 1.000 - 2.500 | 4 | 4 |
| R$ 500 - 1.000 | 3 | 3 |
| R$ 100 - 500 | 2 | 2 |
| < R$ 100 | 1 | 1 |
| R$ 0 | 0 | 0 |

#### Score RFV Final

```
Score RFV = (R × 100) + (F × 10) + V
```

**Exemplo:**
- Recência: 5 (< 30 dias) → 500 pontos
- Frequência: 4 (7 compras) → 40 pontos
- Valor: 5 (R$ 3.200) → 5 pontos
- **Score RFV = 545**

**Intervalo:** 0 a 555

### 9.3 Segmentação de Clientes

```sql
SELECT 
    CASE 
        WHEN recencia_score >= 4 AND frequencia_score >= 4 AND valor_score >= 4 
        THEN 'Campeões'
        
        WHEN recencia_score >= 3 AND frequencia_score >= 3 AND valor_score >= 3 
        THEN 'Clientes Leais'
        
        WHEN recencia_score >= 4 AND frequencia_score <= 2 
        THEN 'Novos Clientes'
        
        WHEN recencia_score <= 2 AND frequencia_score >= 3 AND valor_score >= 3
        THEN 'Clientes VIP em Risco'
        
        WHEN recencia_score <= 2 AND frequencia_score >= 3 
        THEN 'Clientes em Risco'
        
        WHEN recencia_score <= 2 AND frequencia_score <= 2 
        THEN 'Clientes Dorminhocos'
        
        ELSE 'Outros'
    END as segmento,
    COUNT(*) as total_clientes,
    SUM(valor_total_aprovados) as receita_total
FROM api.vw_prime_clientes_rfv
GROUP BY segmento
ORDER BY receita_total DESC;
```

#### Descrição dos Segmentos

| Segmento | Características | Ação Recomendada |
|----------|----------------|------------------|
| **Campeões** | R≥4, F≥4, V≥4 | Recompensas VIP, programa de fidelidade |
| **Clientes Leais** | R≥3, F≥3, V≥3 | Upselling, cross-selling |
| **Novos Clientes** | R≥4, F≤2 | Onboarding, educação |
| **Clientes VIP em Risco** | R≤2, F≥3, V≥3 | Campanhas de reativação urgente |
| **Clientes em Risco** | R≤2, F≥3 | Pesquisa de satisfação, ofertas |
| **Clientes Dorminhocos** | R≤2, F≤2 | Campanhas de reconquista |

### 9.4 Consultas de Análise RFV

```sql
-- Top 20 Clientes Campeões
SELECT nome, email, telefone, score_rfv_calculado,
       total_orcamentos_aprovados, valor_total_aprovados,
       ultima_compra
FROM api.vw_prime_clientes_rfv
WHERE recencia_score >= 4 
  AND frequencia_score >= 4 
  AND valor_score >= 4
ORDER BY score_rfv_calculado DESC
LIMIT 20;

-- Clientes VIP em Risco (precisam de atenção)
SELECT nome, email, telefone, 
       ultima_compra,
       total_orcamentos_aprovados,
       valor_total_aprovados
FROM api.vw_prime_clientes_rfv
WHERE recencia_score <= 2 
  AND frequencia_score >= 3 
  AND valor_score >= 3
ORDER BY valor_total_aprovados DESC;

-- Evolução do Score RFV ao Longo do Tempo
-- (requer executar view com data específica)
```

---

## 10. Exemplos de Uso

### 10.1 API REST do Supabase

#### Listar Clientes

```bash
curl -X GET "https://agdffspstbxeqhqtltvb.supabase.co/rest/v1/prime_clientes?select=*&limit=10" \
  -H "apikey: YOUR_ANON_KEY" \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -H "Accept-Profile: api" \
  -H "Content-Type: application/json"
```

#### Buscar Cliente por CPF

```bash
curl -X GET "https://agdffspstbxeqhqtltvb.supabase.co/rest/v1/prime_clientes?cpf_cnpj=eq.12345678900" \
  -H "apikey: YOUR_ANON_KEY" \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -H "Accept-Profile: api"
```

#### Listar Pedidos de um Cliente

```bash
curl -X GET "https://agdffspstbxeqhqtltvb.supabase.co/rest/v1/prime_pedidos?codigo_cliente_original=eq.12345&select=*,prime_formulas(*)" \
  -H "apikey: YOUR_ANON_KEY" \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -H "Accept-Profile: api"
```

### 10.2 SDK JavaScript

```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  'https://agdffspstbxeqhqtltvb.supabase.co',
  'YOUR_ANON_KEY',
  {
    db: {
      schema: 'api'
    }
  }
)

// Buscar clientes por score RFV
const { data, error } = await supabase
  .from('vw_prime_clientes_rfv')
  .select('*')
  .gte('score_rfv_calculado', 500)
  .order('score_rfv_calculado', { ascending: false })
  .limit(10)

// Buscar pedidos com rastreabilidade
const { data: pedidos } = await supabase
  .from('prime_pedidos')
  .select(`
    *,
    prime_clientes (*),
    prime_formulas (*),
    prime_rastreabilidade (
      *,
      prime_tipos_processo (*)
    )
  `)
  .eq('status_geral', 'APROVADO')
```

### 10.3 Dashboard com React

```jsx
import { useEffect, useState } from 'react'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(URL, KEY, { db: { schema: 'api' } })

function DashboardRFV() {
  const [clientes, setClientes] = useState([])
  
  useEffect(() => {
    async function fetchClientes() {
      const { data } = await supabase
        .from('vw_prime_clientes_rfv')
        .select('*')
        .order('score_rfv_calculado', { ascending: false })
        .limit(100)
      setClientes(data)
    }
    fetchClientes()
  }, [])
  
  return (
    <div>
      <h1>Top Clientes RFV</h1>
      <table>
        <thead>
          <tr>
            <th>Nome</th>
            <th>Score RFV</th>
            <th>Última Compra</th>
            <th>Total Gasto</th>
          </tr>
        </thead>
        <tbody>
          {clientes.map(c => (
            <tr key={c.id}>
              <td>{c.nome}</td>
              <td>{c.score_rfv_calculado}</td>
              <td>{c.ultima_compra}</td>
              <td>R$ {c.valor_total_aprovados}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
```

### 10.4 Relatório com Python/Pandas

```python
import pandas as pd
from supabase import create_client

supabase = create_client(URL, KEY, {'db': {'schema': 'api'}})

# Buscar dados
response = supabase.table('vw_prime_clientes_rfv').select('*').execute()
df = pd.DataFrame(response.data)

# Análise
print("Top 10 Clientes por Score RFV:")
print(df.nlargest(10, 'score_rfv_calculado')[
    ['nome', 'score_rfv_calculado', 'valor_total_aprovados']
])

# Segmentação
df['segmento'] = pd.cut(
    df['score_rfv_calculado'],
    bins=[0, 200, 350, 500, 555],
    labels=['Dorminhoco', 'Em Risco', 'Leal', 'Campeão']
)

print("\nDistribuição por Segmento:")
print(df['segmento'].value_counts())

# Exportar para Excel
df.to_excel('analise_rfv.xlsx', index=False)
```

---

## 11. Manutenção e Troubleshooting

### 11.1 Problemas Comuns

#### Erro: "Foreign key constraint failed"

**Causa:** Tentando inserir pedido para cliente que não existe

**Solução:**
```python
# Sempre exportar nesta ordem:
1. prime_tipos_processo (sem dependências)
2. prime_clientes (sem dependências)
3. prime_pedidos (depende de clientes)
4. prime_rastreabilidade (depende de pedidos e tipos)
5. prime_formulas (depende de pedidos)
```

#### Erro: "Duplicate key value violates unique constraint"

**Causa:** Tentando inserir registro com código que já existe

**Solução:** Usar `upsert` em vez de `insert`:
```python
# ✅ Correto (upsert)
supabase.table('prime_clientes').upsert(dados).execute()

# ❌ Errado (insert)
supabase.table('prime_clientes').insert(dados).execute()
```

#### Erro: "Schema 'api' does not exist"

**Causa:** Headers não configurados ou schema não foi criado

**Solução:**
```python
# 1. Verificar headers
supabase = create_client(URL, KEY, {
    'global': {
        'headers': {
            'Accept-Profile': 'api',
            'Content-Profile': 'api'
        }
    }
})

# 2. Verificar se schema foi criado
# No Supabase SQL Editor:
CREATE SCHEMA IF NOT EXISTS api;
```

#### Timeout durante exportação

**Causa:** Muitos dados sendo exportados de uma vez

**Solução:**
```python
# Reduzir tamanho do batch
exportar_clientes(limite=500)  # em vez de 1000
```

### 11.2 Logs e Monitoramento

#### Arquivo de Log

```
export_firebird_supabase.log
```

**Conteúdo:**
- Timestamps de cada operação
- Quantidade de registros processados
- Erros e stack traces
- Estatísticas finais

#### Verificar Log em Tempo Real

```bash
# Windows PowerShell
Get-Content export_firebird_supabase.log -Wait -Tail 50

# Linux/Mac
tail -f export_firebird_supabase.log
```

#### Dashboard do Supabase

1. Acesse: https://supabase.com/dashboard
2. Vá para "Logs" no menu lateral
3. Filtre por:
   - **API**: Requisições HTTP
   - **Database**: Queries SQL
   - **Auth**: Autenticações

### 11.3 Backup e Restauração

#### Backup Manual

```bash
# Via pg_dump (requer acesso direto ao PostgreSQL)
pg_dump -h db.agdffspstbxeqhqtltvb.supabase.co \
        -U postgres \
        -d postgres \
        -n api \
        -F c \
        -f backup_api_schema.dump
```

#### Backup Automático (Supabase)

O Supabase faz backups automáticos diários. Para restaurar:

1. Dashboard → Settings → Database
2. Backups → Restore

#### Exportar Dados para JSON

```python
import json
from supabase import create_client

supabase = create_client(URL, KEY, {'db': {'schema': 'api'}})

# Exportar todas as tabelas
for tabela in ['prime_clientes', 'prime_pedidos', 'prime_formulas']:
    response = supabase.table(tabela).select('*').execute()
    with open(f'backup_{tabela}.json', 'w', encoding='utf-8') as f:
        json.dump(response.data, f, indent=2, ensure_ascii=False)
```

### 11.4 Atualizações do Schema

#### Adicionar Nova Coluna

```sql
-- No Supabase SQL Editor
ALTER TABLE api.prime_clientes 
ADD COLUMN IF NOT EXISTS whatsapp VARCHAR(20);

-- Atualizar dados existentes
UPDATE api.prime_clientes 
SET whatsapp = telefone 
WHERE whatsapp IS NULL;
```

#### Modificar Script Python para Novos Campos

```python
# Adicionar campo na exportação
cliente = {
    'codigo_cliente_original': row[0],
    'nome': self.limpar_string(row[1]),
    # ... campos existentes ...
    'whatsapp': self.limpar_string(row[X]),  # novo campo
}
```

### 11.5 Performance

#### Consultas Lentas

**Diagnóstico:**
```sql
-- Verificar explain plan
EXPLAIN ANALYZE
SELECT * FROM api.prime_pedidos 
WHERE codigo_cliente_original = 12345;
```

**Solução:** Criar índice
```sql
CREATE INDEX IF NOT EXISTS idx_custom 
ON api.prime_pedidos(campo_sem_indice);
```

#### Paginação de Grandes Resultados

```javascript
// Frontend - Paginação infinita
const PAGE_SIZE = 50
let currentPage = 0

async function loadMore() {
  const { data } = await supabase
    .from('prime_pedidos')
    .select('*')
    .range(currentPage * PAGE_SIZE, (currentPage + 1) * PAGE_SIZE - 1)
  
  currentPage++
  return data
}
```

---

## 📚 Arquivos de Referência

| Arquivo | Descrição |
|---------|-----------|
| `sql_supabase_rastreabilidade_completo.sql` | Schema completo com rastreabilidade |
| `sql_supabase_api.sql` | Schema básico (sem rastreabilidade) |
| `exportar_firebird_supabase_final.py` | Script Python principal |
| `config_supabase.py` | Configurações centralizadas |
| `requirements_export_supabase.txt` | Dependências Python |
| `ARQUITETURA.md` | Arquitetura do sistema |
| `GUIA_IMPLEMENTACAO_SUPABASE.md` | Guia de implementação passo a passo |
| `README_EXPORTACAO_SUPABASE.md` | Documentação de exportação |

---

## 🎯 Resumo Executivo

### O que foi criado?

✅ **5 Tabelas no Supabase** (schema `api`):
- `prime_clientes` - Cadastro de clientes
- `prime_pedidos` - Orçamentos/pedidos
- `prime_tipos_processo` - Tipos de processos de produção
- `prime_rastreabilidade` - Rastreamento de produção
- `prime_formulas` - Detalhes das fórmulas

✅ **3 Views Analíticas**:
- `vw_prime_clientes_rfv` - Análise RFV completa
- `vw_prime_rastreabilidade_completa` - Rastreamento detalhado
- `vw_prime_pedidos_status` - Status e métricas de pedidos

✅ **Sistema de Exportação**:
- Script Python com paginação automática
- Retry automático em caso de falhas
- Logs detalhados
- Suporte a grandes volumes de dados

### Dados Exportados

- **~30.000 clientes** com dados completos
- **~85.000 pedidos** com status e valores
- **~342.000 processos** de rastreabilidade
- **~125.000 fórmulas** detalhadas
- **~25 tipos de processo** cadastrados

### Funcionalidades

✅ Análise RFV (Recência, Frequência, Valor)  
✅ Segmentação automática de clientes  
✅ Rastreabilidade completa de produção  
✅ API REST pronta para uso  
✅ Dashboards e relatórios via SQL  
✅ Permissões e segurança (RLS)  
✅ Exportação incremental  

---

**Documentação gerada automaticamente em 21/10/2025**  
**Versão:** 2.0  
**Autor:** Sistema de Integração Prime-Supabase

