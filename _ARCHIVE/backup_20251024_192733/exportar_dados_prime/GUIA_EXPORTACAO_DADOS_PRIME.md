# 📊 Guia Completo de Exportação de Dados Prime

## 🎯 **Objetivo**
Este documento explica como realizar a exportação em massa de todos os leads do banco de dados Prime, incluindo dados completos de contato (endereço e telefone) e manipulados (orçamentos/fórmulas).

## 🔍 **Descobertas Importantes**

### **Estrutura Real do Banco de Dados:**
- **Tabela Principal**: `CLIENTE` (dados básicos)
- **Endereços**: `CADASTRO_ENDERECO` (8.167 registros)
- **Telefones**: `CADASTRO_TELEFONE` (32.900 registros)
- **Orçamentos**: `ATENDIMENTO_A1` (16.437 registros)
- **Fórmulas**: `ATENDIMENTO_A2` (31.682 registros)

### **Campos de Relacionamento:**
- `CADASTRO_ENDERECO.CODIGO_CADASTRO = CLIENTE.CODIGO` (TIPO_CADASTRO = 1)
- `CADASTRO_TELEFONE.CODIGO_CADASTRO = CLIENTE.CODIGO` (TIPO_CADASTRO = 1)
- `ATENDIMENTO_A1.CODIGO_CLIENTE = CLIENTE.CODIGO`
- `ATENDIMENTO_A2.CODIGO_ATEND_A1 = ATENDIMENTO_A1.CODIGO`

## 📋 **Consulta SQL Completa para Exportação**

### **1. Consulta Principal de Leads Completos:**

```sql
-- Exportação completa de leads com dados de contato
SELECT 
    -- Dados básicos do cliente
    C.CODIGO as codigo_cliente,
    C.NOMECLIENTE as nome,
    C.CPF_CNPJ as cpf,
    C.DIANASCIMENTO as dia_nascimento,
    C.MESNASCIMENTO as mes_nascimento,
    C.ANONASCIMENTO as ano_nascimento,
    C.SEXO as sexo,
    C.EMAIL1 as email,
    
    -- Dados de endereço (tabela CADASTRO_ENDERECO)
    CE.ENDERECO as endereco,
    CE.NUMERO as numero,
    CE.CEP as cep,
    CE.OBSERVACAO as observacao_endereco,
    CID.NOMECIDADE as cidade,
    CID.UF as estado,
    
    -- Dados de telefone (tabela CADASTRO_TELEFONE)
    CT.TELEFONEPREFIXO as prefixo_telefone,
    CT.TELEFONE as telefone,
    CT.TELEFONE_TIPO as tipo_telefone,
    CT.OBSERVACAO as observacao_telefone,
    CT.SMS as sms,
    CT.WHATSAPP as whatsapp

FROM CLIENTE C
LEFT JOIN CADASTRO_ENDERECO CE ON C.CODIGO = CE.CODIGO_CADASTRO 
    AND CE.TIPO_CADASTRO = 1 
    AND CE.PRINCIPAL = -1  -- Endereço principal
LEFT JOIN CADASTRO_TELEFONE CT ON C.CODIGO = CT.CODIGO_CADASTRO 
    AND CT.TIPO_CADASTRO = 1 
    AND CT.PRINCIPAL = -1  -- Telefone principal
LEFT JOIN CIDADEESTADO CID ON CE.CODIGO_CIDADEESTADO = CID.CODIGO

WHERE C.ATIVO = -1  -- Clientes ativos
  AND C.NOMECLIENTE IS NOT NULL 
  AND TRIM(C.NOMECLIENTE) != ''
  AND C.CPF_CNPJ IS NOT NULL 
  AND TRIM(C.CPF_CNPJ) != ''

ORDER BY C.CODIGO;
```

### **2. Consulta de Manipulados (Orçamentos/Fórmulas):**

