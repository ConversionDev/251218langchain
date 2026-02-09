# ShaderCompilerException / "Could not write file" 오류 해결
# 사용법: flutter 폴더에서 .\fix_shader_build.ps1 실행 후 flutter run

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "빌드 캐시 삭제 중 (flutter clean)..." -ForegroundColor Cyan
flutter clean
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "완료. 이제 'flutter run' 또는 run_android.bat 을 실행하세요." -ForegroundColor Green
