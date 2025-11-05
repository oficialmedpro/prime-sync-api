-- ============================================
-- ATUALIZAR SUPABASE PARA CHAMAR RENDER.COM
-- Execute este SQL no SQL Editor do Supabase
-- ============================================

-- Atualizar função para chamar Render.com ao invés de Portainer
CREATE OR REPLACE FUNCTION api.sync_prime_incremental()
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  v_response http_response;
  v_result json;
BEGIN
  -- Chamar Render.com ao invés de sincro.oficialmed.com.br
  SELECT * INTO v_response
  FROM http((
    'POST',
    'https://prime-sync-api.onrender.com/sync',  -- URL do Render.com
    ARRAY[
      http_header('Content-Type', 'application/json'),
      http_header('Authorization', 'Bearer prime-sync-2025-xY9kL2mP4nQ8wR5t')
    ],
    'application/json',
    '{}'
  )::http_request);

  -- Se status 200, sucesso!
  IF v_response.status = 200 THEN
    RAISE NOTICE 'Sincronização bem-sucedida via Render.com';
    RETURN v_response.content::json;
  ELSE
    RAISE WARNING 'Falha no Render.com: Status %', v_response.status;
    RETURN json_build_object(
      'sucesso', false,
      'erro', 'Falha no Render',
      'status_code', v_response.status,
      'content', v_response.content
    );
  END IF;
EXCEPTION WHEN OTHERS THEN
  RAISE WARNING 'Erro ao chamar Render.com: %', SQLERRM;
  RETURN json_build_object(
    'sucesso', false,
    'erro', SQLERRM,
    'timestamp', now()
  );
END;
$$;

-- Testar a função manualmente
-- SELECT api.sync_prime_incremental();

-- Ver logs
-- SELECT * FROM api.sync_logs ORDER BY timestamp DESC LIMIT 10;

