$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskPreview = Join-Path $taskRoot 'previews'
& ffmpeg -y -framerate 10 -i (Join-Path $taskPreview 'frames\%04d.png') -i (Join-Path $taskPreview 'assembly-overlay.png') -filter_complex '[0:v][1:v]overlay=0:0:format=auto,fps=30,format=yuv420p[v]' -map '[v]' -c:v libx264 -crf 18 -movflags +faststart (Join-Path $taskPreview 'assembly-preview.mp4')
if ($LASTEXITCODE -ne 0) { throw 'Assembly encode failed' }
& ffmpeg -y -framerate 10 -i (Join-Path $taskPreview 'frames-explode\%04d.png') -i (Join-Path $taskPreview 'explode-overlay.png') -filter_complex '[0:v][1:v]overlay=0:0:format=auto,fps=30,format=yuv420p[v]' -map '[v]' -c:v libx264 -crf 18 -movflags +faststart (Join-Path $taskPreview 'explode-preview.mp4')
if ($LASTEXITCODE -ne 0) { throw 'Explosion encode failed' }
