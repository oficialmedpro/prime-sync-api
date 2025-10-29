# Sistema de Sincronizacao Firebird → Supabase

**Projeto:** Oficialmed - Sincronizacao Incremental Prime
**Versao:** 2.0.0
**Status:** ✅ EM PRODUCAO

---

## 📋 VISAO GERAL

Sistema automatizado de sincronizacao incremental entre Firebird (Prime) e PostgreSQL (Supabase).

- **Sincronizacao:** Automatica a cada 30 minutos
- **API:** https://sincro.oficialmed.com.br
- **Supabase:** https://supabase.com/dashboard/project/agdffspstbxeqhqtltvb
- **Repositorio:** https://github.com/oficialmedpro/prime-sync-api

---

## 📁 ESTRUTURA DO PROJETO

```
Banco de Dados Prime/
│
├── sync-api/                          # ⭐ API EM PRODUCAO
│   ├── app.py                         # API Flask principal
│   ├── requirements.txt               # Dependencias
│   ├── Dockerfile                     # Build Docker
│   ├── supabase-cronjob.sql          # Configuracao cronjob
│   └── README.md                      # Docs da API
│
├── scripts/                           # Scripts de validacao
│   ├── verificar_novos_registros.py   # Verifica novos registros
│   ├── validar_migracao_completa.py   # Valida dados completos
│   ├── verificar_totais_rapido.py     # Comparacao rapida
│   └── ... (10 scripts)
│
├── schemas/                           # Schemas SQL do Supabase
│   ├── sql_supabase_rastreabilidade_completo.sql
│   ├── supabase_schema.sql
│   └── ... (10 schemas)
│
├── _ARCHIVE/                          # Backups de arquivos removidos
│   └── backup_20251024_192733/        # 241 arquivos arquivados
│
├── DOCUMENTACAO_FINAL.md              # 📄 DOCUMENTACAO COMPLETA
├── ARQUIVOS_PARA_REMOVER.md           # Lista de arquivos removidos
├── requirements.txt                   # Dependencias principais
└── README.md                          # Este arquivo
```

---

## 🚀 INICIO RAPIDO

### 1. Verificar Status da API

```bash
curl https://sincro.oficialmed.com.br/health
```

### 2. Executar Sincronizacao Manual

```bash
curl https://sincro.oficialmed.com.br/sync
```

### 3. Verificar se Dados Estao Sincronizados

```bash
cd "c:\Banco de Dados Prime\scripts"
python verificar_novos_registros.py
```

---

## 📊 DADOS SINCRONIZADOS

| Tabela | Origem (Firebird) | Destino (Supabase) | Status |
|--------|-------------------|-------------------|--------|
| Clientes | CLIENTE | prime_clientes | ✅ 37,271 |
| Pedidos | ATENDIMENTO_A1 | prime_pedidos | ✅ 16,844 |
| Formulas | ATENDIMENTO_A2 | prime_formulas | ✅ 32,402 |
| Itens | ATENDIMENTO_A3 | prime_formulas_itens | ✅ 348,280 |
| Tipos Processo | FORMAFARMACEUTICA_PROCESSO_TIPO | prime_tipos_processo | ✅ 9 |
| Rastreabilidade | PROCESSO_MANIPULACAO | prime_rastreabilidade | ✅ 208,902 |

---

## ⏰ CRONJOB AUTOMATICO

**Configuracao Atual:**
- **Nome:** prime-sync-api-cron
- **Frequencia:** A cada 30 minutos (`*/30 * * * *`)
- **URL:** https://sincro.oficialmed.com.br/sync
- **Metodo:** POST via pg_net

**Verificar status do cronjob no Supabase:**

```sql
-- Ver job ativo
SELECT * FROM cron.job WHERE jobname = 'prime-sync-api-cron';

-- Ver ultimas execucoes
SELECT * FROM cron.job_run_details
WHERE jobid = (SELECT jobid FROM cron.job WHERE jobname = 'prime-sync-api-cron')
ORDER BY start_time DESC LIMIT 10;
```

---

## 📖 DOCUMENTACAO

### Documentacao Principal
📄 **[DOCUMENTACAO_FINAL.md](./DOCUMENTACAO_FINAL.md)** - Documentacao completa com:
- Arquitetura detalhada
- Funcoes da API
- Estrutura das tabelas
- Troubleshooting
- Guias de deploy

### Documentacao da API
📄 **[sync-api/README.md](./sync-api/README.md)** - Documentacao tecnica da API

### Scripts de Validacao
📁 **[scripts/](./scripts/)** - 10 scripts para validacao e monitoramento

### Schemas SQL
📁 **[schemas/](./schemas/)** - 10 schemas SQL do Supabase

---

## 🔧 MANUTENCAO

### Verificar Novos Registros

```bash
cd scripts
python verificar_novos_registros.py
```

### Validar Dados Completos

```bash
cd scripts
python validar_migracao_completa.py
```

### Ver Logs da API (Portainer)

1. Acesse Portainer
2. Va em Containers
3. Clique no container da API
4. Veja logs em tempo real

---

## 🗂️ ARQUIVOS ARQUIVADOS

**Total de arquivos movidos para backup:** 241

Arquivos de teste, desenvolvimento e temporarios foram movidos para:
```
_ARCHIVE/backup_20251024_192733/
```

**Para recuperar algum arquivo:**
1. Navegue ate `_ARCHIVE/backup_20251024_192733/`
2. Localize o arquivo
3. Mova de volta para a pasta original

**Para remover o backup definitivamente:**
```bash
rmdir /s "_ARCHIVE"
```

---

## 📞 CONTATOS

**Desenvolvedor:** Claude Code + Equipe Oficialmed
**API:** https://sincro.oficialmed.com.br
**Repositorio:** https://github.com/oficialmedpro/prime-sync-api
**Supabase:** https://supabase.com/dashboard/project/agdffspstbxeqhqtltvb

---

## 📝 CHANGELOG

### v2.0.0 (24/10/2025)
- ✅ Corrigido erro HTTP 400 em rastreabilidade
- ✅ Corrigido erro SQL em tipos_processo
- ✅ Limpeza completa do projeto (241 arquivos arquivados)
- ✅ Organizacao em pastas (scripts, schemas, docs)
- ✅ Documentacao completa criada
- ✅ Cronjob ativo (30 minutos)

### v1.0.0 (23/10/2025)
- Versao inicial da API
- Sincronizacao basica de clientes, pedidos e formulas

---

**✅ Sistema 100% operacional e sincronizando automaticamente!**
