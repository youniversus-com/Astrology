# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# Launch Windows build inside MSYS2 UCRT64 from PowerShell.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$MsysBash = @(
    "C:\msys64\usr\bin\bash.exe",
    "C:\tools\msys64\usr\bin\bash.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $MsysBash) {
    Write-Error "MSYS2 not found. Install from https://www.msys2.org/ (expected C:\msys64\usr\bin\bash.exe)"
}

$UnixRoot = & $MsysBash -lc "cygpath -u '$Root'"
& $MsysBash -lc "export MSYSTEM=UCRT64; source /etc/profile; cd '$UnixRoot' && bash scripts/build-windows.sh"
