param(
    [string]$Path = ".env"
)

if (-not (Test-Path $Path)) {
    Write-Host "No se encontró el archivo $Path" -ForegroundColor Red
    exit 1
}

Get-Content $Path | ForEach-Object {
    if ($_ -match '^(\s*#|\s*$)') { return }
    if ($_ -match '^(?<key>[^=]+)=(?<value>.*)$') {
        $key = $Matches['key'].Trim()
        $value = $Matches['value']
        Set-Content -Path "Env:$key" -Value $value
    }
}

Write-Host "Variables cargadas desde $Path" -ForegroundColor Green
