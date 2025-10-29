# LISTA DE ARQUIVOS QUE PODEM SER REMOVIDOS

**Data:** 24/10/2025
**Total de arquivos analisados:** ~250
**Arquivos que podem ser removidos:** ~150

---

## ⚠️ IMPORTANTE - LEIA ANTES DE DELETAR!

Esta lista contem arquivos de **TESTE, DESENVOLVIMENTO e TEMPORARIOS** que nao sao mais necessarios.

**Todos os arquivos da pasta `sync-api/` devem ser MANTIDOS!** ⭐

---

## 🗑️ ARQUIVOS SEGUROS PARA REMOVER

### 1. SCRIPTS DE TESTE (38 arquivos)

Podem ser removidos com seguranca:

```
teste_10_formulas_itens.py
teste_10_formulas_itens_corrigido.py
teste_10_itens_formulas_join.py
teste_api_supabase.py
teste_atendimento_a3.py
teste_banco_nuvem.py
teste_conexao.py
teste_conexao_correta.py
teste_conexao_supabase.py
teste_conexoes.py
teste_dados_firebird.py
teste_exportar_pedidos.py
teste_formula_simples.py
teste_insercao_correta.py
teste_insercao_pedido.py
teste_pedidos_final.py
teste_pedidos_simples.py
teste_rapido.py
teste_rastreabilidade.py
teste_supabase_simples.py
teste_upsert_supabase.py
testar_leitura_firebird.py
check_quick.py
check_status.py
```

### 2. ARQUIVOS SQL DE TESTE (25 arquivos)

```
teste_acesso_tabelas.sql
teste_basico.sql
teste_conexao_nuvem.sql
teste_firebird_simples.sql
teste_leads_ajustado.sql
teste_leads_disponiveis.sql
teste_leads_simples.sql
teste_permissoes.sql
teste_simples.sql
teste_view_clientes.sql
validacao_simples.sql
```

### 3. SCRIPTS DE EXPORTACAO ANTIGOS (30 arquivos)

Estes scripts foram substituidos pela API em producao:

```
export_to_supabase.py
export_to_supabase_nuvem.py
exportar_clientes_completo.py
exportar_clientes_correto.py
exportar_clientes_corrigido_schema.py
exportar_clientes_final.py
exportar_clientes_rapido_batch.py
exportar_firebird_supabase_final.py
exportar_formulas.py
exportar_formulas_itens.py
exportar_formulas_novo.py
exportar_formulas_otimizado.py
exportar_mapeamento_correto.py
exportar_orcamentos_com_status.py
exportar_outras_tabelas.py
exportar_para_supabase_completo.py
exportar_para_supabase_prime.py
exportar_paralelo.py
exportar_pedidos.py
exportar_pedidos_otimizado.py
exportar_rastreabilidade_novo.py
exportar_rastreabilidade_otimizado.py
exportar_rastreabilidade_super_rapido.py
```

### 4. SCRIPTS DE EXECUCAO ANTIGOS (12 arquivos)

```
atualizar_clientes_completos.py
atualizar_formulas_itens.py
atualizar_formulas_textorotulo.py
atualizar_sql_direto.py
atualizar_todos_completos.py
atualizar_todos_sql.py
executar_atualizacao_clientes.py
executar_automatico.py
executar_lotes_500.py
executar_migracao_completa.py
executar_migracao_completa_formulas.py
executar_migracao_mcp.py
executar_todos_automatico.py
executar_todos_sqls.py
```

### 5. SCRIPTS DE MIGRACAO ANTIGOS (8 arquivos)

```
gerar_migracao_completa.py
gerar_sql_updates.py
migrar_formulas_completo_cache.py
migrar_formulas_itens_completa.py
migrar_formulas_itens_mcp.py
migrar_itens_formulas_completo_cache.py
migrar_restantes.py
```

### 6. MIGRACAO SQL EM LOTES (28 arquivos)

Estes arquivos foram gerados automaticamente durante migracoes antigas:

```
migracao_lote_001.sql
migracao_lote_002.sql
migracao_lote_003.sql
...
migracao_lote_028.sql
```

### 7. SCRIPTS DE ANALISE (15 arquivos)

```
analisar_atendimento_a1.sql
analisar_atendimento_a2.sql
analisar_cidadeestado.sql
analisar_clientes.sql
analisar_formulamanipulacao.sql
analisar_formulas.sql
analisar_status_finalizacao.sql
analisar_status_orcamentos.sql
analise_orcamentos_aprovados.sql
```

### 8. SCRIPTS DE INVESTIGACAO (20 arquivos)

