# basic_install

Basic Install - A Simplified Installation Framework

Welcome to Basic Install, your go-to solution for seamless and efficient software installation. This repository is designed to automate and simplify common installation tasks, making it an essential tool for developers, system administrators, and tech enthusiasts.

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

Ansible collections: this project requires `community.general`.

🔧 Installation

Clone the Repository:

`git clone https://github.com/saadmarcelo/basic_install.git`

`cd basic_install`

Edit file hosts and change IP addres and ansible_user

Install required Ansible collections:

`ansible-galaxy collection install -r collections/requirements.yml`

Run the Installer:

`ansible-playbook playbook.yaml -k -K`

-k user password

-K become password

after instalation connect to destination and open

`tmux`

`crtl+b I`

to install tmux plugins

open nvim and wait nvim plugins instalation

`nvim`

Follow On-Screen Instructions: The script will guide you through any additional setup.

macOS notes:

- The macOS playbook supports both Apple Silicon (`/opt/homebrew`) and Intel (`/usr/local`) Homebrew installs.
- The macOS installation validates that Neovim is at least `0.12.x` and fails if an older `0.x` version is installed.

Tests:

`python3 -m unittest discover -s tests -v`

Syntax check:

`ansible-playbook playbook.yaml --syntax-check -i localhost, -c local`

📦 Supported Software

The following software and services are supported out of the box:

Development Tools (e.g., Git, Node.js, Python)

Essential Utilities (neovim, tmux, bat, zoxide, zsh, eza, fzf )

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
