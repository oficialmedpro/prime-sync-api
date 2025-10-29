#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Auditoria de Sincronização
Registra todas as operações de sync para rastreamento e verificação
"""

import requests
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Configurações
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Accept-Profile': 'api',
    'Content-Profile': 'api'
}

def iniciar_auditoria(tabela_origem, tabela_destino, total_firebird=0):
    """Inicia registro de auditoria"""
    try:
        data = {
            'tabela_origem': tabela_origem,
            'tabela_destino': tabela_destino,
            'total_registros_firebird': total_firebird,
            'status': 'em_andamento',
            'data_inicio': datetime.now().isoformat()
        }
        
        url = f"{SUPABASE_URL}/rest/v1/sync_auditoria"
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code in [200, 201]:
            auditoria_id = response.json()[0]['id']
            logger.info(f"📝 Auditoria {auditoria_id} iniciada para {tabela_origem} → {tabela_destino}")
            return auditoria_id
        else:
            logger.error(f"❌ Erro ao criar auditoria: {response.status_code}")
            return None
    
    except Exception as e:
        logger.error(f"❌ Erro em iniciar_auditoria: {e}")
        return None

def finalizar_auditoria(auditoria_id, total_supabase=0, registros_novos=0, 
                        registros_atualizados=0, registros_com_erro=0, 
                        status='sucesso', mensagem=None, detalhes=None):
    """Finaliza registro de auditoria"""
    if not auditoria_id:
        return
    
    try:
        # Buscar data início
        url_get = f"{SUPABASE_URL}/rest/v1/sync_auditoria?id=eq.{auditoria_id}"
        resp = requests.get(url_get, headers=headers, timeout=10)
        
        if resp.status_code == 200 and resp.json():
            data_inicio_str = resp.json()[0]['data_inicio']
            data_inicio = datetime.fromisoformat(data_inicio_str.replace('Z', '+00:00'))
            tempo_execucao = (datetime.now() - data_inicio.replace(tzinfo=None)).total_seconds()
        else:
            tempo_execucao = 0
        
        data = {
            'total_registros_supabase': total_supabase,
            'registros_novos': registros_novos,
            'registros_atualizados': registros_atualizados,
            'registros_com_erro': registros_com_erro,
            'data_fim': datetime.now().isoformat(),
            'tempo_execucao_segundos': round(tempo_execucao, 2),
            'status': status,
            'mensagem': mensagem or f'Inseridos: {registros_novos}, Atualizados: {registros_atualizados}',
            'detalhes': detalhes
        }
        
        url = f"{SUPABASE_URL}/rest/v1/sync_auditoria?id=eq.{auditoria_id}"
        response = requests.patch(url, headers=headers, json=data, timeout=10)
        
        if response.status_code in [200, 204]:
            logger.info(f"✅ Auditoria {auditoria_id} finalizada: {status} ({tempo_execucao:.1f}s)")
        else:
            logger.error(f"❌ Erro ao finalizar auditoria: {response.status_code}")
    
    except Exception as e:
        logger.error(f"❌ Erro em finalizar_auditoria: {e}")

def verificar_integridade():
    """Verifica integridade dos dados entre Firebird e Supabase"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/rpc/verificar_integridade_dados"
        response = requests.post(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            logger.info("✅ Verificação de integridade:")
            for item in response.json():
                logger.info(f"   {item['tabela']}.{item['campo']}: {item['percentual_compatibilidade']}% ({item['diferenca']:+d})")
            return response.json()
        else:
            logger.error(f"❌ Erro na verificação: {response.status_code}")
            return None
    
    except Exception as e:
        logger.error(f"❌ Erro em verificar_integridade: {e}")
        return None

def listar_ultimas_sincronizacoes(limite=10):
    """Lista últimas sincronizações"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/sync_auditoria"
        params = {
            'select': 'id,tabela_origem,tabela_destino,status,registros_novos,tempo_execucao_segundos,data_inicio,data_fim',
            'order': 'data_inicio.desc',
            'limit': limite
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return []
    
    except Exception as e:
        logger.error(f"❌ Erro ao listar sincronizações: {e}")
        return []

