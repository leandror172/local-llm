#!/usr/bin/env bash
# ollama-store-guard.sh — installed to /usr/local/bin, wired as ollama's
# ExecStartPre. Aborts ollama startup (nonzero exit) if the model store is not a
# populated ext4 filesystem — so ollama can NEVER silently start on an empty
# fallback store after a missing-vhd-mount (T-67). Belt-and-suspenders over the
# systemd `Requires=` on the .mount unit.
set -u
STORE="${OLLAMA_MODELS:-/mnt/ollama-store/models}"
MIN_BLOBS="${MIN_BLOBS:-50}"

fstype="$(findmnt -n -o FSTYPE --target "$STORE" 2>/dev/null)"
if [[ "$fstype" != "ext4" ]]; then
  echo "ollama-store-guard: REFUSING START — store '$STORE' is on '${fstype:-missing}', not ext4." >&2
  echo "ollama-store-guard: the dedicated ext4 vhdx is probably not attached/mounted." >&2
  exit 1
fi
blobs=$(find "$STORE/blobs" -maxdepth 1 -type f 2>/dev/null | wc -l)
if (( blobs < MIN_BLOBS )); then
  echo "ollama-store-guard: REFUSING START — only $blobs blobs in '$STORE' (< $MIN_BLOBS); store looks empty." >&2
  exit 1
fi
echo "ollama-store-guard: OK — store on ext4 with $blobs blobs."
exit 0
