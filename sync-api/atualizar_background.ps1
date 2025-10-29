# Script PowerShell para rodar atualização em background
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ATUALIZACAO EM BACKGROUND" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$logFile = "atualizar_data_criacao.log"

Write-Host "Iniciando atualizacao em background..." -ForegroundColor Green
Write-Host "Log sera salvo em: $logFile" -ForegroundColor Yellow
Write-Host ""

# Iniciar processo em background
$job = Start-Job -ScriptBlock {
    Set-Location "C:\Banco de Dados Prime\sync-api"
    py atualizar_data_criacao_final.py 2>&1 | Tee-Object -FilePath "atualizar_data_criacao.log"
}

Write-Host "✓ Processo iniciado em background!" -ForegroundColor Green
Write-Host "Job ID: $($job.Id)" -ForegroundColor Cyan
Write-Host ""
Write-Host "Para monitorar em tempo real:" -ForegroundColor Yellow
Write-Host "  Get-Content $logFile -Wait" -ForegroundColor White
Write-Host ""
Write-Host "Para verificar status do job:" -ForegroundColor Yellow
Write-Host "  Get-Job -Id $($job.Id)" -ForegroundColor White
Write-Host ""
Write-Host "Para parar o processo:" -ForegroundColor Yellow
Write-Host "  Stop-Job -Id $($job.Id)" -ForegroundColor White
Write-Host ""