```sql
-- Exportação de manipulados por cliente
SELECT 
    A1.CODIGO_CLIENTE as codigo_cliente,
    A1.CODIGO as codigo_orcamento,
    A1.AVIADA_DT as data_aviada,
    A1.ENTREGUE_DT as data_entrega,
    A1.STATUS_MOV as status,
    A1.VALORVENDA as valor_total,
    A1.OBSERVACAO as observacoes,
    A1.CODIGO_MEDICO as codigo_medico,
    
    -- Fórmulas agrupadas
    LIST('Fórmula ' || A2.NUMEROFORMULA || ' - ' || A2.TEXTOROTULO || ' (' || A2.POSOLOGIA || ')', '; ') as formulas_descricao,
    COUNT(A2.CODIGO) as quantidade_formulas

FROM ATENDIMENTO_A1 A1
LEFT JOIN ATENDIMENTO_A2 A2 ON A1.CODIGO = A2.CODIGO_ATEND_A1

WHERE A1.CODIGO_CLIENTE IN (
    -- Lista de códigos de clientes da consulta principal
    SELECT C.CODIGO FROM CLIENTE C WHERE C.ATIVO = -1
)

GROUP BY 
    A1.CODIGO_CLIENTE, A1.CODIGO, A1.AVIADA_DT, A1.ENTREGUE_DT, 
    A1.STATUS_MOV, A1.VALORVENDA, A1.OBSERVACAO, A1.CODIGO_MEDICO

ORDER BY A1.CODIGO_CLIENTE, A1.AVIADA_DT DESC;
```

## 🚀 **Script Python para Exportação Automática**

### **Arquivo: `exportar_leads_completos.py`**

```python
import fdb
import json
import csv
from datetime import datetime
import os

# Configuração do banco
FIREBIRD_CONFIG = {
    'host': 'db.primesoftware.com.br',
    'port': 3050,
    'database': 'oficialmed1250',
    'user': 'OFICIALMED',
    'password': 'Lt-@=waIh))Ql3~',
    'charset': 'UTF8'
}

def exportar_leads_completos():
    """Exporta todos os leads com dados completos"""
    
    try:
        # Conectar ao banco
        con = fdb.connect(**FIREBIRD_CONFIG)
        cur = con.cursor()
        
        # Consulta principal de leads
        query_leads = """
        SELECT 
            C.CODIGO as codigo_cliente,
            C.NOMECLIENTE as nome,
            C.CPF_CNPJ as cpf,
            C.DIANASCIMENTO as dia_nascimento,
            C.MESNASCIMENTO as mes_nascimento,
            C.ANONASCIMENTO as ano_nascimento,
            C.SEXO as sexo,
            C.EMAIL1 as email,
            CE.ENDERECO as endereco,
            CE.NUMERO as numero,
            CE.CEP as cep,
            CE.OBSERVACAO as observacao_endereco,
            CID.NOMECIDADE as cidade,
            CID.UF as estado,
            CT.TELEFONEPREFIXO as prefixo_telefone,
            CT.TELEFONE as telefone,
            CT.TELEFONE_TIPO as tipo_telefone,
            CT.OBSERVACAO as observacao_telefone,
            CT.SMS as sms,
            CT.WHATSAPP as whatsapp
        FROM CLIENTE C
        LEFT JOIN CADASTRO_ENDERECO CE ON C.CODIGO = CE.CODIGO_CADASTRO 
            AND CE.TIPO_CADASTRO = 1 
            AND CE.PRINCIPAL = -1
        LEFT JOIN CADASTRO_TELEFONE CT ON C.CODIGO = CT.CODIGO_CADASTRO 
            AND CT.TIPO_CADASTRO = 1 
            AND CT.PRINCIPAL = -1
        LEFT JOIN CIDADEESTADO CID ON CE.CODIGO_CIDADEESTADO = CID.CODIGO
        WHERE C.ATIVO = -1
          AND C.NOMECLIENTE IS NOT NULL 
          AND TRIM(C.NOMECLIENTE) != ''
          AND C.CPF_CNPJ IS NOT NULL 
          AND TRIM(C.CPF_CNPJ) != ''
        ORDER BY C.CODIGO
        """
        
        # Executar consulta
        cur.execute(query_leads)
        leads = cur.fetchall()
        
        # Converter para lista de dicionários
        leads_data = []
        for lead in leads:
            leads_data.append({
                'codigo_cliente': lead[0],
                'nome': lead[1],
                'cpf': lead[2],
                'dia_nascimento': lead[3],
                'mes_nascimento': lead[4],
                'ano_nascimento': lead[5],
                'sexo': lead[6],
                'email': lead[7],
                'endereco': lead[8],
                'numero': lead[9],
                'cep': lead[10],
                'observacao_endereco': lead[11],
                'cidade': lead[12],
                'estado': lead[13],
                'prefixo_telefone': lead[14],
                'telefone': lead[15],
                'tipo_telefone': lead[16],
                'observacao_telefone': lead[17],
                'sms': lead[18],
                'whatsapp': lead[19]
            })
        
        # Salvar em JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"leads_completos_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(leads_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Exportados {len(leads_data)} leads para {filename}")
        
        # Salvar em CSV
        csv_filename = f"leads_completos_{timestamp}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            if leads_data:
                writer = csv.DictWriter(f, fieldnames=leads_data[0].keys())
                writer.writeheader()
                writer.writerows(leads_data)
        
        print(f"✅ Exportados {len(leads_data)} leads para {csv_filename}")
        
        con.close()
        return leads_data
        
    except Exception as e:
        print(f"❌ Erro na exportação: {e}")
        return None

if __name__ == "__main__":
    exportar_leads_completos()
```

