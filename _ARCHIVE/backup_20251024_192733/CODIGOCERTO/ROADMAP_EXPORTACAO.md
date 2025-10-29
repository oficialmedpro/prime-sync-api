# 🗺️ ROADMAP - Exportação Prime → Supabase

## 📅 CRONOGRAMA RECOMENDADO

### ⏰ DIA 1 - Preparação e Teste (1-2 horas)

#### 🌅 MANHÃ (9h-10h)
- [ ] **9:00 - 9:15** - Verificar instalação do Python
- [ ] **9:15 - 9:30** - Instalar dependências (fdb, supabase)
- [ ] **9:30 - 9:45** - Criar schema no Supabase
- [ ] **9:45 - 10:00** - Testar conexões

#### 🌞 MANHÃ (10h-11h)
- [ ] **10:00 - 10:30** - Executar exportação de teste (apenas tipos_processo e 100 clientes)
- [ ] **10:30 - 11:00** - Validar dados exportados
- [ ] **11:00 - 11:30** - Revisar logs e corrigir eventuais problemas

#### 🍽️ ALMOÇO (12h-13h)

#### 🌤️ TARDE (14h-16h)
- [ ] **14:00 - 15:00** - Executar exportação completa
- [ ] **15:00 - 15:30** - Validar todos os dados exportados
- [ ] **15:30 - 16:00** - Criar primeiras queries e dashboards

---

## 📋 CHECKLIST DETALHADO

### ✅ FASE 1: PRÉ-REQUISITOS (15 min)

```
┌─────────────────────────────────────────┐
│ □ Python 3.12+ instalado                │
│ □ pip funcionando                       │
│ □ Acesso ao Firebird                    │
│ □ Acesso ao Supabase                    │
│ □ Arquivos do projeto disponíveis      │
└─────────────────────────────────────────┘
```

**Comando de verificação:**
```powershell
python --version
pip --version
```

---

### ✅ FASE 2: INSTALAÇÃO (15 min)

```
┌─────────────────────────────────────────┐
│ □ Navegar para pasta do projeto        │
│ □ Instalar fdb                          │
│ □ Instalar supabase                     │
│ □ Instalar python-dotenv                │
│ □ Instalar requests                     │
│ □ Verificar instalações                 │
└─────────────────────────────────────────┘
```

**Comando único:**
```powershell
cd "C:\Users\User\Documents\Banco de Dados Prime"
pip install fdb supabase python-dotenv requests
```

---

### ✅ FASE 3: CONFIGURAÇÃO DO SUPABASE (15 min)

```
┌─────────────────────────────────────────┐
│ □ Acessar dashboard Supabase            │
│ □ Abrir SQL Editor                      │
│ □ Executar script de schema             │
│ □ Verificar criação das 5 tabelas      │
│ □ Verificar criação das 3 views        │
│ □ Testar permissões RLS                 │
└─────────────────────────────────────────┘
```

**Query de verificação:**
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'api' 
  AND table_name LIKE 'prime_%';
