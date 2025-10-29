# 🚀 Início Rápido - Exportação Firebird → Supabase

## ⚡ 5 Passos para Começar

### 1️⃣ Criar Tabelas no Supabase (2 minutos)
```sql
-- Copie e cole o conteúdo de supabase_schema.sql no SQL Editor do Supabase
-- Dashboard → SQL Editor → New Query → Executar
```

### 2️⃣ Instalar Python e Dependências (3 minutos)
```bash
# Abra o PowerShell na pasta do projeto
pip install -r requirements.txt
```

### 3️⃣ Configurar Credenciais (1 minuto)
```bash
# Copie o arquivo de exemplo
copy config.env.exemplo config.env

# Edite config.env e adicione:
# - SUPABASE_URL do seu projeto
# - SUPABASE_KEY (service_role key)
```
📍 **Onde pegar:** Supabase Dashboard → Settings → API

### 4️⃣ Testar Exportação Manual (1 minuto)
```bash
# Clique duas vezes em:
executar_exportacao.bat

# Ou execute:
python export_to_supabase.py
```

### 5️⃣ Agendar Execução Automática (1 minuto)
```bash
# Clique com botão direito (como Administrador):
agendar_exportacao.bat
```

---

## 📊 O Que Será Exportado

### ✅ Leads (Clientes)
- Nome *(obrigatório)*
- CPF *(obrigatório)*
- Endereço
- Telefone
- Data de Nascimento
- Sexo

### ✅ Manipulados (Orçamentos)
- Número do Orçamento
- Cliente
- Data do Pedido
- Valor Total
- Status

### ✅ Fórmulas
- Número da Fórmula
- Descrição Completa
- Posologia
- Valor
- Quantidade

---

## 🎯 Exemplo de Dado Exportado

```json
{
  "orcamento": 251002809,
  "cliente": "Ismael Alves Lucio",
  "valor_total": 269.04,
  "formulas": [
    {
      "numero": 1,
      "descricao": "60 CAPSULAS | Hidroxicloroquina 150mg, Diacereina 50mg...",
      "valor": 269.04
    }
  ]
}
```

---

## ⏰ Quando Executar

### 🤖 Automático (Recomendado)
- **Frequência:** Diária às 23:00
- **Dados:** Últimas 24 horas
- **Configurado por:** `agendar_exportacao.bat`

### 🖱️ Manual (Quando Precisar)
- Clique: `executar_exportacao.bat`
- Ou comando: `python export_to_supabase.py`

---

## 📝 Ver Resultados

### No Supabase (Web)
```
Dashboard → Table Editor → Tabelas: leads, manipulados, formulas
```

### Via SQL
```sql
-- Ver últimos orçamentos
SELECT * FROM vw_orcamentos_completos 
ORDER BY data_pedido DESC 
LIMIT 10;
```

### No Log
```
Arquivo: export_supabase.log
```

---

## ❓ Problemas Comuns

| Problema | Solução |
|----------|---------|
| "Módulo não encontrado" | `pip install -r requirements.txt` |
| "Unauthorized" no Supabase | Use a chave **service_role** no config.env |
| "Erro ao conectar Firebird" | Verifique caminho/usuário/senha no script |
| Dados não aparecem | Verifique log e consulte últimas 24h no Firebird |

---

## 🆘 Precisa de Ajuda?

1. Veja o log: `export_supabase.log`
2. Leia a documentação completa: `README_EXPORTACAO_SUPABASE.md`
3. Teste conexões separadamente (Firebird e Supabase)

---

## 📁 Arquivos Importantes

| Arquivo | Para Que Serve |
|---------|----------------|
| `export_to_supabase.py` | 🐍 Script principal |
| `executar_exportacao.bat` | ▶️ Rodar manual |
| `agendar_exportacao.bat` | ⏰ Agendar automático |
| `supabase_schema.sql` | 🗄️ Criar tabelas |
| `config.env` | 🔑 Suas credenciais |

---

**🎉 Pronto! Seus dados do ERP estarão sempre sincronizados com o Supabase!**
