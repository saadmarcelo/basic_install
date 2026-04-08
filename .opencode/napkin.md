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

**Learnings:**
- This repo installs software through Ansible playbooks for macOS and Debian/Ubuntu.
- `neovim` was previously installed from moving package repositories and was not version-guaranteed.

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
