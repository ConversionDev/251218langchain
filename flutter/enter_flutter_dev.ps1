ㅊㅊ# 이 스크립트를 dot-source 하면 현재 터미널이 R: 로 바뀌어서 "flutter run" 이 한글 경로 오류 없이 동작합니다.
# 사용법 (flutter 폴더에서):  . .\enter_flutter_dev.ps1
# 그 다음:  flutter run

$ErrorActionPreference = "Stop"
$flutterDir = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
$substDrive = "R:"

# 이미 R:가 다른 경로에 붙어 있으면 해제
$existing = subst 2>$null | Where-Object { $_ -match "^\s*$substDrive\s+" }
if ($existing) { subst $substDrive /D 2>$null }

subst $substDrive $flutterDir
Set-Location "${substDrive}\"
Write-Host "현재 드라이브가 R: (영문 경로)로 설정되었습니다. 이제 'flutter run' 을 입력하세요." -ForegroundColor Green
Write-Host "종료 후 R: 해제: subst R: /D" -ForegroundColor Gray