## 📊 **Script de Estatísticas**

### **Arquivo: `gerar_estatisticas.py`**

```python
import fdb
import json
from datetime import datetime

def gerar_estatisticas():
    """Gera estatísticas dos dados exportados"""
    
    FIREBIRD_CONFIG = {
        'host': 'db.primesoftware.com.br',
        'port': 3050,
        'database': 'oficialmed1250',
        'user': 'OFICIALMED',
        'password': 'Lt-@=waIh))Ql3~',
        'charset': 'UTF8'
    }
    
    try:
        con = fdb.connect(**FIREBIRD_CONFIG)
        cur = con.cursor()
        
        # Estatísticas gerais
        stats = {}
        
        # Total de clientes
        cur.execute("SELECT COUNT(*) FROM CLIENTE WHERE ATIVO = -1")
        stats['total_clientes'] = cur.fetchone()[0]
        
        # Clientes com CPF
        cur.execute("SELECT COUNT(*) FROM CLIENTE WHERE ATIVO = -1 AND CPF_CNPJ IS NOT NULL AND TRIM(CPF_CNPJ) != ''")
        stats['clientes_com_cpf'] = cur.fetchone()[0]
        
        # Clientes com email
        cur.execute("SELECT COUNT(*) FROM CLIENTE WHERE ATIVO = -1 AND EMAIL1 IS NOT NULL AND TRIM(EMAIL1) != ''")
        stats['clientes_com_email'] = cur.fetchone()[0]
        
        # Clientes com data nascimento
        cur.execute("SELECT COUNT(*) FROM CLIENTE WHERE ATIVO = -1 AND DIANASCIMENTO IS NOT NULL AND MESNASCIMENTO IS NOT NULL AND ANONASCIMENTO IS NOT NULL")
        stats['clientes_com_nascimento'] = cur.fetchone()[0]
        
        # Clientes com sexo
        cur.execute("SELECT COUNT(*) FROM CLIENTE WHERE ATIVO = -1 AND SEXO IS NOT NULL")
        stats['clientes_com_sexo'] = cur.fetchone()[0]
        
        # Clientes com endereço
        cur.execute("""
            SELECT COUNT(DISTINCT C.CODIGO) 
            FROM CLIENTE C
            INNER JOIN CADASTRO_ENDERECO CE ON C.CODIGO = CE.CODIGO_CADASTRO 
            WHERE C.ATIVO = -1 AND CE.TIPO_CADASTRO = 1
        """)
        stats['clientes_com_endereco'] = cur.fetchone()[0]
        
        # Clientes com telefone
        cur.execute("""
            SELECT COUNT(DISTINCT C.CODIGO) 
            FROM CLIENTE C
            INNER JOIN CADASTRO_TELEFONE CT ON C.CODIGO = CT.CODIGO_CADASTRO 
            WHERE C.ATIVO = -1 AND CT.TIPO_CADASTRO = 1
        """)
        stats['clientes_com_telefone'] = cur.fetchone()[0]
        
        # Calcular percentuais
        total = stats['total_clientes']
        stats['percentuais'] = {
            'cpf': round((stats['clientes_com_cpf'] / total) * 100, 1),
            'email': round((stats['clientes_com_email'] / total) * 100, 1),
            'nascimento': round((stats['clientes_com_nascimento'] / total) * 100, 1),
            'sexo': round((stats['clientes_com_sexo'] / total) * 100, 1),
            'endereco': round((stats['clientes_com_endereco'] / total) * 100, 1),
            'telefone': round((stats['clientes_com_telefone'] / total) * 100, 1)
        }
        
        # Salvar estatísticas
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"estatisticas_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Estatísticas salvas em {filename}")
        print(f"📊 Total de clientes: {stats['total_clientes']}")
        print(f"📊 Clientes com CPF: {stats['clientes_com_cpf']} ({stats['percentuais']['cpf']}%)")
        print(f"📊 Clientes com email: {stats['clientes_com_email']} ({stats['percentuais']['email']}%)")
        print(f"📊 Clientes com endereço: {stats['clientes_com_endereco']} ({stats['percentuais']['endereco']}%)")
        print(f"📊 Clientes com telefone: {stats['clientes_com_telefone']} ({stats['percentuais']['telefone']}%)")
        
        con.close()
        return stats
        
    except Exception as e:
        print(f"❌ Erro ao gerar estatísticas: {e}")
        return None

if __name__ == "__main__":
    gerar_estatisticas()
```

