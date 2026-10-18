param([ValidateSet('start','test','stop','status')][string]$Action='start',[string]$AgentNSource)
$ErrorActionPreference='Stop'
$repo=Split-Path $PSScriptRoot -Parent
$full=Join-Path $repo 'deployment/full'
$envFile=Join-Path $full '.env'
if (!(Test-Path $envFile)) {
    if ($Action -ne 'start') { throw 'Start the platform first.' }
    if (!$AgentNSource -or !(Test-Path (Join-Path $AgentNSource 'src/agentn_assistant'))) { throw 'Supply -AgentNSource pointing to the independent AgentN consumer.' }
    $values=@("AGENTN_SOURCE=$((Resolve-Path $AgentNSource).Path.Replace('\','/'))")
    foreach ($key in @('POSTGRES_PASSWORD','QDRANT_API_KEY','PLATFORM_AGENT_TOKEN','PLATFORM_OTHER_TOKEN','AGENT_API_TOKEN','GRAFANA_PASSWORD')) {
        $values += "$key=$([Guid]::NewGuid().ToString('N'))$([Guid]::NewGuid().ToString('N'))"
    }
    [IO.File]::WriteAllLines($envFile,$values)
}
function Compose([string[]]$Arguments) {
    & docker compose --env-file $envFile -f (Join-Path $full 'compose.yaml') @Arguments
    if ($LASTEXITCODE -ne 0) { throw 'Docker Compose failed; inspect service logs without printing environment variables.' }
}
switch ($Action) {
    'start' { Compose @('up','-d','--build','--wait','--wait-timeout','180') }
    'stop' { Compose @('down'); return }
    'status' { Compose @('ps'); return }
}
# Acceptance uses the consumer's Python if present; only the standard library is required.
$python='python'
$line=Get-Content $envFile | Where-Object { $_.StartsWith('AGENTN_SOURCE=') } | Select-Object -First 1
$source=$line.Substring('AGENTN_SOURCE='.Length)
$venv=Join-Path $source '.venv/Scripts/python.exe'
if (Test-Path $venv) { $python=$venv }
& $python (Join-Path $repo 'scripts/test_full_platform.py')
if ($LASTEXITCODE -ne 0) { throw 'Platform acceptance tests failed.' }
Write-Host 'Agent API: http://127.0.0.1:8010/docs'
Write-Host 'Platform APIs: http://127.0.0.1:8020/docs'
Write-Host 'Grafana: http://127.0.0.1:3002 (admin; password in ignored deployment/full/.env)'
