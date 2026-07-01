# register-logon-task.ps1 — T-67/T-68 persistence (run ELEVATED, AFTER the move works)
# `wsl --mount` does NOT survive reboot. This registers a logon task that
# re-attaches the vhd. That is ALL it does — attaching the disk raises a udev
# 'add' event inside WSL, and 99-ollama-store.rules + ollama-store-recover.service
# bring the mount + ollama online from there (Option A, T-68). Keeping the task
# to a single hypervisor operation removes the cold-start race that made the old
# two-step task fail at logon (LastTaskResult=1: WSL/systemd not ready yet for the
# chained `systemctl restart`).
$ErrorActionPreference = 'Stop'
$VhdPath = 'I:\wsl-ollama\ollama-store.vhdx'

# Attach the disk only. The in-WSL udev rule + recovery service do the rest.
$cmd = "wsl --mount --vhd `"$VhdPath`" --bare"

$action  = New-ScheduledTaskAction -Execute 'powershell.exe' `
             -Argument "-NoProfile -WindowStyle Hidden -Command `"$cmd`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$set     = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName 'WSL-Ollama-ext4-store' -Action $action `
  -Trigger $trigger -Settings $set -RunLevel Highest -Force
Write-Host "Registered logon task 'WSL-Ollama-ext4-store' (attach-only; udev self-heals inside WSL)."
