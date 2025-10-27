# 📁 Lista de Arquivos do Projeto sync-api

**Atualizado em:** 27/10/2025  
**Projeto:** Sincronização Prime/Firebird → Supabase

---

## 📄 Arquivos Principais

### **Código Fonte**

| Arquivo | Descrição | Linhas | Tecnologia |
|---------|-----------|--------|------------|
| `app.py` | Script principal da API Flask de sincronização. Contém todas as funções de sync (clientes, pedidos, fórmulas, rastreabilidade, tipos_processo). Executa a cada 30 min via cronjob. | 840 | Python 3.11 + Flask |
| `requirements.txt` | Dependências Python necessárias (Flask, fdb, requests, etc) | - | pip |

### **Deploy e Infraestrutura**

| Arquivo | Descrição |
|---------|-----------|
| `Dockerfile` | Imagem Docker baseada em Python 3.11-slim com bibliotecas Firebird |
| `docker-compose.yml` | Configuração local do Docker Compose (desenvolvimento) |
| `stack-portainer.yml` | Stack de produção para Docker Swarm via Portainer. Define secrets, networks, recursos e labels Traefik |
| `stack-portainer-novo.yml` | Versão atualizada da stack (backup/teste) |

### **Documentação**

| Arquivo | Descrição |
|---------|-----------|
| `README.md` | Documentação geral do projeto |
| `DEPLOY.md` | Instruções de deploy no Docker Swarm/Portainer |
| `ESTRUTURA.md` | Estrutura de pastas e arquitetura |
| `GUIA_RAPIDO.md` | Guia rápido de comandos úteis |
| `GITHUB_SETUP.md` | Configuração do repositório GitHub |
| `SECRETS.md` | Documentação sobre Docker Secrets |
| `DOCUMENTACAO_FINAL.md` | Documentação consolidada do projeto |

---

## 🔧 Arquivos de Correção (27/10/2025)

### **Scripts SQL de Correção**

| Arquivo | Função | Uso |
|---------|--------|-----|
| `corrigir_cliente_corrompido.sql` | Deleta registro com `codigo_cliente_original = 9999999` que estava impedindo a sincronização de clientes | Executar 1x no Supabase SQL Editor |
| `corrigir_tipos_processo_duplicados.sql` | Remove registros duplicados da tabela `prime_tipos_processo` (resolve HTTP 409) | Executar 1x no Supabase SQL Editor |
| `verificar_todas_tabelas.sql` | Dashboard SQL completo mostrando status de sincronização de todas as tabelas (total, último código, inserções 24h/7dias) | Executar sempre que precisar verificar status |

### **Documentação de Diagnóstico**

| Arquivo | Função |
|---------|--------|
| `INSTRUCOES_CORRECAO.md` | Passo a passo detalhado para executar a correção. Inclui comandos Docker, queries SQL, troubleshooting e checklist final |
| `RESUMO_DIAGNOSTICO_27-10-2025.md` | Análise técnica completa: problema, causa raiz, solução, validação, prevenção e recomendações |
| `LISTA_ARQUIVOS_PROJETO.md` | Este arquivo - índice de todos os arquivos do projeto |

---

## 🗄️ Schemas e Estruturas

### **SQL Schemas**

| Arquivo | Descrição |
|---------|-----------|
| `supabase-cronjob.sql` | Configuração do cronjob no PostgreSQL (pg_cron extension) |

---

## 🧪 Scripts de Teste e Análise

### **Testes de Conexão Firebird**

| Arquivo | Função |
|---------|--------|
| `encontrar_estoques.py` | Testa queries na tabela ESTOQUE_GERAL |
| `encontrar_nomes_produtos.py` | Busca produtos no Firebird |
| `encontrar_tabela_produtos.py` | Identifica estrutura da tabela de produtos |
| `testar_cotacao_produto.py` | Testa busca de cotações |
| `testar_join_estoque_geral.py` | Testa JOINs complexos |
| `testar_tabelas_produto.py` | Valida estrutura de produtos |
| `teste_atendimento_a3.py` | Testa tabela ATENDIMENTO_A3 (itens de fórmulas) |
| `teste_estrutura_tabela.py` | Verifica estrutura de tabelas Firebird |
| `teste_join_produto.py` | Testa relacionamentos de produtos |

---

## 📂 Estrutura de Pastas

