# 🚀 GUIA PASSO A PASSO - Exportação Firebird → Supabase

## 📋 Objetivo
Este guia permite que qualquer desenvolvedor execute a exportação completa de dados do **Prime Software (Firebird)** para o **Supabase (PostgreSQL)** de forma rápida e segura.

---

## ⏱️ Tempo Estimado
- **Configuração inicial:** 10-15 minutos
- **Criação do schema:** 5 minutos
- **Exportação de dados:** 15-30 minutos (dependendo do volume)
- **Validação:** 5 minutos
- **TOTAL:** ~30-50 minutos

---

## ✅ PRÉ-REQUISITOS

### 1. Software Necessário
- [ ] **Python 3.12+** instalado
- [ ] **Git** (opcional, para versionamento)
- [ ] **Navegador web** (para acessar Supabase)
- [ ] **Editor de texto** (VS Code, Notepad++, etc.)

### 2. Acessos Necessários
- [ ] Acesso ao servidor Firebird (`db.primesoftware.com.br`)
- [ ] Credenciais do banco `oficialmed1250`
- [ ] Acesso ao dashboard do Supabase
- [ ] Chave de API do Supabase

### 3. Arquivos Necessários
Todos os arquivos já estão no diretório do projeto:
- [ ] `config_supabase.py`
- [ ] `exportar_firebird_supabase_final.py`
- [ ] `sql_supabase_rastreabilidade_completo.sql`
- [ ] `requirements_export_supabase.txt`

---

## 📝 PASSO 1: Verificar Instalação do Python

### Windows:
```powershell
# Abrir PowerShell ou CMD
python --version
```

**Resultado esperado:** `Python 3.12.x` ou superior

### Se Python não estiver instalado:
1. Baixar de: https://www.python.org/downloads/
2. **IMPORTANTE:** Marcar "Add Python to PATH" durante a instalação
3. Reiniciar o terminal após a instalação

---

## 📦 PASSO 2: Instalar Dependências Python

### Navegar até a pasta do projeto:
```powershell
cd "C:\Users\User\Documents\Banco de Dados Prime"
```

### Instalar bibliotecas necessárias:
```powershell
pip install fdb supabase python-dotenv requests
```

**OU** usar o arquivo de requirements:
```powershell
pip install -r requirements_export_supabase.txt
```

### Verificar instalação:
```powershell
pip list | findstr "fdb supabase"
```

**Resultado esperado:**
```
fdb                    2.0.2
supabase               2.0.x
```

---

## 🗄️ PASSO 3: Criar Schema no Supabase

### 3.1. Acessar Dashboard do Supabase
1. Abrir navegador em: https://supabase.com
2. Fazer login
3. Selecionar o projeto: `agdffspstbxeqhqtltvb`

### 3.2. Abrir SQL Editor
1. No menu lateral, clicar em **"SQL Editor"**
2. Clicar em **"New query"**

### 3.3. Executar Script SQL
1. Abrir o arquivo: `sql_supabase_rastreabilidade_completo.sql`
2. **Copiar TODO o conteúdo** do arquivo
3. **Colar** no SQL Editor do Supabase
4. Clicar em **"Run"** ou pressionar `Ctrl + Enter`

### 3.4. Verificar Criação das Tabelas
Executar esta query no SQL Editor:
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'api' 
  AND table_name LIKE 'prime_%'
ORDER BY table_name;
```

**Resultado esperado:**
```
prime_clientes
prime_formulas
prime_pedidos
prime_rastreabilidade
prime_tipos_processo
```

✅ **Se aparecerem as 5 tabelas, o schema foi criado com sucesso!**

---

## 🔌 PASSO 4: Testar Conexões

### 4.1. Executar Script de Teste
```powershell
python teste_conexao_correta.py
```

### 4.2. Resultado Esperado
```
🔌 Testando conexão com Firebird...
✅ Firebird conectado! XXX clientes ativos encontrados

