# register-logon-task.ps1 — T-67 persistence (run ELEVATED, AFTER the move works)
# `wsl --mount` does NOT survive reboot. This registers a logon task that
# re-attaches the vhd and restarts the mount + ollama, so the store comes back
# automatically. Without this, after a reboot `make ollama-store-check` FAILs and
# ollama refuses to start (loud, by design) until the vhd is re-attached.
$ErrorActionPreference = 'Stop'
$VhdPath = 'I:\wsl-ollama\ollama-store.vhdx'
$MountUnit = 'mnt-ollama\x2dstore.mount'   # systemd-escaped /mnt/ollama-store

# Attach the disk, then (re)start the mount + ollama inside WSL once it's present.
$cmd = "wsl --mount --vhd `"$VhdPath`" --bare; " +
       "wsl -u root -- systemctl restart '$MountUnit' ollama"

$action  = New-ScheduledTaskAction -Execute 'powershell.exe' `
             -Argument "-NoProfile -WindowStyle Hidden -Command `"$cmd`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$set     = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName 'WSL-Ollama-ext4-store' -Action $action `
  -Trigger $trigger -Settings $set -RunLevel Highest -Force
Write-Host "Registered logon task 'WSL-Ollama-ext4-store'."
