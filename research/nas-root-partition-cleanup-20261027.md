# NAS root partition cleanup — 2026-10-27

## Scope and measurements

The requested Notes candidate and handoff were checked at exact commits
`7fccf15e11896f1f397f1d893fa2a8dab0876b0a` and
`675680844da62d3c9428595713c1d1859b917551`, respectively. Cleanup used a new
worktree from the latter; the existing dirty `ai-nas-lab/main` worktree and the
dirty Notes worktree were left untouched.

At start, `/` was `/dev/mmcblk1p2` (Btrfs), 6.2 GiB, 5.7 GiB used, 424 MiB
available, 94%. At finish it was 6.2 GiB, 4.9 GiB used, 1.1 GiB available,
82%. The kernel-reported available space rose by 713,162,752 bytes; Btrfs
reported used bytes fell by about 796 MB during the same interval. `df -i`
returns zero inode counters on this Btrfs filesystem, so inode utilization is
not reported by the mounted filesystem.

`/vol1` is a separate Btrfs mount with 353 GiB available after the move. `/tmp`
is tmpfs; clearing it does not change root capacity. The before/after checks
used `df`, `findmnt`, Btrfs usage, bounded `du` inventories, process listings,
and `lsof +L1`.

## Actions completed

- Moved the installed Google Cloud CLI 590.0.1 from
  `/home/admin/.local/opt/notes-google-cloud-cli` to
  `/vol1/Docker/.codex-admin/admin-tools/notes-google-cloud-cli-590.0.1`.
  The old path is now a symlink, so `/home/admin/bin/notes-gcloud` was not
  edited. The isolated ADC/config directory remains at
  `/home/admin/.local/state/notes-gcloud-home/.config/gcloud`; the ADC file
  still has mode 0600. No credential was read or printed.
- Verified `cp -a` completed, source and destination each have 41,691 entries
  and 430,620,256 apparent bytes, the `bin/gcloud` and `lib/gcloud.py` hashes
  match, and the copied SDK runs as version 590.0.1 with `sdk_root` under
  `/vol1`. Both the old-path wrapper and the staged symlink resolved the same
  isolated config directory. The destination's filesystem ACL yields more
  restrictive 0700 file modes than the original; the CLI version/info checks
  pass under the NAS admin account. A full-tree content-hash scan stalled on
  slow I/O and was stopped; there is no claim that a recursive content hash
  completed.
- Removed the exact duplicate npm/npx cache
  `/home/admin/.npm/_npx/67eb4586ca667318` (177,412,494 bytes). Its cached
  Vercel CLI was 65.4.0; the known-working 65.4.0 cache at
  `/home/admin/.npm/_npx/50e9ffea52bc6e2a` was retained and runs.
- Removed only the regenerable Node-gyp 22.23.4 header cache
  `/home/admin/.cache/node-gyp/22.23.4` (58,962,041 bytes) and pip HTTP cache
  `/home/admin/.cache/pip` (15,330,297 bytes). The rest of `.cache` remains.
- Removed the exact, already checksum-verified Google Cloud CLI 590.0.1 install
  tarball from `/tmp/gcloud-notes-install` (89,946,099 bytes on tmpfs) and its
  now-empty staging directory. It did not contribute to root free-space gain.

## Post-cleanup checks

- Root usage: 82%, 1.1 GiB available. `.npm` is 549 MiB, `.cache` 2.9 MiB,
  `.local` 91 MiB. The 100 MiB Gemini CLI, Node 22 and Node 24, and the known-
  working Vercel CLI cache remain available.
- `notes-gcloud version`: Google Cloud SDK 590.0.1; info reports the `/vol1`
  SDK root and the original isolated Notes config path. Vercel CLI reports
  65.4.0. Gemini CLI reports 0.65.0. `gemini-task --help` succeeds. No Gemini
  API request was made.
- The private Koofr snapshot directory remains mode 0700 and its gzip snapshot
  mode 0600, 404,736 bytes, SHA-256
  `3dd8ec69231dfc3afb8ca0e515958d2c7107fe61fe56a126bb62ff17692bdf7a`.
  No snapshot content was displayed, modified or moved.
- `lsof +L1` returned no deleted-but-open files. No Node/npm/npx/Vercel/Gemini/
  gcloud process was running after checks. `s25-adb` and both Tapo camera
  containers remained Up. Docker state, logs, backup jobs, app data, checkout
  content, source and reports were not cleaned or reset.

## Retained items and rollback

No credential, ADC, Vercel session, Gemini key/config, Notes state, migration
snapshot, checkout, source, report, Node installation, global Gemini package,
Docker data, camera state, or backup task was removed. APT indexes/cache and
system/application logs were not touched.

The gcloud wrapper itself is byte-for-byte unchanged. To revert the relocation,
copy `/vol1/Docker/.codex-admin/admin-tools/notes-google-cloud-cli-590.0.1`
back to `/home/admin/.local/opt/notes-google-cloud-cli`, replace the symlink
with that directory, then confirm `notes-gcloud version` and `sdk_root`. The
ADC/config directory is independent of this path change. Removed npm, Node-gyp
and pip cache entries are regenerable if later needed.

No Notes cutover, Firestore import, production write freeze, or production data
operation occurred.
