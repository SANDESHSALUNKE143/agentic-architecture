param([ValidateSet('start','test','stop')][string]$Action='start',
      [string]$AgentNSource=$env:AGENTN_SOURCE)
$ErrorActionPreference='Stop'
$repo=Split-Path $PSScriptRoot -Parent
$compose=Join-Path $repo 'deployment/local/compose.yaml'
if (!$AgentNSource -or !(Test-Path (Join-Path $AgentNSource 'src/agentn_assistant'))) { throw 'Supply -AgentNSource with the AgentN consumer checkout path.' }
$env:AGENTN_SOURCE=(Resolve-Path $AgentNSource).Path
if (!$env:AGENT_API_TOKEN) {
    if ($Action -eq 'test') { throw 'Use the same shell/token used to start the service.' }
    $env:AGENT_API_TOKEN=[Guid]::NewGuid().ToString('N')+[Guid]::NewGuid().ToString('N')
}
function Compose([string[]]$Arguments) {
    & docker compose -f $compose @Arguments
    if ($LASTEXITCODE -ne 0) { throw 'Docker Compose failed.' }
}
if ($Action -eq 'stop') { Compose @('down'); return }
if ($Action -eq 'start') { Compose @('up','-d','--build','--wait','--wait-timeout','120') }
$base='http://127.0.0.1:8010'
$headers=@{Authorization="Bearer $env:AGENT_API_TOKEN"}
$path="$base/v1/agents/advertising-assistant"
$health=Invoke-RestMethod "$base/health"
if ($health.status -ne 'ok') { throw 'Health check failed.' }
try { Invoke-RestMethod "$path/config" | Out-Null; throw 'Unauthenticated request was accepted.' }
catch { if (!$_.Exception.Response -or [int]$_.Exception.Response.StatusCode -ne 401) { throw } }
$result=Invoke-RestMethod "$path/runs" -Method Post -Headers $headers -ContentType 'application/json' -Body '{"question":"Is the data ready?"}'
if (($result.tools_used -join ',') -ne 'list_tables,get_data_status' -or $result.answer -notmatch 'DEMO readiness') { throw 'Unexpected workflow result.' }
Compose @('restart','agentn')
Compose @('up','-d','--wait','--wait-timeout','120')
$events=Invoke-RestMethod "$path/events" -Headers $headers
if (!($events.events | Where-Object run_id -eq $result.run_id)) { throw 'Metadata did not survive restart.' }
Write-Host 'PASS: health, authentication, AgentN tool workflow, persistent metadata after restart.'
Write-Host $result.answer
Write-Host 'API: http://127.0.0.1:8010/docs. Token stays in this shell environment; it is not printed.'
