-- ============================================
-- CRONJOB SUPABASE - SINCRONIZAÇÃO AUTOMÁTICA
-- Execute este SQL no SQL Editor do Supabase
-- ============================================

-- 1. Habilitar extensões necessárias (apenas uma vez)
CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE EXTENSION IF NOT EXISTS http;

-- 2. Criar função de sincronização com failover automático
CREATE OR REPLACE FUNCTION api.sync_prime_incremental()
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  v_response http_response;
  v_result json;
  v_url text;
BEGIN
  -- Tentar primeiro endpoint: EasyPanel (IP direto)
  v_url := 'http://72.60.61.40:5000/sync';

  BEGIN
    SELECT * INTO v_response
    FROM http((
      'POST',
      v_url,
      ARRAY[http_header('Content-Type', 'application/json'),
            http_header('Authorization', 'Bearer prime-sync-2025-xY9kL2mP4nQ8wR5t')],
      'application/json',
      '{}'
    )::http_request);

    -- Se status 200, sucesso!
    IF v_response.status = 200 THEN
      RAISE NOTICE 'Sincronização bem-sucedida via EasyPanel (72.60.61.40:5000)';
      RETURN v_response.content::json;
    END IF;

  EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Falha em EasyPanel (72.60.61.40:5000): %. Tentando fallback...', SQLERRM;
  END;

  -- Fallback: tentar segundo endpoint (se configurar domínio depois)
  v_url := 'http://72.60.61.40:5000/sync';

  BEGIN
    SELECT * INTO v_response
    FROM http((
      'POST',
      v_url,
      ARRAY[http_header('Content-Type', 'application/json'),
            http_header('Authorization', 'Bearer prime-sync-2025-xY9kL2mP4nQ8wR5t')],
      'application/json',
      '{}'
    )::http_request);

    -- Se status 200, sucesso!
    IF v_response.status = 200 THEN
      RAISE NOTICE 'Sincronização bem-sucedida via EasyPanel (fallback)';
      RETURN v_response.content::json;
    END IF;

  EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Falha no fallback EasyPanel: %', SQLERRM;
  END;

  -- Se chegou aqui, ambos falharam
  RETURN json_build_object(
    'sucesso', false,
    'erro', 'Ambos os endpoints falharam',
    'timestamp', now()
  );
END;
$$;

-- 3. Criar tabela de log (opcional, mas recomendado)
CREATE TABLE IF NOT EXISTS api.sync_logs (
  id bigserial PRIMARY KEY,
  timestamp timestamptz DEFAULT now(),
  resultado json,
  sucesso boolean,
  total_inseridos integer,
  erro text
);

-- 4. Criar função wrapper que loga o resultado
CREATE OR REPLACE FUNCTION api.sync_prime_with_log()
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
  v_resultado json;
  v_sucesso boolean;
  v_total integer;
  v_erro text;
BEGIN
  -- Executar sincronização
  SELECT api.sync_prime_incremental() INTO v_resultado;

  -- Extrair informações
  v_sucesso := (v_resultado->>'sucesso')::boolean;
  v_total := COALESCE((v_resultado->>'total_inseridos')::integer, 0);
  v_erro := v_resultado->>'erro';

  -- Salvar log
  INSERT INTO api.sync_logs (resultado, sucesso, total_inseridos, erro)
  VALUES (v_resultado, v_sucesso, v_total, v_erro);

  -- Notificar
  IF v_sucesso THEN
    RAISE NOTICE 'Sincronização concluída: % registros inseridos', v_total;
  ELSE
    RAISE WARNING 'Sincronização falhou: %', v_erro;
  END IF;
END;
$$;

-- 5. Agendar execução automática a cada 15 minutos
SELECT cron.schedule(
  'sync-prime-incremental-15min',  -- Nome do job
  '*/15 * * * *',                  -- A cada 15 minutos
  'SELECT api.sync_prime_with_log();'
);

-- ============================================
-- COMANDOS ÚTEIS
-- ============================================

-- Ver jobs agendados
SELECT * FROM cron.job ORDER BY jobid;

-- Ver histórico de execução
SELECT * FROM cron.job_run_details
WHERE jobid = (SELECT jobid FROM cron.job WHERE jobname = 'sync-prime-incremental-15min')
ORDER BY start_time DESC
LIMIT 10;

-- Ver logs de sincronização
SELECT
  timestamp,
  sucesso,
  total_inseridos,
  resultado->>'tempo_execucao_segundos' as tempo_segundos,
  resultado->'clientes'->>'inseridos' as clientes_novos,
  resultado->'pedidos'->>'inseridos' as pedidos_novos,
  erro
FROM api.sync_logs
ORDER BY timestamp DESC
LIMIT 20;

-- Executar manualmente (para testar)
SELECT api.sync_prime_with_log();

-- Desagendar job (se necessário)
-- SELECT cron.unschedule('sync-prime-incremental-15min');

-- Reagendar com frequência diferente
-- SELECT cron.unschedule('sync-prime-incremental-15min');
-- SELECT cron.schedule(
--   'sync-prime-incremental-30min',
--   '*/30 * * * *',  -- A cada 30 minutos
--   'SELECT api.sync_prime_with_log();'
-- );

-- ============================================
-- MONITORAMENTO
-- ============================================

-- Dashboard de sincronização (últimas 24h)
SELECT
  date_trunc('hour', timestamp) as hora,
  COUNT(*) as execucoes,
  SUM(CASE WHEN sucesso THEN 1 ELSE 0 END) as sucessos,
  SUM(CASE WHEN NOT sucesso THEN 1 ELSE 0 END) as falhas,
  SUM(total_inseridos) as total_inseridos,
  ROUND(AVG((resultado->>'tempo_execucao_segundos')::numeric), 2) as tempo_medio_seg
FROM api.sync_logs
WHERE timestamp >= now() - interval '24 hours'
GROUP BY date_trunc('hour', timestamp)
ORDER BY hora DESC;

-- Estatísticas gerais
SELECT
  COUNT(*) as total_execucoes,
  SUM(CASE WHEN sucesso THEN 1 ELSE 0 END) as sucessos,
  SUM(CASE WHEN NOT sucesso THEN 1 ELSE 0 END) as falhas,
  ROUND(100.0 * SUM(CASE WHEN sucesso THEN 1 ELSE 0 END) / COUNT(*), 2) as taxa_sucesso_pct,
  SUM(total_inseridos) as total_registros_sincronizados
FROM api.sync_logs
WHERE timestamp >= now() - interval '7 days';