```

---

### ✅ FASE 4: TESTE DE CONEXÕES (5 min)

```
┌─────────────────────────────────────────┐
│ □ Executar teste_conexao_correta.py    │
│ □ Verificar conexão Firebird OK        │
│ □ Verificar conexão Supabase OK        │
│ □ Confirmar contadores de dados        │
└─────────────────────────────────────────┘
```

**Comando:**
```powershell
python teste_conexao_correta.py
```

**Resultado esperado:**
```
✅ Firebird conectado! XXX clientes ativos encontrados
✅ Supabase conectado via API!
🎉 Todas as conexões estão funcionando!
```

---

### ✅ FASE 5: EXPORTAÇÃO DE TESTE (30 min)

```
┌─────────────────────────────────────────┐
│ □ Modificar script para teste           │
│ □ Exportar apenas 100 clientes         │
│ □ Exportar pedidos desses clientes     │
│ □ Verificar dados no Supabase          │
│ □ Validar integridade                   │
└─────────────────────────────────────────┘
```

**Para teste limitado, modificar temporariamente:**
```python
# Em exportar_firebird_supabase_final.py
# Linha ~289, alterar para:
ROWS 1 TO 100  # ao invés de ROWS {limite} TO {offset + limite}
```

---

### ✅ FASE 6: EXPORTAÇÃO COMPLETA (30-60 min)

```
┌─────────────────────────────────────────┐
│ □ Restaurar script original             │
│ □ Executar exportação completa          │
│ □ Acompanhar progresso em tempo real   │
│ □ Não interromper o processo           │
│ □ Aguardar mensagem de conclusão       │
└─────────────────────────────────────────┘
```

**Comando:**
```powershell
python exportar_firebird_supabase_final.py
```

**Monitorar:**
- Console para progresso em tempo real
- `export_firebird_supabase.log` para detalhes

---

### ✅ FASE 7: VALIDAÇÃO COMPLETA (20 min)

```
┌─────────────────────────────────────────┐
│ □ Contar registros por tabela           │
│ □ Verificar integridade referencial     │
│ □ Testar views de análise               │
│ □ Verificar dados de exemplo            │
│ □ Comparar totais com Firebird          │
│ □ Revisar logs em busca de erros       │
└─────────────────────────────────────────┘
```

**Queries essenciais:**
```sql
-- 1. Contar registros
SELECT 'prime_clientes' as tabela, COUNT(*) FROM api.prime_clientes
UNION ALL SELECT 'prime_pedidos', COUNT(*) FROM api.prime_pedidos
UNION ALL SELECT 'prime_tipos_processo', COUNT(*) FROM api.prime_tipos_processo
UNION ALL SELECT 'prime_rastreabilidade', COUNT(*) FROM api.prime_rastreabilidade
UNION ALL SELECT 'prime_formulas', COUNT(*) FROM api.prime_formulas;

-- 2. Verificar integridade
SELECT COUNT(*) as pedidos_sem_cliente
FROM api.prime_pedidos p
LEFT JOIN api.prime_clientes c ON p.cliente_id = c.id
WHERE c.id IS NULL;
-- Deve retornar 0

-- 3. Testar view RFV
SELECT * FROM api.vw_prime_clientes_rfv 
ORDER BY score_rfv_calculado DESC 
LIMIT 10;
```

---

## 🎯 METAS DE SUCESSO

### 🟢 Critérios de Sucesso (OBRIGATÓRIOS)

- [ ] **5 tabelas criadas** no Supabase
- [ ] **3 views criadas** e funcionando
- [ ] **Todos os clientes ativos** exportados
- [ ] **Todos os pedidos aprovados** exportados
- [ ] **Rastreabilidade completa** de processos
- [ ] **Zero erros** no log final
- [ ] **Integridade referencial** mantida (0 registros órfãos)
- [ ] **Tempo de exportação** < 90 minutos

### 🔵 Critérios Desejáveis (OPCIONAL)

- [ ] Dashboards básicos criados
- [ ] Queries de relatório testadas
- [ ] API REST testada
- [ ] Exportação automatizada configurada
- [ ] Documentação atualizada com observações

---

## ⚠️ PONTOS DE ATENÇÃO

### 🔴 CRÍTICO - NÃO PROSSEGUIR SE:

1. **Teste de conexões falhar**
   - ❌ PARAR e corrigir conexões
   - ✅ Só prosseguir com ambas OK

2. **Schema não for criado corretamente**
   - ❌ PARAR e recriar schema
   - ✅ Só prosseguir com 5 tabelas + 3 views

3. **Teste de exportação tiver muitos erros**
   - ❌ PARAR e revisar configurações
   - ✅ Só exportação completa com teste OK

### 🟡 ATENÇÃO - MONITORAR:

1. **Logs de erro durante exportação**
   - Alguns retries são normais (⚠️)
   - Muitos erros indicam problema (❌)

2. **Performance**
   - Se muito lento (> 90 min), reduzir batch_size
   - Se memória alta, reiniciar em lotes menores

3. **Integridade de dados**
   - Sempre validar totais com origem
   - Verificar registros órfãos

---

## 📊 ORDEM DE EXECUÇÃO DOS DADOS

### Ordem OBRIGATÓRIA (não alterar):

```
1️⃣ prime_tipos_processo
    ↓
