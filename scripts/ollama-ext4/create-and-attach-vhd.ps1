# create-and-attach-vhd.ps1 — T-67 step 1 (run in an ELEVATED Windows PowerShell)
# Creates a dynamic ext4-destined VHDX on I: (NVMe, 399 GB free) and attaches it
# RAW to WSL2 so we can mkfs.ext4 it inside Linux. Does NOT format (that happens
# inside WSL, by-size-verified, to avoid touching the wrong device).
$ErrorActionPreference = 'Stop'
$VhdDir  = 'I:\wsl-ollama'
$VhdPath = Join-Path $VhdDir 'ollama-store.vhdx'
$SizeGB  = 300   # dynamic: only consumes actual used space (~162 GB to start)

if (-not (Test-Path $VhdDir)) { New-Item -ItemType Directory -Path $VhdDir | Out-Null }
if (Test-Path $VhdPath) { throw "Already exists: $VhdPath (aborting so we never clobber data)" }

Write-Host "Creating dynamic VHDX ($SizeGB GB max) at $VhdPath ..."
New-VHD -Path $VhdPath -SizeBytes ($SizeGB * 1GB) -Dynamic | Out-Null

Write-Host "Attaching RAW to WSL2 (block device, no auto-mount) ..."
wsl --mount --vhd "$VhdPath" --bare

Write-Host ""
Write-Host "DONE. The vhd is attached. Now switch to WSL and run, carefully:"
Write-Host "  lsblk -o NAME,SIZE,TYPE,MOUNTPOINT     # find the NEW ~$SizeGB G disk"
Write-Host "  (verify the device is the empty $SizeGB G disk, NOT /dev/sdd = your OS)"
Write-Host "Path for later steps: $VhdPath"
