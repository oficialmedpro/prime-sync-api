# Sistema de Sincronizacao Firebird → Supabase

**Versao:** 3.0.0-FORCADO-AGORA-20250128 | **Status:** ✅ EM PRODUCAO

---

# ⚠️ **ALERTA CRÍTICO - DEPLOY NO EASYPANEL** ⚠️

## 🔴 **PROBLEMA CONHECIDO: EasyPanel NÃO atualiza containers automaticamente!**

O EasyPanel **builda a nova imagem Docker**, mas **NÃO atualiza os containers** para usar a nova imagem. Os containers continuam rodando a imagem antiga, mesmo após múltiplos deploys.

### ✅ **SOLUÇÃO OBRIGATÓRIA - Execute SEMPRE após deploy no EasyPanel:**

**No console do servidor, execute:**

```bash
docker service scale prime-sync-api_prime-sync=0 && \
sleep 5 && \
docker service update --image easypanel/prime-sync-api/prime-sync:latest prime-sync-api_prime-sync --force && \
docker service scale prime-sync-api_prime-sync=1
```

**📖 Documentação completa:** [`SOLUCAO_DEPLOY_EASYPANEL.md`](./SOLUCAO_DEPLOY_EASYPANEL.md)

---

# 🚨 **ALERTA CRÍTICO - LEIA ANTES DE MODIFICAR CÓDIGO** 🚨

## ⚠️ DADOS DE CLIENTES ESTÃO EM 3 TABELAS SEPARADAS NO FIREBIRD! ⚠️

```
❌ ERRO COMUM: SELECT * FROM CLIENTE (telefone e endereço virão NULL!)

✅ CORRETO: Buscar em 3 tabelas:
   1. CLIENTE (dados básicos)
   2. CADASTRO_TELEFONE (WHERE TIPO_CADASTRO = 1)
   3. CADASTRO_ENDERECO (WHERE TIPO_CADASTRO = 1)
```

**📖 LEIA ANTES DE QUALQUER ALTERAÇÃO:**
- **[ESTRUTURA_FIREBIRD_IMPORTANTE.md](./ESTRUTURA_FIREBIRD_IMPORTANTE.md)** ⚠️ OBRIGATÓRIO
- **[sync-api/ALERTA_ESTRUTURA_FIREBIRD.md](./sync-api/ALERTA_ESTRUTURA_FIREBIRD.md)** ⚠️ OBRIGATÓRIO

**Se você esquecer isso:** Clientes serão sincronizados SEM telefone e endereço!

---

## 🚀 INICIO RAPIDO

```bash
# Testar API
curl https://sincro.oficialmed.com.br/health

# Executar sincronizacao
curl https://sincro.oficialmed.com.br/sync

# Verificar dados sincronizados
cd scripts
python verificar_novos_registros.py
```

---

## 📁 ESTRUTURA

```
Banco de Dados Prime/
├── sync-api/              # API em producao
├── scripts/               # Scripts de validacao (10 scripts)
├── schemas/               # Schemas SQL (10 schemas)
├── documentacao_final/    # 📄 DOCUMENTACAO COMPLETA
└── _ARCHIVE/              # Backups (241 arquivos)
```

---

## 📖 DOCUMENTACAO

**Acesse a pasta [documentacao_final/](./documentacao_final/) para:**

- 📄 **DOCUMENTACAO_FINAL.md** - Documentacao tecnica completa
- 📄 **README.md** - Guia detalhado de uso
- 📄 **ARQUIVOS_PARA_REMOVER.md** - Lista de arquivos removidos
- 📄 **log_limpeza_*.txt** - Log da limpeza do projeto

---

## 📊 DADOS SINCRONIZADOS

| Tabela | Total |
|--------|-------|
| Clientes | 37,271 |
| Pedidos | 16,844 |
| Formulas | 32,402 |
| Itens | 348,280 |
| Rastreabilidade | 208,902 |

**Sincronizacao automatica:** A cada 30 minutos

---

## 🔗 LINKS

- **API:** https://sincro.oficialmed.com.br
- **GitHub:** https://github.com/oficialmedpro/prime-sync-api
- **Supabase:** https://supabase.com/dashboard/project/agdffspstbxeqhqtltvb

---

**✅ Sistema 100% operacional!**