2️⃣ prime_clientes
    ↓
3️⃣ prime_pedidos (depende de clientes)
    ↓
4️⃣ prime_rastreabilidade (depende de pedidos e tipos)
    ↓
5️⃣ prime_formulas (depende de pedidos)
```

**Razão:** Integridade referencial (foreign keys)

---

## 💾 ESTIMATIVA DE VOLUME DE DADOS

### Baseado no banco atual:

| Tabela | Estimativa | Tempo |
|--------|------------|-------|
| `prime_tipos_processo` | ~15 registros | < 1 min |
| `prime_clientes` | ~5.000 registros | ~5 min |
| `prime_pedidos` | ~15.000 registros | ~10 min |
| `prime_rastreabilidade` | ~50.000 registros | ~15 min |
| `prime_formulas` | ~25.000 registros | ~10 min |
| **TOTAL** | **~95.000 registros** | **~40 min** |

*Valores aproximados baseados em dados típicos*

---

## 🚨 PLANO DE ROLLBACK (EM CASO DE PROBLEMAS)

### Se algo der errado DURANTE a exportação:

1. **Interromper o script:** `Ctrl + C`
2. **Revisar logs:** Identificar erro
3. **Corrigir problema:** Conexão, configuração, etc.
4. **Limpar dados parciais:**
   ```sql
   TRUNCATE api.prime_rastreabilidade CASCADE;
   TRUNCATE api.prime_formulas CASCADE;
   TRUNCATE api.prime_pedidos CASCADE;
   TRUNCATE api.prime_clientes CASCADE;
   TRUNCATE api.prime_tipos_processo CASCADE;
   ```
5. **Reexecutar:** `python exportar_firebird_supabase_final.py`

### Se algo der errado APÓS a exportação:

1. **Não deletar dados imediatamente**
2. **Identificar problema específico**
3. **Corrigir apenas dados problemáticos:**
   ```sql
   DELETE FROM api.prime_clientes 
   WHERE codigo_cliente_original = XXX;
   ```
4. **Reexportar registro específico** (ou todos com UPSERT)

---

## 📞 CONTATOS EMERGENCIAIS

### Em caso de problemas:

1. **Documentação:** Pasta `CODIGOCERTO/`
2. **Logs:** `export_firebird_supabase.log`
3. **Troubleshooting:** `00_GUIA_PASSO_A_PASSO.md` seção "Troubleshooting"

### Informações para suporte:

- [ ] Versão do Python
- [ ] Sistema Operacional
- [ ] Mensagem de erro exata
- [ ] Últimas linhas do log
- [ ] Passo onde ocorreu o erro

---

## ✅ CHECKLIST FINAL PÓS-EXPORTAÇÃO

```
┌─────────────────────────────────────────────────────────┐
│  VALIDAÇÃO FINAL                                        │
├─────────────────────────────────────────────────────────┤
│  □ Exportação concluída sem erros                      │
│  □ Todas as 5 tabelas têm dados                        │
│  □ Totais conferem com origem                          │
│  □ Integridade referencial OK                          │
│  □ Views funcionando                                   │
│  □ Logs revisados                                      │
│  □ Queries de validação executadas                     │
│  □ Backup realizado (opcional)                         │
│  □ Documentação atualizada                             │
│  □ Próximos passos planejados                          │
└─────────────────────────────────────────────────────────┘
```

---

## 🎉 CELEBRAÇÃO

Quando todos os itens acima estiverem ✅:

```
╔═══════════════════════════════════════════╗
║                                           ║
║   🎉 EXPORTAÇÃO CONCLUÍDA COM SUCESSO! 🎉  ║
║                                           ║
║   ✅ Dados migrados                       ║
║   ✅ Integridade verificada               ║
║   ✅ Sistema pronto para uso              ║
║                                           ║
║   Próximo: Criar dashboards e relatórios ║
║                                           ║
╚═══════════════════════════════════════════╝
```

---

**Versão:** 1.0  
**Criado:** 21/10/2025  
**Status:** ✅ Pronto para Execução  

**Boa Sorte! 🚀**
