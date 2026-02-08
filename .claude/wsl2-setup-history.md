# WSL2 Setup History (Phase 0 Archive)

**Created:** 2026-02-02
**Completed:** 2026-02-03
**Status:** ✅ RESOLVED - WSL2 + GPU passthrough working

---

## Summary

This file documents the troubleshooting journey to get WSL2 working with GPU passthrough. The blocker was `hypervisorlaunchtype=Off` in the Windows boot configuration.

---

## Completed Steps

- [x] Verified GPU: RTX 3060 12GB, driver 591.74 ✅
- [x] Verified VT-x enabled in BIOS ✅
- [x] WSL installed (version 2.6.3.0) ✅
- [x] Ubuntu-22.04 installed (initially WSL1) ✅
- [x] Ran `wsl --install --no-distribution` in elevated PowerShell
- [x] Diagnosed hypervisorlaunchtype issue
- [x] Applied fix: `bcdedit /set hypervisorlaunchtype auto`
- [x] Restarted computer
- [x] Ubuntu-22.04 converted to WSL2 ✅
- [x] GPU passthrough verified: `nvidia-smi` works ✅

---

## The Blocker & Resolution

### Symptom
```
wsl --set-version Ubuntu-22.04 2
# Error: HCS_E_HYPERV_NOT_INSTALLED
```

### Root Cause
`hypervisorlaunchtype` was set to `Off` in boot configuration, even though all Windows features were enabled.

### Solution
```powershell
bcdedit /set hypervisorlaunchtype auto
# Restart required
```

### Verification
```powershell
wsl -l -v
# Ubuntu-22.04    VERSION 2  ✅

wsl -d Ubuntu-22.04 -e nvidia-smi
# Shows RTX 3060 with 12GB VRAM  ✅
```

---

## Diagnostic Commands Used

```powershell
# Check Windows features
Get-WindowsOptionalFeature -Online | Where-Object {$_.FeatureName -like "*Virtual*" -or $_.FeatureName -like "*WSL*" -or $_.FeatureName -like "*Hyper*"}

# Check Hyper-V services
Get-Service | Where-Object {$_.Name -like "*hv*" -or $_.Name -like "*vmcompute*"}

# Check boot configuration
bcdedit /enum | findstr hypervisorlaunchtype
```

---

## Lessons Learned

1. **Windows features ≠ hypervisor enabled**: Even with VirtualMachinePlatform, Hyper-V, and HypervisorPlatform all "Enabled", the hypervisor won't launch if `bcdedit` has it disabled.

2. **Check bcdedit early**: When WSL2 fails with hypervisor errors, check `bcdedit /enum` before anything else.

3. **Some tools disable hypervisor**: Android emulators, VMware, and certain performance tools may set `hypervisorlaunchtype Off` for compatibility.
