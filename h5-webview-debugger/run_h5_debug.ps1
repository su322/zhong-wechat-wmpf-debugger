$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..")
$mainPy = Join-Path $repoRoot "main.py"
$checkPy = Join-Path $scriptDir "check_h5_debug.py"
$devtoolsPort = 9222

Write-Host "H5 WebView debug launcher" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script only enables the existing PC WeChat XWeb inspect path."
Write-Host "It does not bypass WeChat-only pages, forge login state, or read web credentials."
Write-Host "Do not press Enter in the Python hook prompt until the H5 page has opened in PC WeChat."
Write-Host "After the page opens, check http://127.0.0.1:$devtoolsPort/json/list in a normal browser."
Write-Host ""

$wechatProcesses = Get-Process |
    Where-Object { $_.ProcessName -match "^(WeChat|WeChatAppEx|WeChatWeb|Weixin|HD_Weixin|XWeb)$" }

if ($wechatProcesses) {
    Write-Host "Detected running WeChat/XWeb processes:" -ForegroundColor Yellow
    $wechatProcesses | ForEach-Object {
        Write-Host ("- {0} PID {1}" -f $_.ProcessName, $_.Id)
    }
    Write-Host ""
    Write-Host "Close all PC WeChat windows and background processes, then run this script again." -ForegroundColor Yellow
    exit 1
}

$portListeners = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Where-Object { $_.LocalPort -eq $devtoolsPort }

if ($portListeners) {
    Write-Host "DevTools port $devtoolsPort is already in use:" -ForegroundColor Yellow
    $portListeners | ForEach-Object {
        Write-Host ("- {0}:{1} PID {2}" -f $_.LocalAddress, $_.LocalPort, $_.OwningProcess)
    }
    Write-Host ""
    Write-Host "Close the process using this port, then run this script again." -ForegroundColor Yellow
    exit 1
}

Write-Host "Starting PC WeChat through python ..\main.py -c ..." -ForegroundColor Green
Push-Location $repoRoot
try {
    python $mainPy -c
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "Failed to start PC WeChat through main.py -c. Fix the error above before testing H5 DevTools." -ForegroundColor Red
        exit $LASTEXITCODE
    }
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Hook has ended. Review the diagnostics below." -ForegroundColor Cyan
Write-Host ""
python $checkPy

Write-Host ""
Write-Host "Manual check:"
Write-Host "1. During the hook prompt, open the H5 page inside PC WeChat before pressing Enter."
Write-Host "2. Open http://127.0.0.1:9222/json/list in a normal browser and look for inspectable targets."
Write-Host "3. F12 inside WeChat may not be wired to DevTools even when the debug flag is present."
Write-Host "4. Record the result using h5-webview-debugger\reports\manual-check-template.md."
