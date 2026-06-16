$venvPath = Join-Path $PSScriptRoot 'venv-win'
if (-not (Test-Path $venvPath)) {
    python -m venv $venvPath
}
$python = Join-Path $venvPath 'bin\python.exe'
& $python -m pip install --upgrade pip setuptools wheel
& $python -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt')
& $python -m pip install --force-reinstall orjson pydantic-core
