# PRD — basic_install

Status: rascunho derivado do código existente (2026-10-29). Dono: Marcelo Saad.

## 1. Resumo

`basic_install` é um bootstrap Ansible que prepara uma máquina de desenvolvimento
(shell, editor, multiplexador, ferramentas CLI, dotfiles) a partir de um único comando.
Detecta o SO via fact `os_family` e roda o fluxo de Linux (Debian/Ubuntu, amd64) ou macOS
(Homebrew, Apple Silicon e Intel).

## 2. Problema

Montar um ambiente de desenvolvimento novo à mão é lento e gera divergência entre
máquinas (versão do Neovim, plugins do tmux, dotfiles). O projeto torna o setup
repetível e idempotente.

## 3. Objetivos

- G1. Um comando provisiona uma máquina nova, local ou via SSH.
- G2. Paridade funcional entre Linux e macOS nas ferramentas centrais.
- G3. Neovim na série `0.12.x` no Linux (versão controlada por uma variável); no macOS exige `>= 0.12`.
- G4. Reexecutar o playbook não quebra nada e não altera estado desnecessariamente (idempotência).
- G5. Dotfiles (`saadmarcelo/dotfiles`) aplicados com GNU Stow para `nvim`, `tmux`, `zshrc` (+ `kitty` no macOS).

## 4. Não-objetivos

- Windows, Linux não-Debian, Linux ARM (decisão do dono: só `amd64`).
- Garantia de versão do Neovim no macOS além do piso 0.12.
- Gerenciar segredos, chaves SSH ou configuração de apps GUI além da instalação.

## 5. Usuários

Um único usuário-alvo: o dono do repositório, em máquinas pessoais ou servidores de dev.
Secundário: quem faz fork para o próprio setup.

## 6. Escopo funcional

### 6.1 Roteamento (`playbook.yaml`)
- FR-1. `hosts: all`, `become: true`, `gather_facts: true`, `venv_path=/opt/venv`.
- FR-2. `Darwin` inclui `roles/macos/tasks/main.yaml`; `Debian` inclui `roles/linux/tasks/main.yaml`.
- FR-3. Outros SOs mostram mensagem de "não suportado".

### 6.2 Linux (`roles/linux/tasks/main.yaml`)
- FR-L1. NodeSource 22.x + pacotes APT (git, stow, tmux, zsh, fd-find, ripgrep, bat, zoxide, eza, golang, lua, luarocks, build tools, locales etc.).
- FR-L2. Remove `neovim` do APT; instala tarball oficial em `/opt/nvim-linux-x86_64` com link em `/usr/local/bin/nvim`; consulta a API do GitHub pela última release `0.12.x`, com fallback `v0.12.0`; valida a versão final.
- FR-L3. Instala `npm` (APT) somente se houver Ubuntu Desktop (evita conflito com NodeSource).
- FR-L4. venv Python em `/opt/venv` com pip/setuptools/wheel/isort; `pipx` e `ansible-lint`.
- FR-L5. Locale `en_US.UTF-8` (dependência do fzf).
- FR-L6. lazygit (última release), fzf `v0.57.0`, fonte SauceCodePro Nerd Font `v3.0.2`.
- FR-L7. Oh My Zsh + plugins (autosuggestions, completions, syntax-highlighting) para o usuário e para `root`; zsh como shell padrão.
- FR-L8. TPM + plugins do tmux; clone dos dotfiles; `stow` de tmux/nvim/zshrc para o usuário e `root`.

### 6.3 macOS (`roles/macos/tasks/main.yaml`)
- FR-M1. Detecta Homebrew em `/opt/homebrew` ou `/usr/local`; instala não interativo se faltar; tarefas brew rodam com `become: false`.
- FR-M2. Casks: font-sauce-code-pro-nerd-font, flycut, kitty, raycast, rectangle.
- FR-M3. Fórmulas: bat, eza, fd, fzf, git, go, lazygit, lua, luarocks, neovim, node, python, ripgrep, stow, tmux, wget, yazi, zoxide, zsh.
- FR-M4. zsh do Homebrew em `/etc/shells` e como shell padrão; venv + isort; Oh My Zsh (`KEEP_ZSHRC=yes`); dotfiles; stow de nvim/tmux/zshrc/kitty; TPM; integrações do fzf.
- FR-M5. Falha se o Neovim for menor que 0.12.

