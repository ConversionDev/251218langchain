# Cursor/VS Code 터미널에서 Android 에뮬레이터로 Flutter 앱 실행
# 사용법: flutter 폴더에서 .\run_android.ps1 또는 powershell -File run_android.ps1

$ErrorActionPreference = "Stop"
$flutterDir = $PSScriptRoot

# ShaderCompilerException 회피: 경로에 한글이 있으면 impellerc가 쓰기 실패함.
# subst로 영문 경로(예: R:)를 붙여서 빌드하면 shaders 쓰기 성공.
$substDrive = "R:"
$existingSubst = subst 2>$null | Where-Object { $_ -match "^\s*$substDrive\s+" }
if ($existingSubst) {
    subst $substDrive /D 2>$null
}
subst $substDrive $flutterDir
try {
    Set-Location "${substDrive}\"
} catch {
    subst $substDrive /D 2>$null
    Set-Location $flutterDir
    Write-Host "subst 실패, 프로젝트 경로에서 실행합니다. (쉐이더 오류 시 프로젝트를 C:\dev\RAG 등 영문 경로로 옮기세요.)" -ForegroundColor Yellow
}
$projectRoot = (Get-Location).Path

# Android SDK 경로 (local.properties 우선)
$localProps = Join-Path $projectRoot "android\local.properties"
$sdkDir = $null
if (Test-Path $localProps) {
    $content = Get-Content $localProps -Raw
    if ($content -match "sdk\.dir=(.+)") {
        $sdkDir = $matches[1].Trim().Replace("/", "\")
    }
}
if (-not $sdkDir) {
    $sdkDir = Join-Path $env:LOCALAPPDATA "Android\Sdk"
}

$emulatorExe = Join-Path $sdkDir "emulator\emulator.exe"
if (-not (Test-Path $emulatorExe)) {
    Write-Host "오류: Android 에뮬레이터를 찾을 수 없습니다. 경로: $emulatorExe" -ForegroundColor Red
    Write-Host "Android Studio에서 SDK와 AVD를 설치했는지 확인하세요." -ForegroundColor Yellow
    exit 1
}

# 실행 중인 에뮬레이터 확인
$devices = flutter devices 2>&1 | Out-String
$emulatorRunning = $devices -match "emulator-\d+"

if (-not $emulatorRunning) {
    $avds = & $emulatorExe -list-avds 2>$null
    if (-not $avds) {
        Write-Host "오류: AVD가 없습니다. Android Studio > Device Manager에서 에뮬레이터를 만드세요." -ForegroundColor Red
        exit 1
    }
    $avd = $avds[0]
    Write-Host "에뮬레이터 기동 중: $avd" -ForegroundColor Cyan
    Start-Process -FilePath $emulatorExe -ArgumentList "-avd", $avd -WindowStyle Normal
    Write-Host "부팅될 때까지 대기 중 (최대 90초)..." -ForegroundColor Cyan
    $timeout = 90
    $step = 3
    for ($t = 0; $t -lt $timeout; $t += $step) {
        Start-Sleep -Seconds $step
        $devices = flutter devices 2>&1 | Out-String
        if ($devices -match "emulator-\d+") {
            Write-Host "에뮬레이터가 준비되었습니다." -ForegroundColor Green
            break
        }
    }
    if ($t -ge $timeout) {
        Write-Host "경고: 시간 초과. 에뮬레이터가 아직 부팅 중일 수 있습니다. flutter run을 시도합니다." -ForegroundColor Yellow
    }
} else {
    Write-Host "이미 실행 중인 에뮬레이터를 사용합니다." -ForegroundColor Green
}

# ShaderCompilerException 회피: impellerc가 쓸 shaders 폴더를 미리 생성
$shadersDir = Join-Path $projectRoot "build\app\intermediates\flutter\debug\flutter_assets\shaders"
if (-not (Test-Path $shadersDir)) {
    New-Item -ItemType Directory -Path $shadersDir -Force | Out-Null
    Write-Host "shaders 출력 폴더 생성: $shadersDir" -ForegroundColor Gray
}

flutter run --no-enable-impeller
$exitCode = $LASTEXITCODE
if ($projectRoot -match "^[A-Z]:\\$") { subst $substDrive /D 2>$null }
exit $exitCode
