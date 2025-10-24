# Documentacao Final - API de Sincronizacao Firebird -> Supabase

**Versao:** 2.0.0
**Data:** 24/10/2025
**Projeto:** Oficialmed - Sincronizacao Incremental Prime

---

## 1. VISAO GERAL

API Flask que realiza sincronizacao incremental de dados do banco Firebird (Prime Software) para o Supabase (PostgreSQL).

### 1.1 Tecnologias
- **Backend:** Flask 3.0.0
- **Database Origem:** Firebird (fdb 2.0.2)
- **Database Destino:** Supabase (PostgreSQL via REST API)
- **Deploy:** Docker + Portainer
- **Servidor:** https://sincro.oficialmed.com.br

---

## 2. ESTRUTURA DO PROJETO

```
sync-api/
├── app.py                          # Aplicacao principal Flask
├── requirements.txt                # Dependencias Python
├── Dockerfile                      # Container Docker
├── docker-compose.yml              # Compose local
├── stack-portainer.yml             # Stack Portainer (producao)
├── .env.example                    # Exemplo de variaveis de ambiente
├── README.md                       # Documentacao basica
├── DEPLOY.md                       # Guia de deploy
├── ESTRUTURA.md                    # Estrutura de tabelas
├── GUIA_RAPIDO.md                  # Guia rapido
├── SECRETS.md                      # Configuracao de secrets
├── GITHUB_SETUP.md                 # Setup GitHub Actions
└── supabase-cronjob.sql           # Cronjob Supabase
```

---

## 3. FUNCIONALIDADES

A API sincroniza 6 tipos de entidades:

### 3.1 Clientes (`sync_clientes_novos`)
- **Tabela Firebird:** `CLIENTE` + `CIDADEESTADO`
- **Tabela Supabase:** `prime_clientes`
- **Criterio:** `C.CODIGO > ultimo_codigo` AND `ATIVO = -1`
- **Limite:** 1000 registros/execucao

### 3.2 Pedidos (`sync_pedidos_novos`)
- **Tabela Firebird:** `ATENDIMENTO_A1`
- **Tabela Supabase:** `prime_pedidos`
- **Criterio:** `A.CODIGO > ultimo_codigo`
- **Limite:** 1000 registros/execucao
- **Dependencia:** Requer cliente ja sincronizado

### 3.3 Formulas (`sync_formulas_novas`)
- **Tabela Firebird:** `ATENDIMENTO_A2`
- **Tabela Supabase:** `prime_formulas`
- **Criterio:** `A2.CODIGO_ATEND_A1 > ultimo_codigo`
- **Limite:** 2000 registros/execucao
- **Campo Chave:** `TEXTOROTULO` (descricao completa da formula)

### 3.4 Itens de Formula (`sync_formulas_itens_novos`)
- **Tabela Firebird:** `ATENDIMENTO_A3` + `ESTOQUE_GERAL`
- **Tabela Supabase:** `prime_formulas_itens`
- **Criterio:** `A3.CODIGO_ATEND_A1 > ultimo_codigo`
- **Limite:** 1000 registros/execucao

### 3.5 Rastreabilidade (`sync_rastreabilidade_nova`)
- **Tabela Firebird:** `PROCESSO_MANIPULACAO`
- **Tabela Supabase:** `prime_rastreabilidade`
- **Criterio:** `PM.CODIGO > ultimo_codigo`
- **Limite:** 1000 registros/execucao

### 3.6 Tipos de Processo (`sync_tipos_processo_novos`)
- **Tabela Firebird:** `FORMAFARMACEUTICA_PROCESSO_TIPO`
- **Tabela Supabase:** `prime_tipos_processo`
- **Criterio:** `FPT.CODIGO > ultimo_codigo`
- **Limite:** 1000 registros/execucao

---

## 4. ENDPOINTS DA API

### 4.1 GET/POST `/health`
Verifica se a API esta ativa.

**Resposta:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-24T21:44:21.986742",
  "version": "2.0.0"
}
```

### 4.2 GET/POST `/sync`
Executa sincronizacao incremental de todas as entidades.

**Resposta (exemplo):**
```json
{
  "sucesso": true,
  "timestamp": "2025-10-24T21:44:32.219329",
  "tempo_execucao_segundos": 1.672684,
  "version": "2.0.0",
  "clientes": {
    "inseridos": 0,
    "mensagem": "Nenhum cliente novo"
  },
  "pedidos": {
    "inseridos": 0,
    "mensagem": "Nenhum pedido novo"
  },
  "formulas": {
    "inseridos": 0,
    "mensagem": "Nenhuma formula nova"
  },
  "formulas_itens": {
    "inseridos": 0,
    "mensagem": "Nenhum item novo"
  },
  "rastreabilidade": {
    "inseridos": 0,
    "erro": "HTTP 400"
  },
  "tipos_processo": {
    "inseridos": 0,
    "erro": "Column unknown - FPT.TIPO"
  },
  "total_inseridos": 0
}
```

---

## 5. CONFIGURACAO

### 5.1 Variaveis de Ambiente

```env
# Firebird
FIREBIRD_HOST=db.primesoftware.com.br
FIREBIRD_DB=oficialmed1250
FIREBIRD_USER=OFICIALMED
FIREBIRD_PASS=<senha_secreta>