🔌 Testando conexão com Supabase...
✅ Supabase conectado via API!

🎉 Todas as conexões estão funcionando!
```

### 4.3. Se houver erro de conexão:

#### Erro no Firebird:
- Verificar se as credenciais em `config_supabase.py` estão corretas:
  ```python
  FIREBIRD_CONFIG = {
      'host': 'db.primesoftware.com.br',
      'database': 'oficialmed1250',
      'user': 'OFICIALMED',
      'password': 'Lt-@=waIh))Ql3~',
      'charset': 'UTF8'
  }
  ```
- Verificar conectividade com o servidor (ping, firewall)

#### Erro no Supabase:
- Verificar URL e Service Key em `config_supabase.py`
- Verificar se o schema `api` foi criado
- Verificar se as tabelas existem

---

## 🚀 PASSO 5: Executar Exportação de Dados

### 5.1. Executar Script Principal
```powershell
python exportar_firebird_supabase_final.py
```

### 5.2. Acompanhar Progresso
O script mostrará o progresso em tempo real:

```
🚀 Iniciando exportação completa Firebird → Supabase...
🔌 Conectando ao Firebird...
✅ Conectado ao Firebird com sucesso!
🔌 Conectando ao Supabase...
✅ Conectado ao Supabase com sucesso!

🔄 Exportando tipos de processo...
✅ 15 tipos de processo exportados!

🔄 Exportando clientes...
✅ 1000 clientes exportados (total: 1000)
✅ 1000 clientes exportados (total: 2000)
...

🔄 Exportando pedidos...
✅ 1000 pedidos exportados (total: 1000)
...

🔄 Exportando rastreabilidade...
✅ 1000 registros de rastreabilidade exportados (total: 1000)
...

🔄 Exportando fórmulas...
✅ 1000 fórmulas exportadas (total: 1000)
...

🎉 Exportação concluída com sucesso!
📊 Estatísticas:
   tipos_processo: 15
   clientes: 5430
   pedidos: 12567
   rastreabilidade: 45890
   formulas: 23456
```

### 5.3. Tempo de Execução
- **Pequeno volume** (< 10k registros): 5-10 minutos
- **Médio volume** (10k-50k registros): 15-30 minutos
- **Grande volume** (> 50k registros): 30-60 minutos

---

## ✅ PASSO 6: Validar Dados Exportados

### 6.1. Verificar no Supabase Dashboard
1. Acessar: https://supabase.com
2. Ir em **"Table Editor"**
3. Selecionar schema: **"api"**
4. Verificar cada tabela:
   - `prime_clientes`
   - `prime_pedidos`
   - `prime_tipos_processo`
   - `prime_rastreabilidade`
   - `prime_formulas`

### 6.2. Executar Queries de Validação

#### No SQL Editor do Supabase:

**1. Contar registros por tabela:**
```sql
SELECT 
    'prime_clientes' as tabela, 
    COUNT(*) as total 
FROM api.prime_clientes
UNION ALL
SELECT 
    'prime_pedidos', 
    COUNT(*) 
FROM api.prime_pedidos
UNION ALL
SELECT 
    'prime_tipos_processo', 
    COUNT(*) 
FROM api.prime_tipos_processo
UNION ALL
SELECT 
    'prime_rastreabilidade', 
    COUNT(*) 
FROM api.prime_rastreabilidade
UNION ALL
SELECT 
    'prime_formulas', 
    COUNT(*) 
FROM api.prime_formulas;
```

**2. Verificar integridade dos dados:**
```sql
-- Verificar se todos os pedidos têm clientes válidos
SELECT COUNT(*) as pedidos_sem_cliente
FROM api.prime_pedidos p
LEFT JOIN api.prime_clientes c ON p.cliente_id = c.id
WHERE c.id IS NULL;
```

**Resultado esperado:** `0` (zero pedidos sem cliente)

**3. Verificar rastreabilidade:**
```sql
-- Ver exemplo de rastreabilidade completa
SELECT 
    p.codigo_orcamento_original,
    c.nome as cliente,
    p.status_geral,
    tp.nome_processo,
    r.sequencia,
    r.data_processo,
    r.status_processo
