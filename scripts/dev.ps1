$ErrorActionPreference='Stop'
$workspaceRoot=Split-Path -Parent $PSScriptRoot
& (Join-Path $workspaceRoot '.venv\Scripts\python.exe') -X utf8 (Join-Path $PSScriptRoot 'dev.py')
exit $LASTEXITCODE
