# basic_install

Basic Install - A Simplified Installation Framework

Ansible playbooks that bootstrap a development machine (shell, editor, tmux, CLI tools and dotfiles) on Ubuntu/Debian (amd64) and macOS (Apple Silicon and Intel).

🚀 Key Features

Ease of Use: Intuitive scripts for quick setup.

Cross-Platform: Compatibility with multiple operating systems (ubuntu/debian and MacOS).

Modular Design: Easily customize and extend functionalities.

Time-Saving: Automates repetitive tasks to boost productivity.

📋 Prerequisites

Before you get started, ensure you have the following:

Operating System: Linux (Ubuntu/Debian) or MacOS.

Package Manager: apt, brew, or others depending on your OS.

Permissions: Admin/root access may be required for certain installations.

Ansible collections: `community.general` and `ansible.posix` (see `collections/requirements.yml`).

🔧 Installation

Clone the Repository:

`git clone https://github.com/saadmarcelo/basic_install.git`

`cd basic_install`

Edit file `hosts`: change the IP address and `ansible_user` (for the local machine, uncomment the `localhost` line).

Install required Ansible collections:

`ansible-galaxy collection install -r collections/requirements.yml`

Run the Installer:

`ansible-playbook playbook.yaml -K`

-K become password (add `-k` to also type the SSH password if you do not use the key set in `hosts`)

Optional: `-e github_token=<token>` avoids the GitHub API rate limit (60 requests/hour per IP).

after installation connect to the destination and open nvim; wait for the plugin installation (tmux plugins are installed by the playbook)

`nvim`

macOS notes:

- The macOS playbook supports both Apple Silicon (`/opt/homebrew`) and Intel (`/usr/local`) Homebrew installs.
- The macOS installation validates that Neovim is at least `0.12.x` and fails if an older `0.x` version is installed.

Tests (need PyYAML: `pip install pyyaml`, or use the Python that ships with Ansible):

`python3 -m unittest discover -s tests -v`

Lint:

`ansible-lint`

Syntax check:

`ansible-playbook playbook.yaml --syntax-check -i localhost, -c local`

📦 Supported Software

The following software and services are supported out of the box:

Development Tools: git, Node.js, Python (venv + isort), Go, Lua/LuaRocks, lazygit, ansible-lint

Essential Utilities: neovim, tmux, bat, zoxide, zsh + Oh My Zsh, eza, fzf, fd, ripgrep, stow

macOS only: kitty, Raycast, Flycut, Rectangle, yazi

Product requirements and known issues: `docs/PRD.md`

🛠️ Customization

Feel free to modify the playbook.yaml script or other files in the repository to suit your specific needs. Contributions are welcome; check out the Contributing section below!

🤝 Contributing

We’d love your help! To contribute:

Fork the repository.

Create a feature branch (git checkout -b feature-name).

Commit your changes (git commit -m 'Add new feature').

Push to the branch (git push origin feature-name).

Open a pull request.

🧑‍💻 About the Author

Marcelo Saad is a passionate developer and tech enthusiast dedicated to creating tools that simplify technology. Connect with me on LinkedIn or explore my other projects on GitHub.

🛡️ License

This project is licensed under the MIT License.

⭐ Support the Project

If you find this project helpful, consider giving it a star on GitHub and sharing it with your network! Contributions, feedback, and suggestions are always welcome.