```
descobrir_colunas_reais.py
explorar_estrutura_firebird.py
investigar_campos_cliente.py
investigar_campos_endereco.sql
investigar_estrutura_firebird.py
investigar_oc_rastreabilidade.sql
investigar_orcamentos_detalhado.sql
investigar_rastreabilidade_processos.sql
investigar_status_pedidos.sql
investigar_tabelas_contato.py
investigar_tabelas_endereco_telefone.sql
investigar_tabelas_status.sql
investigar_tabelas_status_producao.sql
```

### 9. SCRIPTS DE BUSCA TEMPORARIOS (18 arquivos)

```
buscar_campos_aviados_aprovados.sql
buscar_clientes_com_dados.py
buscar_clientes_com_email.sql
buscar_clientes_supabase.py
buscar_clientes_teste.py
buscar_dados_completos_lucas.sql
buscar_dados_corretos.py
buscar_dados_lucas.py
buscar_enderecos_corrigido.py
buscar_exemplos_formulas_detalhadas.py
buscar_lote_clientes.py
buscar_lucas_fernandes.sql
buscar_orcamentos_lucas.sql
buscar_orcamentos_lucas_corrigido.sql
buscar_orcamentos_simples.sql
buscar_processos_manipulacao.sql
buscar_status_corrigido.sql
buscar_status_disponiveis.sql
buscar_status_producao.sql
buscar_tabelas_producao.sql
buscar_tipos_processo.sql
```

### 10. SCRIPTS DE VERIFICACAO ANTIGOS (20 arquivos)

MANTER: verificar_novos_registros.py, validar_migracao_completa.py, validar_status_atual.py, verificar_totais_rapido.py

REMOVER:
```
verificar_aprovacao_orcamentos.sql
verificar_atendimento_log.sql
verificar_ativo.sql
verificar_campos_alternativos.sql
verificar_cliente_com_dados.sql
verificar_clientes_estatisticas.sql
verificar_clientes_orcamentos.sql
verificar_criterios.sql
verificar_dados.sql
verificar_dados_clientes.sql
verificar_datas_disponiveis.sql
verificar_estrutura_endereco_telefone.sql
verificar_lucas_completo.sql
verificar_manipulados_lead.sql
verificar_manipulados_lead2.sql
verificar_manipulados_lead3.sql
verificar_manipulados_lucas.sql
verificar_nomes_exatos.sql
verificar_status_mov.sql
verificar_status_ordem_servico.sql
verificar_todos_orcamentos_lucas.sql
verificar_usuario_atual.sql
verificar_views.sql
```

### 11. ARQUIVOS DE DADOS TEMPORARIOS (8 arquivos)

```
dados_12_07_2025.json
dados_12_07_2025.txt
dados_exportacao_teste.txt
dados_gabrielli_henrique_script.json
rastreabilidade_log.txt
exportar_dados_prime/banco_de_dados-prime/extracao_20251021_183000.json
```

### 12. UTILITARIOS ANTIGOS (10 arquivos)

```
config_supabase.py
contar_clientes_disponiveis.py
contar_itens_formulas.py
contar_tabelas.py
continuar_pedidos.py
corrigir_ids_formulas.py
limpar_formulas_itens.py
inserir_via_api_background.py
monitorar_exportacao.py
monitorar_progresso.py
status_exportacao.py
```

### 13. CONSULTAS SQL ANTIGAS (15 arquivos)

```
consulta_agrupada_final.sql
consulta_ajustada.sql
consulta_completa_clientes_pedidos.sql
consulta_dia_12_07_2025.sql
consulta_dia_15_10_2025.sql
consulta_export_supabase.sql
consulta_final_clientes_pedidos.sql
consulta_manipulados.sql
consulta_simples_final.sql
consulta_teste_simples.sql
exemplos_orcamentos_aprovados.sql
exemplos_orcamentos_aprovados_corrigido.sql
exemplos_orcamentos_nao_aprovados.sql
exportar_json_automatico.sql
listar_campos_cliente.sql
listar_tabelas.sql
segmentacao_clientes_rfv.sql
```

### 14. RELATORIOS ANTIGOS (8 arquivos)

```
consulta_final_funcionando.md
relatorio_analise_banco.md
relatorio_exportacao_json.md
relatorio_lucas_fernandes.md
relatorio_orcamentos_aprovados.md
relatorio_teste_banco_nuvem.md
RESUMO_TESTE_FINAL.md
```

### 15. DOCUMENTACAO ANTIGA/DUPLICADA (10 arquivos)

MANTER: DOCUMENTACAO_FINAL.md, sync-api/README.md, sync-api/DEPLOY.md

