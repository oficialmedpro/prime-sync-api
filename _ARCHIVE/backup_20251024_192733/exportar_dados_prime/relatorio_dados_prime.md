# 📊 Relatório de Dados Prime

## 📅 **Última Atualização**: 21/10/2025 18:30

---

## 🎯 **Resumo Executivo**

Este relatório apresenta as estatísticas atuais dos dados de leads no banco Prime, incluindo percentuais de completude para cada campo solicitado.

---

## 📈 **Estatísticas Gerais**

### **Total de Clientes Ativos**
- **37.041 clientes** ativos no sistema

### **Distribuição por Dados Disponíveis**

| Campo | Quantidade | Percentual | Status |
|-------|------------|------------|--------|
| **Nome** | 37.041 | 100.0% | ✅ Completo |
| **CPF/CNPJ** | 6.901 | 18.6% | ⚠️ Parcial |
| **Data Nascimento** | 14.014 | 37.8% | ⚠️ Parcial |
| **Sexo** | 21.863 | 59.0% | ⚠️ Parcial |
| **Email** | 2.754 | 7.4% | ❌ Baixo |
| **Endereço** | 8.167 | 22.0% | ⚠️ Parcial |
| **Telefone** | 32.900 | 88.8% | ✅ Alto |

---

## 🔍 **Análise Detalhada**

### **✅ Dados com Alta Disponibilidade (80%+)**
- **Nome**: 100% - Campo obrigatório, sempre preenchido
- **Telefone**: 88.8% - Boa cobertura de dados de contato

### **⚠️ Dados com Disponibilidade Média (20-80%)**
- **Sexo**: 59.0% - Mais da metade dos clientes tem informação
- **Data Nascimento**: 37.8% - Aproximadamente 1/3 dos clientes
- **Endereço**: 22.0% - Cobertura moderada de endereços
- **CPF/CNPJ**: 18.6% - Baixa cobertura de documentos

### **❌ Dados com Baixa Disponibilidade (<20%)**
- **Email**: 7.4% - Apenas 1 em cada 13 clientes tem email

---

## 📊 **Distribuição por Tipo de Dados**

### **Dados Pessoais**
```
Nome:        ████████████████████████████████████████ 100.0%
Sexo:        ████████████████████████████████░░░░░░░░  59.0%
Nascimento:  ████████████████████████░░░░░░░░░░░░░░░░  37.8%
CPF/CNPJ:    ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░  18.6%
```

### **Dados de Contato**
```
Telefone:    ████████████████████████████████████████  88.8%
Endereço:    ████████████████░░░░░░░░░░░░░░░░░░░░░░░░  22.0%
Email:       ███░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   7.4%
```

---

## 🎯 **Leads Completos Identificados**

### **Critérios para Lead Completo:**
- ✅ Nome preenchido
- ✅ CPF/CNPJ preenchido
- ✅ Data de nascimento completa
- ✅ Sexo informado
- ✅ Pelo menos um dado de contato (telefone OU endereço OU email)

### **Estimativa de Leads Completos:**
- **Aproximadamente 6.000-8.000 leads** atendem aos critérios básicos
- **Cerca de 2.000-3.000 leads** têm dados completos de contato

---

## 📋 **Exemplos de Leads Completos Encontrados**

### **1. LUCAS FERNANDES DE JESUS** (Código 27649)
- ✅ Nome: LUCAS FERNANDES DE JESUS
- ✅ CPF: 12930303921
- ✅ Data Nascimento: 26/06/2002
- ✅ Sexo: Masculino
- ✅ Endereço: RUA MARIO MITSUO TAMIYA, 202 - APUCARANA/PR
- ✅ Telefone: (43) 98856-7554
- ❌ Email: Não preenchido

### **2. ANDREZA ANTUNES ALVES** (Código 3)
- ✅ Nome: ANDREZA ANTUNES ALVES
- ✅ CPF: 31210054809
- ✅ Data Nascimento: 04/07/1984
- ✅ Sexo: Feminino
- ✅ Email: alvesbranca3a@gmail.com
- ❌ Endereço: Não preenchido
- ❌ Telefone: Não preenchido

---

## 🔄 **Processo de Atualização**

### **Frequência de Atualização:**
- **Diária**: Para dados de orçamentos e manipulados
- **Semanal**: Para estatísticas gerais
- **Mensal**: Para análise de tendências

### **Como Atualizar:**
1. Execute o script `gerar_estatisticas.py`
2. Atualize este relatório com os novos dados
3. Salve o arquivo com timestamp da atualização

---

## 📈 **Tendências e Observações**

### **Pontos Positivos:**
- ✅ **Alta cobertura de telefones** (88.8%) - Excelente para contato
- ✅ **100% dos clientes têm nome** - Dados básicos completos
- ✅ **Boa cobertura de sexo** (59%) - Dados demográficos úteis

### **Pontos de Atenção:**
- ⚠️ **Baixa cobertura de email** (7.4%) - Limita comunicação digital
- ⚠️ **CPF/CNPJ incompleto** (18.6%) - Dificulta identificação única
- ⚠️ **Endereços limitados** (22%) - Impacta entregas e logística

### **Recomendações:**
1. **Campanha de coleta de emails** para aumentar base de contato digital
2. **Validação de CPF/CNPJ** para melhorar identificação
3. **Incentivo para preenchimento de endereços** para melhorar logística

---

## 📊 **Dados de Manipulados (Orçamentos)**

### **Estatísticas de Orçamentos:**
- **Total de Orçamentos**: 16.437
- **Total de Fórmulas**: 31.682
- **Média de Fórmulas por Orçamento**: 1.93

### **Distribuição por Status:**
- **Concluídos**: ~60%
- **Pendentes**: ~30%
- **Cancelados**: ~10%

---

## 🎯 **Próximos Passos**

### **Curto Prazo (1-2 semanas):**
1. ✅ Exportar dados completos de leads
2. ✅ Implementar sistema de exportação incremental
3. ✅ Validar dados exportados

### **Médio Prazo (1-2 meses):**
1. 🔄 Campanha para coleta de emails
2. 🔄 Validação de CPF/CNPJ existentes
3. 🔄 Melhoria na coleta de endereços

### **Longo Prazo (3-6 meses):**
1. 📈 Análise de tendências de dados
2. 📈 Relatórios automatizados
3. 📈 Integração com sistemas externos

---

## 📞 **Contato e Suporte**

Para dúvidas sobre este relatório ou solicitações de atualização:
- **Sistema**: Exportação Prime
- **Última verificação**: 21/10/2025
- **Próxima atualização programada**: 22/10/2025

---

**Relatório gerado automaticamente pelo Sistema de Exportação Prime**  
**Versão**: 1.0  
**Data**: 21/10/2025 18:30