## 7. Requisitos não-funcionais

- NFR-1. Idempotência: segunda execução sem mudanças reportadas (hoje violado, ver §9).
- NFR-2. Reprodutibilidade: versões fixadas ou política explícita de "latest" documentada.
- NFR-3. Segurança: sem `curl | bash` de branch móvel sem verificação onde houver alternativa; arquivos temporários não previsíveis; nada rodando como root dentro de `$HOME` do usuário sem `chown`.
- NFR-4. Qualidade: `ansible-lint` sem violações; `--syntax-check` limpo; testes unitários verdes.
- NFR-5. Dependências declaradas: todas as collections usadas (e as do `ansible.cfg`) em `collections/requirements.yml`.

## 8. Arquitetura e arquivos

| Caminho | Função |
|---|---|
| `playbook.yaml` | Play único, roteia por SO |
| `roles/linux/tasks/main.yaml` | Fluxo Debian/Ubuntu (457 linhas) |
| `roles/macos/tasks/main.yaml` | Fluxo macOS (247 linhas) |
| `hosts` | Inventário (IP fixo + chave SSH; localhost comentado) |
| `ansible.cfg` | Configuração local |
| `collections/requirements.yml` | `community.general` |
| `tests/` | Testes unitários (`unittest`) |
| `macOS.yaml` | Legado, 100% comentado |

Nota: `roles/` não são roles de verdade (sem `defaults/`, `vars/`, `meta/`); são arquivos de tarefas incluídos por caminho.

## 9. Problemas conhecidos (backlog priorizado)

Itens P1 resolvidos têm teste normal; os P2 abertos têm teste `expectedFailure` em `tests/test_playbook_structure.py`.

### P1 — bugs funcionais (itens 1–6 corrigidos em 2026-10-29)
1. Linux: plugins do tmux instalados **antes** do stow do `tmux.conf` — `install_plugins` não encontra plugins para instalar (por isso o README pede `ctrl+b I` manual). No macOS a ordem está certa.
2. Linux: plugins do zsh clonados com `become: true` dentro do `$HOME` do usuário — arquivos ficam como `root`.
3. macOS: `fzf/install --all` altera `~/.zshrc`, que após o stow é symlink para o repositório de dotfiles — suja o repo.
4. `ansible.cfg` habilita `profile_tasks` (`ansible.posix`) que não está em `requirements.yml`; falha em instalação só com `ansible-core`.
5. macOS: `target_user`/`target_home` dependem de `ansible_user`, indefinido no uso local (linha do localhost está comentada no `hosts`). Usar `ansible_facts['user_id']`.
6. Linux: `/home/{{ ansible_user }}` assumido; quebra com `ansible_user=root` (lista `users` duplica root) ou home não padrão.

### P2 — idempotência e correção (itens 7–14 corrigidos em 2026-10-29; `yazi` segue só no macOS, `wget` já existia no Linux)
7. Linux: `chsh` executado duas vezes (linha 266 antes de garantir `/etc/shells`, e linha 350), sem `changed_when`.
8. Linux: "Recarregar locale" com `source` em subshell não faz nada; "Verificar o shell atual" usa `command: echo $SHELL` (sem expansão, imprime literal).
9. Linux: lazygit roda toda vez, baixa no CWD, usa `sudo` dentro de `become`, sem `pipefail`, versão flutuante.
10. Linux: `fd-find` instala o binário `fdfind`; sem alias `fd` (o macOS tem `fd`), Telescope/plugins esperam `fd`.
11. Linux: `/usr/local/share/fonts` pode não existir (unarchive falha); `fc-cache` sempre "changed"; fzf re-extraído sempre e fixado em v0.57.0 enquanto o macOS usa a última.
12. Paridade: `ansible-lint` só no Linux; `kitty` só no macOS (aceitável); `yazi`, `wget` só no macOS.
13. Linux: sem checagem de `ansible_architecture` (tarballs são amd64); `eza` não existe em Ubuntu 22.04 ou anterior, e derruba a task de pacotes inteira.
14. `chsh` no macOS roda como root por herança de `become` e com `changed_when: false` (esconde mudanças).

