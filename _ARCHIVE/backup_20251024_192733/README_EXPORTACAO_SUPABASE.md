# 📤 Exportação Automática: Firebird ERP → Supabase

Documentação completa do sistema de exportação automática de dados do ERP (Firebird) para o Supabase.

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Estrutura de Dados](#estrutura-de-dados)
3. [Configuração Inicial](#configuração-inicial)
4. [Como Usar](#como-usar)
5. [Automação](#automação)
6. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

Este sistema exporta automaticamente dados do seu ERP Firebird para o Supabase, incluindo:

- **Leads (Clientes)**: Nome, CPF, endereço, telefone, data de nascimento, sexo
- **Manipulados (Orçamentos)**: Número do orçamento, cliente, data, valor total, status
- **Fórmulas**: Detalhes de cada fórmula (descrição, posologia, valor, quantidade)

### 📊 Exemplo de Dados Exportados

```
Orçamento nº: 251002809
Cliente: Ismael Alves Lucio
Fórmula nº 1: 60 CAPSULAS | Hidroxicloroquina 150mg, Diacereina 50mg...
Valor R$ 269,04
```

---

## 🗄️ Estrutura de Dados

### Tabela: `leads`

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `id` | BIGSERIAL | ✅ (PK) | ID interno do Supabase |
| `codigo_cliente` | INTEGER | ✅ (Unique) | Código do cliente no ERP |
| `nome` | VARCHAR(255) | ✅ | Nome completo do cliente |
| `cpf` | VARCHAR(14) | ✅ | CPF do cliente |
| `endereco` | TEXT | ❌ | Endereço completo |
| `telefone` | VARCHAR(20) | ❌ | Telefone com DDD |
| `data_nascimento` | DATE | ❌ | Data de nascimento |
| `sexo` | CHAR(1) | ❌ | M/F |
| `created_at` | TIMESTAMP | ✅ | Data de criação |
| `updated_at` | TIMESTAMP | ✅ | Data de atualização |

### Tabela: `manipulados`

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `id` | BIGSERIAL | ✅ (PK) | ID interno do Supabase |
| `codigo_orcamento` | INTEGER | ✅ (Unique) | Número do orçamento |
| `codigo_cliente` | INTEGER | ✅ (FK) | Referência ao lead |
| `data_pedido` | TIMESTAMP | ✅ | Data do pedido |
| `valor_total` | DECIMAL(10,2) | ✅ | Valor total em R$ |
| `status` | VARCHAR(50) | ❌ | ATIVO/CANCELADO |
| `observacoes` | TEXT | ❌ | Observações |
| `created_at` | TIMESTAMP | ✅ | Data de criação |
| `updated_at` | TIMESTAMP | ✅ | Data de atualização |

### Tabela: `formulas`

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `id` | BIGSERIAL | ✅ (PK) | ID interno do Supabase |
| `codigo_orcamento` | INTEGER | ✅ (FK) | Referência ao manipulado |
| `numero_formula` | INTEGER | ✅ | Número da fórmula |
| `descricao` | TEXT | ✅ | Descrição completa |
| `posologia` | TEXT | ❌ | Como tomar |
| `valor` | DECIMAL(10,2) | ✅ | Valor em R$ |
| `quantidade` | INTEGER | ❌ | Quantidade |
| `created_at` | TIMESTAMP | ✅ | Data de criação |

---

## ⚙️ Configuração Inicial

### 1️⃣ Criar Tabelas no Supabase

1. Acesse o **SQL Editor** no dashboard do Supabase
2. Execute o script `supabase_schema.sql`
3. Verifique se as tabelas foram criadas com sucesso

### 2️⃣ Instalar Dependências Python

```bash
# Navegue até a pasta do projeto
cd "C:\Users\User\Documents\Banco de Dados Prime"

# Instale as dependências
pip install -r requirements.txt
```

### 3️⃣ Configurar Credenciais

1. Copie o arquivo de exemplo:
   ```bash
   copy config.env.exemplo config.env
   ```

2. Edite `config.env` com suas credenciais do Supabase:
   ```env
   SUPABASE_URL=https://seu-projeto.supabase.co
   SUPABASE_KEY=sua-chave-service-role-aqui
   ```

3. **IMPORTANTE**: Use a chave **service_role** (não a anon key)
   - Acesse: Supabase Dashboard → Settings → API
   - Copie a chave **service_role** (mantém segura!)

### 4️⃣ Ajustar Configurações do Firebird

No arquivo `export_to_supabase.py`, ajuste se necessário:

```python
FIREBIRD_CONFIG = {
    'host': 'localhost',  # ou IP do servidor
    'database': r'C:\Users\User\Documents\Banco de Dados Prime\psbd.fdb',
    'user': 'SYSDBA',
    'password': 'masterkey',
    'charset': 'UTF8'
}
```

---

## 🚀 Como Usar

### Execução Manual

**Opção 1: Clique duplo no arquivo batch**
```
executar_exportacao.bat
```

**Opção 2: Via linha de comando**
```bash
cd "C:\Users\User\Documents\Banco de Dados Prime"
python export_to_supabase.py
```

### O que acontece durante a exportação:

1. ✅ Conecta ao Firebird e Supabase
2. 📤 Exporta **TODOS os clientes ativos**
3. 📤 Exporta **manipulados das últimas 24 horas**
4. 🔄 Atualiza registros existentes ou insere novos
5. 📝 Gera log detalhado (`export_supabase.log`)

### Exemplo de Log

```
2025-10-21 09:30:00 - INFO - 🚀 INICIANDO EXPORTAÇÃO: FIREBIRD -> SUPABASE
2025-10-21 09:30:01 - INFO - ✅ Conectado ao Firebird com sucesso
2025-10-21 09:30:02 - INFO - ✅ Conectado ao Supabase com sucesso
2025-10-21 09:30:05 - INFO - 📤 Iniciando exportação de LEADS...
2025-10-21 09:30:15 - INFO - ✅ LEADS - Inseridos: 150, Atualizados: 200, Erros: 0
2025-10-21 09:30:16 - INFO - 📤 Iniciando exportação de MANIPULADOS...
2025-10-21 09:30:25 - INFO - ✅ MANIPULADOS - Inseridos: 25, Atualizados: 5
2025-10-21 09:30:25 - INFO - ✅ FÓRMULAS - Inseridas: 45, Erros: 0
2025-10-21 09:30:25 - INFO - ⏱️  Tempo total: 25.34 segundos
```

---

## ⏰ Automação

### Agendar Execução Diária (Windows)

**Método 1: Usar o script batch (Recomendado)**

1. Clique com botão direito em `agendar_exportacao.bat`
2. Selecione **"Executar como administrador"**
3. A tarefa será agendada para executar **todos os dias às 23:00**

**Método 2: Agendador de Tarefas do Windows**

1. Abra o **Agendador de Tarefas** do Windows
2. Criar Tarefa Básica
   - Nome: `Exportacao Firebird para Supabase`
   - Gatilho: Diariamente às 23:00
   - Ação: Iniciar programa
     - Programa: `python`
     - Argumentos: `export_to_supabase.py`
     - Iniciar em: `C:\Users\User\Documents\Banco de Dados Prime`

### Verificar Tarefa Agendada

```bash
# Listar tarefas agendadas
schtasks /query /tn "Exportacao Firebird para Supabase"

# Executar manualmente
schtasks /run /tn "Exportacao Firebird para Supabase"

# Remover tarefa
schtasks /delete /tn "Exportacao Firebird para Supabase" /f
```

### Alterar Horário de Execução

Edite o arquivo `agendar_exportacao.bat` e altere:

```batch
REM Altere /st 23:00 para o horário desejado (formato 24h)
schtasks /create ... /st 23:00 /f
```

---

## 📊 Consultar Dados no Supabase

### Usando o SQL Editor

```sql
-- Ver todos os leads
SELECT * FROM leads ORDER BY created_at DESC LIMIT 10;

-- Ver orçamentos completos (com fórmulas)
SELECT * FROM vw_orcamentos_completos 
WHERE data_pedido >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY data_pedido DESC;

-- Total de orçamentos por cliente
SELECT 
    l.nome,
    COUNT(m.id) as total_orcamentos,
    SUM(m.valor_total) as valor_total
FROM leads l
LEFT JOIN manipulados m ON l.codigo_cliente = m.codigo_cliente
GROUP BY l.nome
ORDER BY valor_total DESC;
```

### Usando a API do Supabase

```javascript
// Exemplo em JavaScript
const { data, error } = await supabase
  .from('vw_orcamentos_completos')
  .select('*')
  .gte('data_pedido', '2025-10-01')
  .order('data_pedido', { ascending: false });
```

---

## 🔧 Troubleshooting

### ❌ Erro: "Módulo fdb não encontrado"

**Solução:**
```bash
pip install fdb==2.0.2
```

### ❌ Erro: "Não foi possível conectar ao Firebird"

**Verificar:**
1. Caminho do banco está correto?
2. Usuário/senha estão corretos?
3. Firebird está rodando?

**Testar conexão:**
```python
import fdb
conn = fdb.connect(
    database=r'C:\Users\User\Documents\Banco de Dados Prime\psbd.fdb',
    user='SYSDBA',
    password='masterkey'
)
print("Conectado com sucesso!")
conn.close()
```

### ❌ Erro: "Unauthorized" no Supabase

**Solução:**
- Verifique se está usando a chave **service_role** (não anon)
- Confirme a URL do projeto no `config.env`

### ❌ Erro: "Foreign key constraint"

**Causa:** Tentando inserir manipulado para cliente que não existe

**Solução:**
1. Execute primeiro a exportação de leads
2. Verifique se o `codigo_cliente` existe na tabela `leads`

### ⚠️ Dados não aparecem no Supabase

**Verificar:**
1. Há dados nas últimas 24h no Firebird?
2. Verifique o log: `export_supabase.log`
3. Execute consulta direta no Firebird:
   ```sql
   SELECT COUNT(*) FROM ATENDIMENTO_A1 
   WHERE AVIADA_DT >= CURRENT_DATE - 1;
   ```

### 📝 Ver Log Detalhado

O arquivo `export_supabase.log` contém todos os detalhes da execução:

```bash
# Ver últimas 50 linhas do log
Get-Content export_supabase.log -Tail 50
```

---

## 🎯 Personalizações

### Alterar Período de Exportação

No arquivo `export_to_supabase.py`, na chamada da função:

```python
# Exportar últimos 7 dias
exportar_manipulados(conn_firebird, supabase, dias_retroativos=7)

# Exportar apenas hoje
exportar_manipulados(conn_firebird, supabase, dias_retroativos=0)
```

### Adicionar Novos Campos

1. Adicione o campo no Supabase
2. Modifique a consulta SQL em `consulta_export_supabase.sql`
3. Atualize o dicionário no script Python

### Filtrar Apenas Clientes Específicos

Modifique a consulta em `export_to_supabase.py`:

```python
sql_leads = """
    SELECT ... FROM CLIENTE C
    WHERE C.ATIVO = 'S'
    AND C.CODIGO >= 10000  -- Exemplo: apenas clientes >= 10000
    ORDER BY C.CODIGO
"""
```

---

## 📚 Arquivos do Sistema

| Arquivo | Descrição |
|---------|-----------|
| `export_to_supabase.py` | Script principal de exportação |
| `supabase_schema.sql` | Schema das tabelas do Supabase |
| `requirements.txt` | Dependências Python |
| `config.env.exemplo` | Exemplo de configuração |
| `executar_exportacao.bat` | Execução manual |
| `agendar_exportacao.bat` | Agendar execução automática |
| `export_supabase.log` | Log de execuções |
| `consulta_export_supabase.sql` | Consulta para Leads |
| `consulta_manipulados.sql` | Consulta para Manipulados |

---

## 🆘 Suporte

Para problemas ou dúvidas:

1. Verifique o log: `export_supabase.log`
2. Revise a seção [Troubleshooting](#troubleshooting)
3. Teste a conexão com Firebird e Supabase separadamente
4. Verifique se as tabelas foram criadas corretamente no Supabase

---

## ✅ Checklist de Implementação

- [ ] Criar tabelas no Supabase (`supabase_schema.sql`)
- [ ] Instalar Python 3.7+ 
- [ ] Instalar dependências (`pip install -r requirements.txt`)
- [ ] Configurar credenciais no `config.env`
- [ ] Testar exportação manual (`executar_exportacao.bat`)
- [ ] Agendar execução automática (`agendar_exportacao.bat`)
- [ ] Verificar dados no Supabase
- [ ] Configurar alertas/monitoramento (opcional)

---

**🎉 Sistema pronto para uso!**

A exportação automática garante que seus dados estejam sempre sincronizados entre o ERP Firebird e o Supabase, permitindo construir dashboards, integrações e aplicações modernas com facilidade.
