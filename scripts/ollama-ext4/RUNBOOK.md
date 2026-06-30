# T-67 execution runbook — move Ollama store to a dedicated ext4 vhdx

Target: store on real ext4 (mmap works) at `/mnt/ollama-store/models`, vhdx file on
I: (NVMe), persistent across reboots, with a loud-fail guard so ollama never starts
on an empty fallback store.

Legend: **[WIN]** = elevated Windows PowerShell · **[SUDO]** = `sudo` in WSL · **[ME]** = Claude runs.

---

### Step 1 — create + attach the vhd  **[WIN]**
```powershell
I:\…\llm\scripts\ollama-ext4\create-and-attach-vhd.ps1
# (or the WSL path: \\wsl.localhost\… — easiest: copy the .ps1 to Windows and run)
```
Then report `lsblk -o NAME,SIZE,TYPE,MOUNTPOINT` output back.

### Step 2 — format the NEW device  **[SUDO]** ⚠ DATA-LOSS IF WRONG DEVICE
Identify the empty **~300 G** disk with NO mountpoint and NO children. `/dev/sdd` is
the OS — never touch it. Confirm the device with `lsblk` first, then:
```bash
sudo mkfs.ext4 -L ollama-store /dev/sdX      # sdX = the new 300G disk, VERIFIED
```

### Step 3 — mount + hand ownership to your user  **[SUDO]**
```bash
sudo mkdir -p /mnt/ollama-store
sudo mount /dev/sdX /mnt/ollama-store
sudo install -d -o "$USER" -g "$USER" /mnt/ollama-store/models
blkid /dev/sdX        # copy the UUID="..." — needed for the .mount unit
```

### Step 4 — copy the 162 GB store  **[ME]**
```bash
rsync -aH --info=progress2 /mnt/i/ollama-models/ /mnt/ollama-store/models/
# then verify blob+manifest counts match the source (178 / 81)
```

### Step 5 — install the systemd mount unit + guard, repoint ollama  **[SUDO]**
```bash
sudo install -m755 scripts/ollama-ext4/ollama-store-guard.sh /usr/local/bin/

# /etc/systemd/system/mnt-ollama\x2dstore.mount  (use the UUID from step 3)
sudo tee '/etc/systemd/system/mnt-ollama\x2dstore.mount' >/dev/null <<EOF
[Unit]
Description=Ollama ext4 model store (dedicated vhdx)
[Mount]
What=UUID=<PASTE-UUID>
Where=/mnt/ollama-store
Type=ext4
Options=defaults,nofail
[Install]
WantedBy=multi-user.target
EOF

# ollama override: point at the new store, require the mount, add the guard.
sudo install -d /etc/systemd/system/ollama.service.d
sudo tee /etc/systemd/system/ollama.service.d/ext4-store.conf >/dev/null <<'EOF'
[Unit]
Requires=mnt-ollama\x2dstore.mount
After=mnt-ollama\x2dstore.mount
[Service]
Environment="OLLAMA_MODELS=/mnt/ollama-store/models"
ExecStartPre=/usr/local/bin/ollama-store-guard.sh
EOF

# IMPORTANT: also remove the old `Requires=mnt-i.mount` / OLLAMA_MODELS=/mnt/i/...
# line in the existing override.conf so the two don't fight.
sudoedit /etc/systemd/system/ollama.service.d/override.conf

sudo systemctl daemon-reload
sudo systemctl enable 'mnt-ollama\x2dstore.mount'
sudo systemctl restart 'mnt-ollama\x2dstore.mount' ollama
```

### Step 6 — verify  **[ME]**
```bash
make -C ~/workspaces ollama-store-check       # expect PASS (ext4)
curl …/api/generate -d '{"model":"my-go-qcoder",…}'   # expect 200, no ENOMEM
journalctl -u ollama | grep -i UseMmap        # should NOT be false now
```

### Step 7 — persistence + cleanup  **[WIN]** / **[ME]**
```powershell
…\llm\scripts\ollama-ext4\register-logon-task.ps1     # [WIN] survive reboot
```
```bash
# [ME] after a reboot test passes, reclaim I: space:
rm -rf /mnt/i/ollama-models       # frees 162 GB on I:
# optionally lower .wslconfig memory back toward default (mmap makes 24G non-load-bearing)
```

### Rollback
Repoint `OLLAMA_MODELS` back to `/mnt/i/ollama-models`, `daemon-reload`, restart ollama.
The original store stays untouched until Step 7's `rm`.