FROM api.prime_rastreabilidade r
INNER JOIN api.prime_pedidos p ON r.pedido_id = p.id
INNER JOIN api.prime_clientes c ON p.cliente_id = c.id
INNER JOIN api.prime_tipos_processo tp ON r.tipo_processo_id = tp.id
WHERE p.codigo_orcamento_original = (
    SELECT codigo_orcamento_original 
    FROM api.prime_pedidos 
    LIMIT 1
)
ORDER BY r.sequencia;
```

**4. Verificar análise RFV:**
```sql
-- Top 10 clientes por score RFV
SELECT 
    nome,
    total_orcamentos_aprovados,
    valor_total_aprovados,
    ultima_compra,
    recencia_score,
    frequencia_score,
    valor_score,
    score_rfv_calculado
FROM api.vw_prime_clientes_rfv
ORDER BY score_rfv_calculado DESC
LIMIT 10;
```

---

## 📊 PASSO 7: Verificar Logs

### 7.1. Localizar arquivo de log
```powershell
notepad export_firebird_supabase.log
```

### 7.2. O que procurar no log:
- ✅ Mensagens de sucesso: `✅ Conectado`, `✅ exportados`
- ⚠️ Avisos: `⚠️ Tentativa X falhou` (normal se tiver retry)
- ❌ Erros: `❌ Erro ao` (indicam problemas)

### 7.3. Se houver erros:
1. Ler a mensagem de erro completa no log
2. Verificar se é erro de conexão (voltar ao Passo 4)
3. Verificar se é erro de dados (verificar queries no Firebird)
4. Consultar seção de Troubleshooting abaixo

---

## 🔄 PASSO 8: Configurar Exportação Automática (Opcional)

### 8.1. Para executar diariamente no Windows:

**Criar arquivo batch** (`exportar_diario.bat`):
```batch
@echo off
cd "C:\Users\User\Documents\Banco de Dados Prime"
python exportar_firebird_supabase_final.py
pause
```

**Configurar Agendador de Tarefas do Windows:**
1. Abrir **"Agendador de Tarefas"** (Task Scheduler)
2. Criar **"Tarefa Básica"**
3. Nome: `Exportação Prime para Supabase`
4. Disparador: **Diariamente** às 02:00 (horário de baixo uso)
5. Ação: **Iniciar um programa**
6. Programa: Caminho para `exportar_diario.bat`
7. Concluir

---

## 🆘 TROUBLESHOOTING (Solução de Problemas)

### ❌ Problema: "Python não é reconhecido"
**Solução:**
1. Reinstalar Python marcando "Add to PATH"
2. OU adicionar manualmente ao PATH:
   - Painel de Controle → Sistema → Variáveis de Ambiente
   - Adicionar `C:\Python312` ao PATH

### ❌ Problema: "ModuleNotFoundError: No module named 'fdb'"
**Solução:**
```powershell
pip install fdb supabase python-dotenv
```

### ❌ Problema: "SQLCODE: -902 - Your user name and password are not defined"
**Solução:**
1. Verificar credenciais em `config_supabase.py`
2. Testar conexão manualmente com o Firebird
3. Verificar firewall/VPN

### ❌ Problema: "Erro 401 ou 403 no Supabase"
**Solução:**
1. Verificar se a Service Key está correta
2. Verificar se o schema `api` existe
3. Verificar permissões RLS no Supabase

### ❌ Problema: "Memory Error" ou script muito lento
**Solução:**
Reduzir batch size em `config_supabase.py`:
```python
EXPORT_CONFIG = {
    'batch_size': 500,  # Reduzir de 1000 para 500
    'max_retries': 3,
    'retry_delay': 2,
    'log_level': 'INFO'
}
```

### ❌ Problema: "Dados duplicados no Supabase"
**Solução:**
O script usa UPSERT, então dados duplicados são atualizados automaticamente. Para limpar e reimportar:
```sql
-- NO SQL EDITOR DO SUPABASE (USE COM CUIDADO!)
TRUNCATE api.prime_rastreabilidade CASCADE;
TRUNCATE api.prime_formulas CASCADE;
TRUNCATE api.prime_pedidos CASCADE;
TRUNCATE api.prime_clientes CASCADE;
TRUNCATE api.prime_tipos_processo CASCADE;
```
Depois executar novamente: `python exportar_firebird_supabase_final.py`

---

## 📞 CONTATOS E SUPORTE

### Documentação
- **Pasta CODIGOCERTO:** Toda a documentação técnica
- **Logs:** `export_firebird_supabase.log`

### Arquivos Importantes
- `config_supabase.py` - Configurações
- `exportar_firebird_supabase_final.py` - Script principal
- `sql_supabase_rastreabilidade_completo.sql` - Schema do banco

---

## ✅ CHECKLIST FINAL

Antes de considerar a exportação concluída, verificar:

- [ ] Python 3.12+ instalado
- [ ] Bibliotecas instaladas (fdb, supabase)
- [ ] Schema criado no Supabase (5 tabelas + 3 views)
- [ ] Teste de conexões passou (Firebird + Supabase)
- [ ] Exportação executada sem erros
- [ ] Dados validados no Supabase
- [ ] Logs revisados
- [ ] Queries de validação executadas
- [ ] Views funcionando
- [ ] Documentação lida e compreendida

---

## 🎯 PRÓXIMOS PASSOS APÓS A EXPORTAÇÃO

1. **Criar Dashboards:**
   - Usar as views `vw_prime_clientes_rfv` e `vw_prime_pedidos_status`
   - Integrar com ferramentas de BI (Metabase, Grafana, etc.)

2. **Configurar API:**
   - Usar endpoints REST do Supabase
   - Criar funções serverless (Edge Functions)

3. **Automatizar:**
   - Configurar exportação automática diária
   - Configurar alertas de falha

4. **Monitorar:**
   - Verificar logs regularmente
   - Acompanhar volume de dados
   - Monitorar performance das queries

---

## 📊 RESUMO VISUAL DO FLUXO

```
┌─────────────────────────────────────────────────────────────┐
│  PASSO 1: Verificar Python                                  │
│  ├─ python --version                                        │
│  └─ Se não instalado: instalar Python 3.12+                 │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  PASSO 2: Instalar Dependências                             │
│  └─ pip install fdb supabase python-dotenv                  │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  PASSO 3: Criar Schema no Supabase                          │
│  ├─ Acessar dashboard Supabase                              │
│  ├─ Abrir SQL Editor                                        │
│  └─ Executar sql_supabase_rastreabilidade_completo.sql      │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  PASSO 4: Testar Conexões                                   │
│  └─ python teste_conexao_correta.py                         │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  PASSO 5: Executar Exportação                               │
│  └─ python exportar_firebird_supabase_final.py              │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  PASSO 6: Validar Dados                                     │
│  ├─ Verificar dashboard Supabase                            │
│  └─ Executar queries de validação                           │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  PASSO 7: Verificar Logs                                    │
│  └─ Revisar export_firebird_supabase.log                    │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  🎉 EXPORTAÇÃO CONCLUÍDA COM SUCESSO!                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 NOTAS IMPORTANTES

1. **Backup:** Sempre faça backup antes de executar scripts em produção
2. **Horário:** Execute exportações fora do horário comercial
3. **Logs:** Sempre verifique os logs após a execução
4. **Validação:** Nunca pule a etapa de validação de dados
5. **Documentação:** Mantenha esta documentação atualizada

---

**Versão:** 1.0  
**Data:** 21/10/2025  
**Status:** ✅ Pronto para Produção  
**Última Atualização:** 21/10/2025 20:15