## 🔄 **Processo de Exportação Incremental**

### **Arquivo: `exportacao_incremental.py`**

```python
import fdb
import json
import os
from datetime import datetime, timedelta

def exportacao_incremental():
    """Exporta apenas dados novos desde a última extração"""
    
    # Verificar última extração
    ultima_extração = None
    arquivos_json = [f for f in os.listdir('.') if f.startswith('leads_completos_') and f.endswith('.json')]
    
    if arquivos_json:
        # Encontrar o arquivo mais recente
        arquivo_mais_recente = max(arquivos_json, key=os.path.getctime)
        with open(arquivo_mais_recente, 'r', encoding='utf-8') as f:
            dados_anteriores = json.load(f)
        
        # Extrair timestamp do nome do arquivo
        timestamp_str = arquivo_mais_recente.replace('leads_completos_', '').replace('.json', '')
        ultima_extração = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
    
    # Consulta com filtro de data (se houver última extração)
    if ultima_extração:
        filtro_data = f"AND A1.AVIADA_DT > '{ultima_extração.strftime('%Y-%m-%d %H:%M:%S')}'"
    else:
        filtro_data = ""
    
    # Executar exportação incremental
    # ... (código similar ao anterior, mas com filtro de data)
    
    print(f"🔄 Exportação incremental desde {ultima_extração or 'início'}")
```

## 📁 **Estrutura de Arquivos Recomendada**

```
exportar_dados_prime/
├── GUIA_EXPORTACAO_DADOS_PRIME.md          # Este guia
├── exportar_leads_completos.py             # Script principal
├── gerar_estatisticas.py                   # Script de estatísticas
├── exportacao_incremental.py               # Script incremental
├── requirements.txt                         # Dependências Python
├── config.env                              # Configurações
└── banco_de_dados-prime/                   # Pasta para extrações
    ├── leads_completos_20251021_182700.json
    ├── leads_completos_20251022_090000.json
    └── estatisticas_20251021_182700.json
```

## 🚀 **Como Executar**

### **1. Instalar Dependências:**
```bash
pip install fdb
```

### **2. Executar Exportação Completa:**
```bash
python exportar_leads_completos.py
```

### **3. Gerar Estatísticas:**
```bash
python gerar_estatisticas.py
```

### **4. Exportação Incremental:**
```bash
python exportacao_incremental.py
```

## ⚠️ **Observações Importantes**

1. **Backup**: Sempre faça backup antes de executar exportações em massa
2. **Performance**: Para grandes volumes, considere executar em horários de menor uso
3. **Validação**: Sempre valide os dados exportados antes de usar em produção
4. **Segurança**: Mantenha as credenciais do banco em arquivos seguros
5. **Monitoramento**: Monitore o espaço em disco durante exportações grandes

## 📞 **Suporte**

Para dúvidas ou problemas:
- Verifique os logs de erro
- Consulte a documentação do Firebird
- Teste as consultas SQL diretamente no banco antes de executar os scripts

---

**Última atualização**: 21/10/2025  
**Versão**: 1.0  
**Autor**: Sistema de Exportação Prime
