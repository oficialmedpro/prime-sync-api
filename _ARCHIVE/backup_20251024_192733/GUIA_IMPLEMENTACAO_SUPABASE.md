# 🚀 Guia de Implementação - Supabase Prime

## 🎯 **Objetivo**
Criar duas tabelas no Supabase (`prime_clientes` e `prime_pedidos`) para análise RFV completa dos clientes do sistema Prime.

---

## 📋 **Estrutura das Tabelas**

### **1. Tabela `prime_clientes`**
- **Chave primária**: `id` (auto-incremento)
- **Relacionamento**: `codigo_cliente_original` (ID do banco Prime)
- **Dados pessoais**: nome, CPF, data nascimento, sexo
- **Dados de contato**: email, telefone, endereço completo
- **Métricas RFV**: totais, médias, datas importantes
- **Score RFV**: calculado automaticamente

### **2. Tabela `prime_pedidos`**
- **Chave primária**: `id` (auto-incremento)
- **Relacionamento**: `cliente_id` → `prime_clientes.id`
- **Dados do pedido**: códigos, datas, valores, status
- **Status de aprovação**: baseado em `AVIADA_DT`
- **Análise temporal**: dias para aprovação/entrega

### **3. Tabela `prime_formulas`**
- **Chave primária**: `id` (auto-incremento)
- **Relacionamento**: `pedido_id` → `prime_pedidos.id`
- **Dados da fórmula**: descrição, posologia, valor

---

## 🔧 **Passo a Passo de Implementação**

### **ETAPA 1: Configurar Supabase**