# Supabase
SUPABASE_URL=https://agdffspstbxeqhqtltvb.supabase.co
SUPABASE_KEY=<service_role_key>

# API
API_TOKEN=prime-sync-2025
PORT=5000
```

### 5.2 Secrets (Producao)
No Portainer, configurar como Docker Secrets:
- `firebird_pass`
- `supabase_key`
- `api_token`

---

## 6. DEPLOY

### 6.1 Local (Docker Compose)
```bash
cd sync-api
docker-compose up -d
```

### 6.2 Producao (Portainer)
1. Criar secrets no Portainer
2. Importar `stack-portainer.yml`
3. Deploy da stack

### 6.3 Automacao (GitHub Actions)
Push para `main` → Build automatico → Deploy via webhook

---

## 7. TESTES

### 7.1 Teste Manual
```bash
# Health check
curl https://sincro.oficialmed.com.br/health

# Sincronizacao
curl https://sincro.oficialmed.com.br/sync
```

### 7.2 Scripts de Teste Incluidos
- `teste_atendimento_a3.py` - Testa tabela A3
- `teste_join_produto.py` - Testa join com produtos
- `testar_cotacao_produto.py` - Testa cotacao
- `encontrar_estoques.py` - Verifica estoques
- `encontrar_nomes_produtos.py` - Busca nomes de produtos
- `teste_estrutura_tabela.py` - Verifica estrutura de tabelas

---

## 8. ERROS CONHECIDOS

### 8.1 Rastreabilidade - HTTP 400
**Erro:** `{"rastreabilidade": {"erro": "HTTP 400", "inseridos": 0}}`

**Causa Provavel:**
- Schema Supabase incompativel com dados enviados
- Campos obrigatorios faltando
- Tipos de dados incorretos

**Solucao:**
1. Verificar schema da tabela `prime_rastreabilidade` no Supabase
2. Validar campos obrigatorios
3. Ajustar mapeamento de dados

### 8.2 Tipos Processo - Column Unknown
**Erro:** `Column unknown - FPT.TIPO - At line 6, column 21`

**Causa:**
Versao em producao do `app.py` esta desatualizada e tenta acessar coluna `FPT.TIPO` que nao existe.

**Colunas Corretas da Tabela:**
```
CODIGO, TIPO_MOVIMENTO, NOMETIPO, NOMEFICHA, TIPO_PRODUCAO, TIPO_INCLUSAO,
PAGARCOMISSAO, REGISTRAR_BAIXA, SEQUENCIA, BLOQUEAR_CALCULO, PROCESSO_OPCIONAL,
ATIVO, CADASTRO_LJ, CADASTRO_DT, CADASTRO_CF, ALTERACAO_LJ, ALTERACAO_DT,
ALTERACAO_CF, OBSERVACAO, BLOQUEIO_BAIXA, LIBERAR_ENTREGA, BLOQUEAR_RECEITA, MSG_OMNI
```

**Solucao:**
1. Fazer redeploy do `app.py` atualizado
2. Verificar se codigo em producao corresponde ao repositorio

---

## 9. MONITORAMENTO

### 9.1 Logs
```bash
docker logs sync-api-container
```

### 9.2 Metricas
- Tempo de execucao (campo `tempo_execucao_segundos`)
- Total de registros inseridos por entidade
- Erros por tipo

---

## 10. MANUTENCAO

### 10.1 Atualizacao de Codigo
```bash
git pull origin main
docker-compose down
docker-compose up -d --build
```

### 10.2 Backup
- Dados Firebird: gerenciado pelo Prime Software
- Dados Supabase: backups automaticos do Supabase

### 10.3 Cronjob
Configurado no Supabase para executar `/sync` periodicamente:
```sql
-- Ver supabase-cronjob.sql
```

---

## 11. CONTATOS

- **Desenvolvedor:** [Seu Nome]
- **Cliente:** Oficialmed
- **Suporte Prime:** db.primesoftware.com.br

---

## 12. HISTORICO DE VERSOES

### v2.0.0 (Atual)
- Adicao de `prime_formulas_itens` (ATENDIMENTO_A3)
- Campo `TEXTOROTULO` para formulas completas
- Sincronizacao de rastreabilidade
- Tipos de processo

### v1.0.0
- Versao inicial
- Clientes, Pedidos, Formulas

---

## 13. PROXIMOS PASSOS

- [ ] Corrigir erro HTTP 400 em rastreabilidade
- [ ] Fazer redeploy para corrigir erro de tipos_processo
- [ ] Adicionar autenticacao por token nos endpoints
- [ ] Implementar retry automatico em caso de falha
- [ ] Dashboard de monitoramento
- [ ] Alertas por email em caso de erro

---

**Documentacao gerada em:** 24/10/2025
**Ultima atualizacao:** app.py linha 805