```
sync-api/
├── app.py                          # ← Script principal
├── requirements.txt                # ← Dependências
├── Dockerfile                      # ← Build da imagem
├── docker-compose.yml              # ← Compose local
├── stack-portainer.yml             # ← Stack produção
├── stack-portainer-novo.yml        # ← Stack backup
├── supabase-cronjob.sql            # ← Cronjob config
│
├── DEPLOY.md                       # ← Docs de deploy
├── ESTRUTURA.md                    # ← Arquitetura
├── GUIA_RAPIDO.md                  # ← Comandos úteis
├── README.md                       # ← Readme geral
├── DOCUMENTACAO_FINAL.md           # ← Documentação consolidada
├── GITHUB_SETUP.md                 # ← Setup Git
├── SECRETS.md                      # ← Docs secrets
│
├── corrigir_cliente_corrompido.sql           # ← Correção clientes
├── corrigir_tipos_processo_duplicados.sql    # ← Correção tipos
├── verificar_todas_tabelas.sql               # ← Dashboard SQL
├── INSTRUCOES_CORRECAO.md                    # ← Passo a passo
├── RESUMO_DIAGNOSTICO_27-10-2025.md          # ← Análise técnica
├── LISTA_ARQUIVOS_PROJETO.md                 # ← Este arquivo
│
├── encontrar_*.py                  # ← Testes Firebird
├── testar_*.py                     # ← Testes diversos
├── teste_*.py                      # ← Testes diversos
│
└── src/                            # ← (Vazio por enquanto)
    ├── config/
    ├── routes/
    ├── services/
    └── utils/
```

---

## 🔑 Arquivos de Configuração (Não versionados)

### **Secrets Docker (Portainer)**

Armazenados no Docker Swarm:
- `PRIME_FIREBIRD_HOST` → Host do Firebird
- `PRIME_FIREBIRD_DB` → Nome do banco
- `PRIME_FIREBIRD_USER` → Usuário
- `PRIME_FIREBIRD_PASS` → Senha
- `PRIME_SUPABASE_URL` → URL da API Supabase
- `PRIME_SUPABASE_KEY` → Service Role Key

### **Variáveis de Ambiente**

```env
NODE_ENV=production
PORT=5000
API_TOKEN=prime-sync-2025-xY9kL2mP4nQ8wR5t
```

---

## 📊 Mapeamento de Tabelas

### **Firebird → Supabase**

| Tabela Firebird | Tabela Supabase | Função Python | Status |
|-----------------|-----------------|---------------|--------|
| CLIENTE | prime_clientes | `sync_clientes_novos()` | ✅ Corrigido |
| ATENDIMENTO_A1 | prime_pedidos | `sync_pedidos_novos()` | ✅ OK |
| ATENDIMENTO_A2 | prime_formulas | `sync_formulas_novas()` | ✅ OK |
| ATENDIMENTO_A3 | prime_formulas_itens | `sync_formulas_itens_novos()` | ✅ OK |
| PROCESSO_MANIPULACAO | prime_rastreabilidade | `sync_rastreabilidade_nova()` | ✅ OK |
| FORMAFARMACEUTICA_PROCESSO_TIPO | prime_tipos_processo | `sync_tipos_processo_novos()` | ✅ Corrigido |

---

## 🚀 Comandos Úteis

### **Build e Deploy**

```bash
# Build local
docker build -t oficialmedpro/prime-sync-api:latest .

# Push para registry
docker push oficialmedpro/prime-sync-api:latest

# Deploy via Portainer
# (UI: Stacks → prime-sync-api → Update)

# Deploy via CLI
docker stack deploy -c stack-portainer.yml prime-sync-api
```

### **Logs e Monitoramento**

```bash
# Ver logs em tempo real
docker service logs prime-sync-api_prime-sync-api --follow

# Ver últimas 100 linhas
docker service logs prime-sync-api_prime-sync-api --tail 100

# Filtrar erros
docker service logs prime-sync-api_prime-sync-api | grep ERROR
```

### **Teste Local**

```bash
# Executar localmente
python app.py

# Testar endpoint
curl http://localhost:5000/sync
curl http://localhost:5000/health
```

---

## 📝 Histórico de Alterações

### **27/10/2025 - Correção de Sincronização**

**Problema:** Clientes não sincronizando há 4 dias

**Arquivos criados:**
- `corrigir_cliente_corrompido.sql`
- `corrigir_tipos_processo_duplicados.sql`
- `verificar_todas_tabelas.sql`
- `INSTRUCOES_CORRECAO.md`
- `RESUMO_DIAGNOSTICO_27-10-2025.md`
- `LISTA_ARQUIVOS_PROJETO.md`

**Causa:** Registro com `codigo_cliente_original = 9999999` impedindo sincronização

**Solução:** Scripts SQL para deletar registro corrompido e duplicatas

---

## 🔗 Links Úteis

- **API Produção:** https://sincro.oficialmed.com.br
- **Portainer:** https://portainer.oficialmed.com.br
- **Supabase Dashboard:** https://supabase.com/dashboard/project/[projeto]
- **Documentação Firebird:** https://firebirdsql.org/
- **Documentação Supabase:** https://supabase.com/docs

---

## ✅ Checklist de Manutenção Semanal

- [ ] Executar `verificar_todas_tabelas.sql` no Supabase
- [ ] Verificar se todas as tabelas têm registros nas últimas 24h
- [ ] Revisar logs do container para erros
- [ ] Confirmar que não há HTTP 409 ou outros erros
- [ ] Validar que códigos máximos estão crescendo

---

_Este documento é atualizado sempre que novos arquivos são criados ou modificados no projeto._

**Última atualização:** 27/10/2025 - Adicionados scripts de correção de sincronização

