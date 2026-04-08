# Napkin - basic_install

> Persistent memory of mistakes, corrections, and learnings

## Session Log

### 2026-04-08 - Session 1

**Mistakes:**
- Initial Linux Neovim install logic compared only versions and did not account for whether the official `/opt/nvim-linux-x86_64` installation already existed.

**Corrections:**
- User wants Neovim version guarantees only on Linux, not macOS.
- User only needs Linux `amd64` support.
- Added a filesystem check so the playbook reinstalls Neovim when the official install path is missing, even if some other `nvim 0.11.x` is already on the machine.
- User later changed the target version family from `0.11.x` to `0.12.x`; keep the version series easy to update.
- Refactored the playbook so the Neovim series is controlled by one variable instead of repeated regex literals.

**Learnings:**
- This repo installs software through Ansible playbooks for macOS and Debian/Ubuntu.
- `neovim` was previously installed from moving package repositories and was not version-guaranteed.
- The Neovim version family may change quickly, so hardcoded series checks are a likely maintenance point.

## Patterns

### Recurring Issues
- Package manager installs are not sufficient when the user needs a constrained version series.

### Solutions That Work
- Prefer official release artifacts when a reproducible version family must be enforced.

## Preferences

### User Preferences
- Keep the Neovim version guarantee limited to Linux.
- Linux target architecture is `amd64`.

### Environment Notes
- Repository is a small Ansible-based bootstrap project.
