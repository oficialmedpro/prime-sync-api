# 🏗️ Arquitetura do Sistema de Exportação

## 📊 Fluxo de Dados

```
┌─────────────────────────────────────────────────────────────────────┐
│                     FIREBIRD ERP (psbd.fdb)                         │
│                                                                     │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────┐            │
│  │ CLIENTE  │    │ATENDIMENTO_A1│    │ATENDIMENTO_A2│            │
│  │ (Leads)  │───▶│ (Orçamentos) │───▶│  (Fórmulas)  │            │
│  └──────────┘    └──────────────┘    └──────────────┘            │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ 📤 export_to_supabase.py
                              │    (Executado automaticamente às 23:00)
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         SUPABASE (PostgreSQL)                        │
│                                                                     │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────┐            │
│  │  leads   │    │ manipulados  │    │   formulas   │            │
│  │ (clones) │◀───│   (clones)   │◀───│   (clones)   │            │
│  └──────────┘    └──────────────┘    └──────────────┘            │
│                                                                     │
│  ┌───────────────────────────────────────────────────┐            │
│  │       vw_orcamentos_completos (View)              │            │
│  │   (Visão completa: leads + manipulados + fórmulas)│            │
│  └───────────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌─────────────────────────────────┐
              │  🌐 Suas Aplicações              │
              │  - Dashboards                    │
              │  - Apps Mobile                   │
              │  - Integrações                   │
              │  - APIs RESTful                  │
              └─────────────────────────────────┘
```

## 🔄 Processo de Exportação

### Fase 1: Extração (Firebird)
```
1. Conectar ao banco Firebird
2. Executar query SQL para LEADS
3. Executar query SQL para MANIPULADOS (últimas 24h)
4. Coletar dados em memória
```

### Fase 2: Transformação (Python)
```
1. Validar dados obrigatórios (nome, CPF)
2. Formatar telefones, datas
3. Agrupar fórmulas por orçamento
4. Preparar objetos JSON
```

### Fase 3: Carga (Supabase)
```
1. Verificar se registro já existe
2. INSERT (novo) ou UPDATE (existente)
3. Manter integridade referencial
4. Registrar log de operações
```

## 📋 Mapeamento de Campos

### CLIENTE (Firebird) → leads (Supabase)

| Firebird | Transformação | Supabase |
|----------|---------------|----------|
| `CODIGO` | → | `codigo_cliente` |
| `NOMECLIENTE` | trim() → | `nome` |
| `CPF_CNPJ` | trim() → | `cpf` |
| `ENDERECO + NUMERO` | concat() → | `endereco` |
| `TELEFONEPREFIXO + TELEFONE1` | concat() → | `telefone` |
| `DIA/MES/ANO NASCIMENTO` | to_date() → | `data_nascimento` |
| `SEXO` | → | `sexo` |

### ATENDIMENTO_A1 (Firebird) → manipulados (Supabase)

| Firebird | Transformação | Supabase |
|----------|---------------|----------|
| `CODIGO` | → | `codigo_orcamento` |
| `CODIGO_CLIENTE` | → | `codigo_cliente` (FK) |
| `AVIADA_DT` | to_iso() → | `data_pedido` |
| `VALORVENDA` | to_decimal() → | `valor_total` |
| `STATUS_MOV` | -1='CANCELADO', 0='ATIVO' → | `status` |
| `OBSERVACAO` | trim() → | `observacoes` |

### ATENDIMENTO_A2 (Firebird) → formulas (Supabase)

| Firebird | Transformação | Supabase |
|----------|---------------|----------|
| `CODIGO_ATEND_A1` | → | `codigo_orcamento` (FK) |
| `NUMEROFORMULA` | → | `numero_formula` |
| `TEXTOROTULO` | trim() → | `descricao` |
| `POSOLOGIA` | trim() → | `posologia` |
| `VALORFORMULA_VENDA` | to_decimal() → | `valor` |
| `MULTIPLO` | → | `quantidade` |

## ⚙️ Componentes do Sistema

### 🐍 Python Script (`export_to_supabase.py`)
```python
Funções principais:
├── conectar_firebird()      # Conexão com ERP
├── conectar_supabase()       # Conexão com Supabase
├── exportar_leads()          # Exporta clientes
├── exportar_manipulados()    # Exporta orçamentos + fórmulas
└── main()                    # Orquestra tudo
```

### 🗄️ Banco Supabase
```sql
Tabelas:
├── leads              # Clientes
├── manipulados        # Orçamentos
├── formulas           # Detalhes das fórmulas
└── vw_orcamentos_completos  # View agregada

Índices:
├── idx_leads_cpf
├── idx_leads_nome
├── idx_manipulados_cliente
├── idx_manipulados_data
└── idx_formulas_orcamento

Triggers:
├── update_leads_updated_at
└── update_manipulados_updated_at
```

### 📝 Logs e Auditoria
```
export_supabase.log:
├── Timestamp de execução
├── Contadores (inseridos/atualizados/erros)
├── Tempo de execução
└── Stack trace de erros
```

## 🔐 Segurança

### Credenciais
```
✅ Armazenadas em config.env (não versionado)
✅ Uso de service_role key do Supabase
✅ Conexão Firebird local/VPN
✅ Logs não expõem dados sensíveis
```

### Validações
```
✅ Campos obrigatórios (nome, CPF)
✅ Tipos de dados validados
✅ Foreign keys respeitadas
✅ Transações atômicas
```

## 📈 Performance

### Otimizações
- ✅ Queries filtradas por data (apenas últimas 24h)
- ✅ Batch inserts quando possível
- ✅ Índices em campos de busca
- ✅ Conexões reutilizadas
- ✅ Logs assíncronos

### Métricas Esperadas
```
Leads: ~30.000 registros em ~15 segundos
Manipulados: ~50 registros/dia em ~5 segundos
Fórmulas: ~100 registros/dia em ~3 segundos
Total: ~25 segundos por execução completa
```

## 🔄 Manutenção

### Monitoramento
1. Verificar `export_supabase.log` diariamente
2. Alertas para erros críticos
3. Backup do Supabase (automático)
4. Validação periódica de integridade

### Atualizações
1. Testar em ambiente de desenvolvimento
2. Backup antes de mudanças
3. Versionamento de scripts SQL
4. Rollback plan preparado

## 🎯 Casos de Uso

### 1. Dashboard Gerencial
```
Supabase → API REST → Frontend
Visualizar vendas, top clientes, fórmulas mais vendidas
```

### 2. App Mobile
```
Supabase → SDK Mobile → App iOS/Android
Consultar histórico de orçamentos do cliente
```

### 3. Integração com CRM
```
Supabase → Webhooks → CRM Externo
Sincronizar leads automaticamente
```

### 4. Análise de Dados
```
Supabase → Python/R → Data Science
Machine Learning, previsões, segmentação
```

## 🛠️ Troubleshooting Rápido

| Sintoma | Causa Provável | Solução |
|---------|----------------|---------|
| Nenhum dado exportado | Firebird sem dados nas últimas 24h | Ajustar `dias_retroativos` |
| Foreign key error | Lead não existe | Exportar leads primeiro |
| Timeout | Muitos registros | Adicionar paginação |
| Duplicatas | Código não único | Verificar chave primária |

---

**📚 Para mais detalhes, consulte:**
- `README_EXPORTACAO_SUPABASE.md` - Documentação completa
- `INICIO_RAPIDO.md` - Guia de início rápido
