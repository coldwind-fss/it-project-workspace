param([switch]$NoDatabase)
$ErrorActionPreference='Stop'
$workspaceRoot=Split-Path -Parent $PSScriptRoot
$workspacePython=Join-Path $workspaceRoot '.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $workspacePython)) { throw 'Run Python 3.12 scripts/setup.py first.' }
$workspaceArguments=@('-X','utf8',(Join-Path $PSScriptRoot 'verify.py'))
if ($NoDatabase) { $workspaceArguments+='--no-database' }
& $workspacePython @workspaceArguments
exit $LASTEXITCODE