### P3 — segurança e higiene
15. `curl | bash` de Homebrew, Oh My Zsh (`master`) e NodeSource sem checksum/pin; API do GitHub sem token (limite 60/h por IP) em duas tarefas.
16. Tarballs em `/tmp` com nome previsível, baixados como root.
17. `hosts`: IP privado fixo e `id_rsa` no repo; README manda usar `-k` (senha) mas o inventário usa chave.
18. `ansible.cfg`: `library=/usr/share/my_modules` inexistente; `interpreter_python=/usr/bin/python3` (stub do Xcode no macOS); `ansible_managed` deprecated (removido no core 2.23); `module_name=command` incomum.
19. `macOS.yaml`: código morto, caminho errado (`/usr/homebrew/bin/brew`), variáveis indefinidas. Remover.
20. `tests/__pycache__/*.pyc` versionado e `.gitignore` sem `__pycache__`/`.ansible/`. `.opencode/napkin.md` (notas de agente) versionado.
21. `ansible-lint`: 26 `var-naming[no-role-prefix]`, 19 `no-changed-when`, 8 `latest[git]`, 3 `risky-file-permissions`, 2 `risky-shell-pipe`, 2 `partial-become`, 1 `command-instead-of-module`.
22. Pacotes instalados com `loop` + `package` (27 chamadas); passar a lista inteira de uma vez.
23. README: texto de marketing, "Follow On-Screen Instructions" (não há scripts interativos), `crtl+b` (typo), "Supported Software" desatualizado, cita licença MIT sem arquivo `LICENSE`, não documenta teste/PyYAML.

## 10. Critérios de aceite

- AC-1. `ansible-playbook playbook.yaml --syntax-check -i localhost, -c local` sem erros.
- AC-2. `ansible-lint` sem violações (ou ignores documentados).
- AC-3. Segunda execução em VM Ubuntu 24.04 limpa e em macOS: `changed=0`.
- AC-4. Após o playbook, `tmux` já abre com plugins instalados e `nvim --version` é 0.12.x.
- AC-5. `python -m unittest discover -s tests` verde, sem `expectedFailure` restantes após o backlog P1–P2.

## 11. Estratégia de testes

| Camada | Ferramenta | Cobertura |
|---|---|---|
| Estática | `yamllint`, `ansible-lint`, `--syntax-check` | Sintaxe e boas práticas |
| Unitária estrutural | `unittest` + PyYAML (`tests/test_playbook_structure.py`) | Ordem das tarefas, `become`, listas de pacotes, regex de versão, config |
| Regressão textual | `unittest` (`tests/test_installation_playbooks.py`) | URLs e strings críticas |
| Integração (futuro) | Molecule/Docker (Ubuntu 24.04), runner macOS no CI | Idempotência real |

Como rodar:

```
pip install pyyaml            # ou use o Python do Ansible
python3 -m unittest discover -s tests -v
```

Testes `expectedFailure` documentam bugs abertos: ao corrigir um, o runner reporta
"unexpected success" e o decorator deve ser removido.

## 12. Riscos e perguntas abertas

- Política de versão: fixar tudo (reprodutível) ou "latest" (menos manutenção)? Hoje é misto.
- Manter o stow do `root` apontando para dotfiles do usuário, ou dar a `root` cópia própria?
- Adicionar CI (GitHub Actions) com runner Ubuntu + macOS?
- Transformar `roles/*` em roles reais (`defaults/main.yaml`, prefixo de variáveis) resolve a maior parte do lint.
