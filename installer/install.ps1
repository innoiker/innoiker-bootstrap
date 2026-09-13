$ErrorActionPreference = 'Stop'

$BootstrapRawUrl = if ($env:INNOIKER_BOOTSTRAP_RAW_URL) { $env:INNOIKER_BOOTSTRAP_RAW_URL } else { 'https://raw.githubusercontent.com/innoiker/innoiker-bootstrap/main/installer/install.sh' }

function Write-Info($Message) {
    Write-Host "[innoiker] $Message"
}

if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
    throw 'Windows 설치는 WSL2를 요구합니다. 먼저 `wsl --install`을 실행하고 재부팅한 뒤 다시 시도하세요.'
}

Write-Info 'WSL에서 Innoiker bootstrapper를 설치합니다.'
$escapedUrl = $BootstrapRawUrl.Replace("'", "'\"'\"'")
$command = "curl -fsSL '$escapedUrl' | bash"
& wsl.exe bash -lc $command

Write-Info '설치 완료. WSL 터미널에서 다음을 실행하세요:'
Write-Host 'inno doctor'
Write-Host 'inno create my-project'
