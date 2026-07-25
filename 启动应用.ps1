$ErrorActionPreference = "Stop"

Set-Location -LiteralPath $PSScriptRoot

Write-Host "正在启动 明白金 FinFair..." -ForegroundColor Cyan
Write-Host "浏览器地址：http://localhost:8501" -ForegroundColor DarkGray

python -m streamlit run app.py --server.port=8501 --server.headless=true --server.showEmailPrompt=false --browser.gatherUsageStats=false