REMOVER:
```
ARQUITETURA.md
CLAUDE_CODE_COMO_PROSSEGUIR.md
DOCUMENTACAO_COMPLETA_SUPABASE.md
ESTRATEGIA_SEGMENTACAO_CLIENTES.md
GUIA_IMPLEMENTACAO_SUPABASE.md
GUIA_MIGRACAO_FORMULAS_COMPLETAS.md
INICIO_RAPIDO.md
README_EXPORTACAO_SUPABASE.md
```

### 16. PASTA CODIGOCERTO (pode ser removida inteira)

```
CODIGOCERTO/
  ├── 00_GUIA_PASSO_A_PASSO.md
  ├── 01_CONEXOES_CORRETAS.md
  ├── 02_TABELAS_SUPABASE.md
  ├── 03_MAPEAMENTO_FIREBIRD.md
  ├── 04_RESUMO_FINAL_INTEGRACAO.md
  ├── CLAUDE_CODE_COMO_PROSSEGUIR.md
  ├── INDEX.md
  ├── README.md
  ├── RESUMO_EXECUTIVO.md
  ├── ROADMAP_EXPORTACAO.md
  └── teste_final_integracao.py
```

### 17. PASTA exportar_dados_prime (pode ser removida inteira)

```
exportar_dados_prime/
  ├── exportar_leads_completos.py
  ├── gerar_estatisticas.py
  ├── GUIA_EXPORTACAO_DADOS_PRIME.md
  ├── relatorio_dados_prime.md
  └── requirements.txt
```

---

## ✅ ARQUIVOS QUE DEVEM SER MANTIDOS

### Pasta sync-api/ (TODA) ⭐
```
sync-api/
  ├── app.py                      # API principal
  ├── requirements.txt            # Dependencias
  ├── Dockerfile                  # Build Docker
  ├── docker-compose.yml          # Compose local
  ├── stack-portainer.yml         # Stack Portainer
  ├── supabase-cronjob.sql       # Cronjob config
  ├── .github/workflows/
  │   └── docker-build.yml       # CI/CD
  ├── README.md                   # Docs
  ├── DEPLOY.md                   # Guia deploy
  ├── ESTRUTURA.md                # Estrutura
  ├── GUIA_RAPIDO.md             # Guia rapido
  └── SECRETS.md                  # Secrets
```

### Scripts de Validacao ⭐
```
verificar_novos_registros.py      # Validacao principal
validar_migracao_completa.py      # Validacao completa
validar_status_atual.py           # Status atual
verificar_totais_rapido.py        # Comparacao rapida
verificar_estrutura_a2.py         # Estrutura A2
verificar_estruturas_tabelas.py   # Estruturas
verificar_codigos_maximos.py      # Codigos maximos
verificar_status.py               # Status geral
verificar_tabelas_supabase.py     # Tabelas Supabase
validar_scripts_teste.py          # Scripts de teste
```

### Schemas SQL ⭐
```
sql_supabase_rastreabilidade_completo.sql   # Schema principal
supabase_schema.sql                          # Schema alternativo
supabase_schema_prime.sql                    # Schema prime
ajustar_tabelas_supabase.sql                # Ajustes
corrigir_permissoes_sequencias.sql          # Permissoes
sql_criar_tabela_formulas_itens.sql         # Formulas itens
sql_permissoes_prime_formulas_itens.sql     # Permissoes itens
sql_supabase_api.sql                         # API SQL
sql_supabase_api_atualizado.sql             # API atualizada
sql_updates_clientes.sql                     # Updates clientes
```

### Documentacao ⭐
```
DOCUMENTACAO_FINAL.md            # Documentacao completa
ARQUIVOS_PARA_REMOVER.md         # Esta lista
```

### Requirements ⭐
```
requirements.txt                  # Dependencias principais
requirements_export_supabase.txt  # Export supabase
requirements_supabase.txt         # Supabase
```

---

## 🚀 COMO REMOVER OS ARQUIVOS

### Opcao 1: Manual (Mais Seguro)

1. Leia esta lista com atencao
2. Delete arquivo por arquivo
3. Confirme que nao deletou nada da pasta `sync-api/`

### Opcao 2: Script Python (Rapido)

Vou criar um script que remove tudo automaticamente com backup.

### Opcao 3: Mover para pasta ARCHIVE

Mais seguro - move arquivos para uma pasta de backup antes de deletar.

---

## 📊 RESUMO

**Total de arquivos no projeto:** ~250
**Arquivos essenciais:** ~40
**Arquivos que podem ser removidos:** ~150
**Economia de espaco estimada:** 50-70%

**Arquivos por categoria:**
- ✅ Manter: 40 arquivos (~16%)
- 🗑️ Remover: 150 arquivos (~60%)
- ⚠️ Revisar: 60 arquivos (~24%)

---

**Quer que eu crie um script para remover automaticamente com backup?**