1. **Acesse o Supabase Dashboard**
   - Vá para [supabase.com](https://supabase.com)
   - Faça login na sua conta

2. **Crie um novo projeto** (se necessário)
   - Clique em "New Project"
   - Escolha organização e nome do projeto
   - Aguarde a criação (2-3 minutos)

3. **Execute o Schema SQL**
   - Vá para "SQL Editor" no menu lateral
   - Cole o conteúdo do arquivo `supabase_schema_prime.sql`
   - Clique em "Run" para executar

4. **Verifique as tabelas criadas**
   - Vá para "Table Editor"
   - Confirme que as tabelas foram criadas:
     - `api.prime_clientes`
     - `api.prime_pedidos`
     - `api.prime_formulas`

### **ETAPA 2: Configurar Credenciais**

1. **Obter credenciais do Supabase**
   - Vá para "Settings" → "API"
   - Copie a "Project URL"
   - Copie a "service_role" key (não a anon key)

2. **Configurar arquivo de ambiente**
   ```bash
   # Copie o arquivo de exemplo
   cp config_supabase.env.exemplo config_supabase.env
   
   # Edite com suas credenciais
   nano config_supabase.env
   ```

3. **Preencher credenciais**
   ```env
   SUPABASE_URL=https://seu-projeto.supabase.co
   SUPABASE_KEY=sua-chave-service-role-aqui
   ```

### **ETAPA 3: Instalar Dependências**

```bash
# Instalar dependências Python
pip install -r requirements_supabase.txt

# Ou instalar individualmente
pip install fdb supabase python-dotenv
```

### **ETAPA 4: Executar Exportação**

```bash
# Executar script de exportação
python exportar_para_supabase_prime.py
```

---

## 📊 **Análise RFV Implementada**

### **Métricas de Recência (R)**
- **Score 5**: Última compra há menos de 30 dias
- **Score 4**: Última compra há 30-60 dias
- **Score 3**: Última compra há 60-90 dias
- **Score 2**: Última compra há 90-180 dias
- **Score 1**: Última compra há mais de 180 dias

### **Métricas de Frequência (F)**
- **Score 5**: 10+ compras aprovadas
- **Score 4**: 5-9 compras aprovadas
- **Score 3**: 2-4 compras aprovadas
- **Score 2**: 1 compra aprovada
- **Score 1**: 0 compras aprovadas

### **Métricas de Valor (V)**
- **Score 5**: R$ 2.500+ em compras
- **Score 4**: R$ 1.000-2.500
- **Score 3**: R$ 500-1.000
- **Score 2**: R$ 100-500
- **Score 1**: R$ 0-100

### **Score RFV Combinado**
```
Score RFV = (Recência × 100) + (Frequência × 10) + Valor
```

---

## 🔍 **Consultas Úteis**

### **1. Top 10 Clientes por Score RFV**
```sql
SELECT 
    nome,
    cpf_cnpj,
    email,
    score_rfv_calculado,
    total_orcamentos_aprovados,
    valor_total_aprovados,
    ultima_compra
FROM api.vw_prime_clientes_rfv
ORDER BY score_rfv_calculado DESC
LIMIT 10;
```

### **2. Clientes por Segmento RFV**
```sql
SELECT 
    CASE 
        WHEN recencia_score >= 4 AND frequencia_score >= 4 AND valor_score >= 4 THEN 'Campeões'
        WHEN recencia_score >= 3 AND frequencia_score >= 3 AND valor_score >= 3 THEN 'Clientes Leais'
        WHEN recencia_score >= 4 AND frequencia_score <= 2 THEN 'Novos Clientes'
        WHEN recencia_score <= 2 AND frequencia_score >= 3 THEN 'Clientes em Risco'
        WHEN recencia_score <= 2 AND frequencia_score <= 2 AND valor_score >= 3 THEN 'Clientes VIP em Risco'
        ELSE 'Clientes Dorminhocos'
    END as segmento_rfv,
    COUNT(*) as quantidade
FROM api.vw_prime_clientes_rfv
GROUP BY segmento_rfv
ORDER BY quantidade DESC;
```

### **3. Análise de Pedidos por Status**
```sql
SELECT 
    status_aprovacao,
    status_geral,
    COUNT(*) as quantidade,
    AVG(valor_total) as valor_medio,
    SUM(valor_total) as valor_total
FROM api.prime_pedidos
GROUP BY status_aprovacao, status_geral
ORDER BY quantidade DESC;
```

### **4. Evolução Temporal de Vendas**
```sql
SELECT 
    DATE_TRUNC('month', data_aprovacao) as mes,
    COUNT(*) as pedidos_aprovados,
    SUM(valor_total) as valor_total,
    AVG(valor_total) as valor_medio
FROM api.prime_pedidos
WHERE status_aprovacao = 'APROVADO'
GROUP BY mes
ORDER BY mes DESC;
```

---

## 📈 **Dashboard Sugerido**

### **Métricas Principais**
1. **Total de Clientes**: `COUNT(*) FROM prime_clientes`
2. **Clientes Ativos**: `COUNT(*) WHERE ultima_compra >= NOW() - INTERVAL '90 days'`
3. **Taxa de Aprovação**: `(aprovados / total) * 100`
4. **Ticket Médio**: `AVG(valor_total) WHERE status_aprovacao = 'APROVADO'`
5. **Receita Total**: `SUM(valor_total) WHERE status_aprovacao = 'APROVADO'`

### **Gráficos Recomendados**
1. **Distribuição RFV**: Pizza chart com segmentos
2. **Evolução de Vendas**: Linha temporal
3. **Top Produtos**: Fórmulas mais vendidas
4. **Geolocalização**: Vendas por cidade/estado
5. **Análise de Churn**: Clientes inativos

---

## 🔄 **Manutenção e Atualizações**

### **Exportação Incremental**
```bash
# Executar exportação diária
python exportar_para_supabase_prime.py
```

### **Atualização de Métricas RFV**
```sql
-- Executar após cada exportação
SELECT api.atualizar_metricas_rfv();
```

### **Limpeza de Dados Antigos**
```sql
-- Manter apenas últimos 2 anos
DELETE FROM api.prime_pedidos 
WHERE data_criacao < NOW() - INTERVAL '2 years';
```

---

## ⚠️ **Considerações Importantes**

### **Segurança**
- Use sempre a `service_role` key para operações de escrita
- Configure RLS (Row Level Security) se necessário
- Monitore logs de acesso

### **Performance**
- Os índices foram criados para otimizar consultas
- Use paginação para grandes volumes de dados
- Monitore performance das consultas

### **Backup**
- Configure backup automático no Supabase
- Exporte dados regularmente para backup local
- Mantenha logs de exportação

---

## 📞 **Suporte e Troubleshooting**

### **Problemas Comuns**

1. **Erro de conexão Supabase**
   - Verifique URL e chave
   - Confirme que o projeto está ativo

2. **Erro de permissão**
   - Use service_role key, não anon key
   - Verifique políticas RLS

3. **Timeout na exportação**
   - Reduza batch_size no script
   - Execute em horários de menor uso

4. **Dados duplicados**
   - Use upsert com on_conflict
   - Verifique chaves únicas

### **Logs e Monitoramento**
- Verifique logs do Supabase Dashboard
- Monitore uso de API
- Configure alertas de erro

---

**Última atualização**: 21/10/2025  
**Versão**: 1.0  
**Autor**: Sistema de Exportação Prime
