# 将 16 下所有 Languages\ChineseSimplified 里的 Keyed 和 DefInjected 汇总到根目录：
#   Languages/ChineseSimplified/Keyed/  和  Languages/ChineseSimplified/DefInjected/
# 使用原始文件名；同名时在扩展名前加序号 1、2、3…（如 AbilityDef1.xml），不覆盖。
# 运行: PowerShell -ExecutionPolicy Bypass -File "Collect-All-Translations-To-Root.ps1"

$ErrorActionPreference = "Stop"
$ModsRoot = "C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Mods"
$PackRoot = Join-Path $ModsRoot "rjw-zh-main"
$Base16 = Join-Path $PackRoot "1.6"
$DstBase = Join-Path $PackRoot "Languages\ChineseSimplified"
$DstKeyed = Join-Path $DstBase "Keyed"
$DstDefInjected = Join-Path $DstBase "DefInjected"

$sourceDirs = Get-ChildItem -Path $Base16 -Directory -Recurse -Filter "ChineseSimplified" -ErrorAction SilentlyContinue `
    | Where-Object { $_.FullName -match "\\Languages\\ChineseSimplified$" }

if (-not $sourceDirs) {
    Write-Host "No Languages\ChineseSimplified found under 16" -ForegroundColor Yellow
    exit 0
}

# 若目标已存在则生成带序号的文件名：Name1.xml, Name2.xml, ...
function Get-UniqueFileName($dir, $baseName) {
    $ext = [System.IO.Path]::GetExtension($baseName)
    $stem = [System.IO.Path]::GetFileNameWithoutExtension($baseName)
    $path = Join-Path $dir $baseName
    if (-not (Test-Path $path)) { return $baseName }
    $n = 1
    do { $candidate = "${stem}${n}${ext}"; $path = Join-Path $dir $candidate; $n++ }
    while (Test-Path $path)
    return $candidate
}

New-Item -ItemType Directory -Path $DstKeyed -Force | Out-Null
New-Item -ItemType Directory -Path $DstDefInjected -Force | Out-Null

$totalKeyed = 0
$totalDefInjected = 0
$numbered = 0
foreach ($srcLang in $sourceDirs) {
    $relativeFrom16 = $srcLang.Parent.Parent.FullName
    if (-not $relativeFrom16.StartsWith($Base16)) { continue }
    $pathIn16 = $relativeFrom16.Substring($Base16.Length).TrimStart("\")
    if ([string]::IsNullOrWhiteSpace($pathIn16)) { continue }

    $keyedSrc = Join-Path $srcLang.FullName "Keyed"
    if (Test-Path $keyedSrc) {
        foreach ($f in Get-ChildItem $keyedSrc -File -Recurse -ErrorAction SilentlyContinue) {
            $rel = $f.FullName.Substring($keyedSrc.Length).TrimStart("\")
            $dstDir = Join-Path $DstKeyed (Split-Path $rel -Parent)
            if ($rel -match "\\") { New-Item -ItemType Directory -Path $dstDir -Force | Out-Null }
            else { $dstDir = $DstKeyed }
            $dstName = Get-UniqueFileName $dstDir $f.Name
            $dstPath = Join-Path $dstDir $dstName
            if ($dstName -ne $f.Name) {
                Write-Host "[Duplicate] $pathIn16 -> $dstName" -ForegroundColor Yellow
                $numbered++
            }
            Copy-Item -Path $f.FullName -Destination $dstPath -Force
            $totalKeyed++
        }
    }

    $defSrc = Join-Path $srcLang.FullName "DefInjected"
    if (Test-Path $defSrc) {
        foreach ($f in Get-ChildItem $defSrc -File -Recurse -ErrorAction SilentlyContinue) {
            $rel = $f.FullName.Substring($defSrc.Length).TrimStart("\")
            $dstDir = Join-Path $DstDefInjected (Split-Path $rel -Parent)
            if ($rel -match "\\") { New-Item -ItemType Directory -Path $dstDir -Force | Out-Null }
            else { $dstDir = $DstDefInjected }
            $dstName = Get-UniqueFileName $dstDir $f.Name
            $dstPath = Join-Path $dstDir $dstName
            if ($dstName -ne $f.Name) {
                Write-Host "[Duplicate] $pathIn16 -> $dstName" -ForegroundColor Yellow
                $numbered++
            }
            Copy-Item -Path $f.FullName -Destination $dstPath -Force
            $totalDefInjected++
        }
    }
}

Write-Host "Done. Keyed: $totalKeyed files, DefInjected: $totalDefInjected files -> $DstBase." -ForegroundColor Cyan
if ($numbered -gt 0) { Write-Host "Duplicate names (saved with 1,2,3...): $numbered file(s)." -ForegroundColor Yellow }
