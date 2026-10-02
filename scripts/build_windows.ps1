param(
    [switch]$Clean,
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

if ($env:OS -ne "Windows_NT") {
    throw "O build Windows deve ser executado no Windows."
}

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location $ProjectRoot
try {
    if ($Clean) {
        foreach ($Folder in @("build", "dist")) {
            $Target = Join-Path $ProjectRoot $Folder
            if (Test-Path -LiteralPath $Target) {
                Remove-Item -LiteralPath $Target -Recurse -Force
            }
        }
    }

    if (-not $SkipTests) {
        python -m pytest
        if ($LASTEXITCODE -ne 0) {
            throw "Os testes falharam. O build foi interrompido."
        }
    }

    python -m PyInstaller --noconfirm VistoriaApp.spec
    if ($LASTEXITCODE -ne 0) {
        throw "O PyInstaller falhou. Consulte as mensagens acima."
    }

    $Executable = Join-Path $ProjectRoot "dist\VistoriaApp\VistoriaApp.exe"
    if (-not (Test-Path -LiteralPath $Executable -PathType Leaf)) {
        throw "O executavel esperado nao foi encontrado: $Executable"
    }
    Write-Host "Build concluido: $Executable"
    Write-Host "Distribua a pasta dist\VistoriaApp inteira, incluindo _internal."
}
finally {
    Pop-Location
}
