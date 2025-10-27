@echo off
echo ========================================
echo ATUALIZACAO EM BACKGROUND
echo ========================================
echo.
echo Iniciando atualizacao em background...
echo Log sera salvo em: atualizar_data_criacao.log
echo.
echo Para monitorar: type atualizar_data_criacao.log
echo.

start /B py atualizar_data_criacao_final.py > atualizar_data_criacao.log 2>&1

echo.
echo ✓ Processo iniciado em background!
echo.
echo Para monitorar o progresso execute:
echo   type atualizar_data_criacao.log
echo.
echo Para ver o progresso em tempo real:
echo   powershell Get-Content atualizar_data_criacao.log -Wait
echo.
pause
