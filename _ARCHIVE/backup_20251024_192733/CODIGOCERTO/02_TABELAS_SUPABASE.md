# 🗄️ TABELAS CRIADAS NO SUPABASE

## 📋 Resumo das Tabelas

O Supabase foi configurado com **5 tabelas principais** no schema `api` para receber os dados do Firebird:

1. **`prime_clientes`** - Dados dos clientes
2. **`prime_pedidos`** - Pedidos/orçamentos
3. **`prime_tipos_processo`** - Tipos de processo de produção
4. **`prime_rastreabilidade`** - Rastreabilidade de processos
5. **`prime_formulas`** - Fórmulas dos pedidos

## 🏗️ Estrutura Detalhada das Tabelas

### 1. `prime_clientes` - Tabela de Clientes

```sql
CREATE TABLE api.prime_clientes (
    -- Chave primária
    id BIGSERIAL PRIMARY KEY,
    
    -- ID original do banco Prime
    codigo_cliente_original INTEGER NOT NULL UNIQUE,
    
    -- Dados pessoais
    nome VARCHAR(255) NOT NULL,
    cpf_cnpj VARCHAR(20),
    data_nascimento DATE,
    sexo INTEGER, -- 1=Masculino, 2=Feminino
    
    -- Dados de contato
    email VARCHAR(255),
    telefone VARCHAR(20),
    endereco_logradouro VARCHAR(255),
    endereco_numero VARCHAR(20),
    endereco_cep VARCHAR(10),
    endereco_cidade VARCHAR(100),
    endereco_estado VARCHAR(2),
    endereco_observacao TEXT,
    
    -- Dados de análise RFV
    total_orcamentos INTEGER DEFAULT 0,
    total_orcamentos_aprovados INTEGER DEFAULT 0,
    total_orcamentos_entregues INTEGER DEFAULT 0,
    valor_total_orcamentos DECIMAL(15,2) DEFAULT 0,
    valor_total_aprovados DECIMAL(15,2) DEFAULT 0,
    valor_total_entregues DECIMAL(15,2) DEFAULT 0,
    valor_medio_orcamento DECIMAL(15,2) DEFAULT 0,
    valor_medio_aprovado DECIMAL(15,2) DEFAULT 0,
    valor_medio_entregue DECIMAL(15,2) DEFAULT 0,
    
    -- Datas importantes
    primeira_compra DATE,
    ultima_compra DATE,
    ultima_atualizacao TIMESTAMP DEFAULT NOW(),
    
    -- Status
    ativo BOOLEAN DEFAULT true,
    score_rfv INTEGER DEFAULT 0, -- Score RFV calculado
    
    -- Metadados
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Função:** Armazena dados dos clientes com métricas RFV (Recência, Frequência, Valor) para análise de comportamento.

### 2. `prime_pedidos` - Tabela de Pedidos/Orçamentos

```sql
CREATE TABLE api.prime_pedidos (
    -- Chave primária
    id BIGSERIAL PRIMARY KEY,
    
    -- ID original do banco Prime
    codigo_orcamento_original INTEGER NOT NULL UNIQUE,
    
    -- Relacionamento com cliente
    cliente_id BIGINT NOT NULL REFERENCES api.prime_clientes(id) ON DELETE CASCADE,
    codigo_cliente_original INTEGER NOT NULL,
    
    -- Dados do pedido
    data_criacao TIMESTAMP,
    data_aprovacao TIMESTAMP, -- AVIADA_DT
    data_entrega TIMESTAMP,   -- ENTREGUE_DT
    data_cancelamento TIMESTAMP,
    
    -- Valores
    valor_total DECIMAL(15,2) NOT NULL DEFAULT 0,
    valor_desconto DECIMAL(15,2) DEFAULT 0,
    valor_final DECIMAL(15,2) DEFAULT 0,
    
    -- Status de aprovação
    status_aprovacao VARCHAR(20) NOT NULL, -- 'APROVADO', 'NAO_APROVADO'
    status_entrega VARCHAR(20) NOT NULL,   -- 'ENTREGUE', 'NAO_ENTREGUE'
    status_geral VARCHAR(20) NOT NULL,     -- 'APROVADO', 'PENDENTE', 'CANCELADO', 'DESCARTADO', 'ENTREGUE'
    status_mov INTEGER, -- Status original do banco
    
    -- Status de produção
    data_inicio_producao TIMESTAMP,
    data_fim_producao TIMESTAMP,
    data_prevista_entrega TIMESTAMP,
    
    -- Dados de laboratório
    laboratorio_iniciado BOOLEAN DEFAULT false,
    laboratorio_finalizado BOOLEAN DEFAULT false,
    data_laboratorio_inicio TIMESTAMP,
    data_laboratorio_fim TIMESTAMP,
    
    -- Dados de transporte/entrega
    transporte_iniciado BOOLEAN DEFAULT false,
    transporte_finalizado BOOLEAN DEFAULT false,
    data_transporte_inicio TIMESTAMP,
    data_transporte_fim TIMESTAMP,
    
    -- Observações
    observacoes TEXT,
    observacao_cancelamento TEXT,
    observacao_descarte TEXT,
    observacao_producao TEXT,
    
    -- Dados de análise temporal
    dias_para_aprovacao INTEGER,
    dias_para_entrega INTEGER,
    dias_total_processo INTEGER,
    dias_producao INTEGER,
    dias_transporte INTEGER,
    
    -- Metadados
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Função:** Armazena pedidos/orçamentos com status de produção, laboratório e transporte para rastreabilidade completa.

### 3. `prime_tipos_processo` - Tipos de Processo de Produção

```sql
CREATE TABLE api.prime_tipos_processo (
    -- Chave primária
    id BIGSERIAL PRIMARY KEY,
    
    -- ID original do banco Prime
    codigo_tipo_original INTEGER NOT NULL UNIQUE,
    
    -- Dados do tipo de processo
    nome_processo VARCHAR(100) NOT NULL, -- Ex: "1 - CONF. INICIAL", "2 - PESAGEM"
    nome_ficha VARCHAR(100),
    tipo_producao INTEGER, -- 1=Produção, 3=Conferência, 4=Balcão/Logística
    sequencia INTEGER NOT NULL, -- Ordem de execução
    ativo BOOLEAN DEFAULT true,
    
    -- Configurações
    processo_opcional BOOLEAN DEFAULT false,
    pagar_comissao BOOLEAN DEFAULT false,
    registrar_baixa BOOLEAN DEFAULT false,
    bloquear_calculo BOOLEAN DEFAULT false,
    liberar_entrega BOOLEAN DEFAULT false,
    bloquear_receita BOOLEAN DEFAULT false,
    
    -- Observações
    observacao TEXT,
    
    -- Metadados
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Função:** Define os tipos de processo de produção (CONF. INICIAL, PESAGEM, HOMOGENEIZAÇÃO, MANIPULAÇÃO, etc.).

### 4. `prime_rastreabilidade` - Rastreabilidade de Processos

```sql
CREATE TABLE api.prime_rastreabilidade (
    -- Chave primária
    id BIGSERIAL PRIMARY KEY,
    
    -- ID original do banco Prime
    codigo_processo_original INTEGER NOT NULL UNIQUE,
    
    -- Relacionamentos
    pedido_id BIGINT NOT NULL REFERENCES api.prime_pedidos(id) ON DELETE CASCADE,
    codigo_orcamento_original INTEGER NOT NULL,
    tipo_processo_id BIGINT NOT NULL REFERENCES api.prime_tipos_processo(id),
    codigo_tipo_original INTEGER NOT NULL,
    
    -- Dados do processo
    tipo_movimento INTEGER NOT NULL, -- 1=Orçamento
    codigo_funcionario INTEGER,
    nome_funcionario VARCHAR(255),
    data_processo DATE NOT NULL,
    hora_processo TIME NOT NULL,
    sequencia INTEGER NOT NULL, -- Sequência do processo no pedido
    
    -- Status do processo
    status_processo VARCHAR(50), -- 'PENDENTE', 'EM_ANDAMENTO', 'CONCLUIDO'
    data_inicio TIMESTAMP,
    data_fim TIMESTAMP,
    
    -- Configurações
    pagar_comissao BOOLEAN DEFAULT false,
    
    -- Metadados
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Função:** Rastreia cada etapa do processo de produção com funcionário responsável e horários.

### 5. `prime_formulas` - Fórmulas dos Pedidos

```sql
CREATE TABLE api.prime_formulas (
    -- Chave primária
    id BIGSERIAL PRIMARY KEY,
    
    -- Relacionamento com pedido
    pedido_id BIGINT NOT NULL REFERENCES api.prime_pedidos(id) ON DELETE CASCADE,
    codigo_orcamento_original INTEGER NOT NULL,
    
    -- Dados da fórmula
    numero_formula INTEGER NOT NULL,
    descricao TEXT,
    posologia TEXT,
    valor_formula DECIMAL(15,2) DEFAULT 0,
    
    -- Status de produção da fórmula
    data_inicio_producao TIMESTAMP,
    data_fim_producao TIMESTAMP,
    
    -- Metadados
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Função:** Armazena as fórmulas manipuladas associadas a cada pedido.

## 🔗 Relacionamentos

```
prime_clientes (1) ←→ (N) prime_pedidos
prime_pedidos (1) ←→ (N) prime_rastreabilidade
prime_pedidos (1) ←→ (N) prime_formulas
prime_tipos_processo (1) ←→ (N) prime_rastreabilidade
```

## 📊 Views Criadas

### 1. `vw_prime_clientes_rfv` - Análise RFV
Calcula scores de Recência, Frequência e Valor para segmentação de clientes.

### 2. `vw_prime_rastreabilidade_completa` - Rastreabilidade Completa
Mostra o fluxo completo de produção de cada pedido.

### 3. `vw_prime_pedidos_status` - Status de Pedidos
Resumo do status de produção de todos os pedidos.

## 🔒 Segurança (RLS)

- **Row Level Security** habilitado em todas as tabelas
- **Políticas** configuradas para usuários autenticados
- **Grants** para `anon`, `authenticated` e `service_role`

## 📈 Índices de Performance

Criados índices otimizados para:
- Busca por códigos originais
- Filtros por status
- Ordenação por datas
- Joins entre tabelas

## 🎯 Objetivo das Tabelas

1. **Análise de Clientes:** RFV, comportamento de compra
2. **Rastreabilidade:** Acompanhamento completo da produção
3. **Gestão de Pedidos:** Status, prazos, responsáveis
4. **Relatórios:** Dashboards e análises de performance
5. **Integração:** API para sistemas externos
