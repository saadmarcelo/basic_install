import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


class PlaybookRoutingTests(unittest.TestCase):
    def test_main_playbook_routes_macos_to_unified_role(self) -> None:
        content = read_text("playbook.yaml")
        self.assertIn("roles/macos/tasks/main.yaml", content)
        self.assertNotIn("roles/brew_macOS.yaml", content)
        self.assertNotIn("roles/zsh_macOS.yaml", content)

    def test_main_playbook_keeps_linux_role(self) -> None:
        content = read_text("playbook.yaml")
        self.assertIn("roles/linux/tasks/main.yaml", content)
        self.assertIn("ansible_facts['os_family'] == 'Debian'", content)


class AnsibleDependencyTests(unittest.TestCase):
    def test_repo_declares_community_general_collection(self) -> None:
        content = read_text("collections/requirements.yml")
        self.assertIn("collections:", content)
        self.assertIn("- name: community.general", content)


class LinuxInstallationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.content = read_text("roles/linux/tasks/main.yaml")

    def test_linux_keeps_official_neovim_release_install(self) -> None:
        self.assertIn("/opt/nvim-linux-x86_64/bin/nvim", self.content)
        self.assertIn("nvim-linux-x86_64.tar.gz", self.content)
        self.assertRegex(self.content, r"neovim_version_series:\s*\"0\.12\"")

    def test_linux_keeps_python_venv_and_isort(self) -> None:
        self.assertIn("python3 -m venv {{ venv_path }}", self.content)
        self.assertIn("name: isort", self.content)

    def test_linux_keeps_dotfiles_and_tmux_setup(self) -> None:
        self.assertIn("https://github.com/saadmarcelo/dotfiles.git", self.content)
        self.assertIn("https://github.com/tmux-plugins/tpm.git", self.content)
        self.assertIn("stow -R -d /home/{{ ansible_user }}/dotfiles", self.content)


class MacOSInstallationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.content = read_text("roles/macos/tasks/main.yaml")

    def test_macos_supports_both_homebrew_prefixes(self) -> None:
        self.assertIn("/opt/homebrew/bin/brew", self.content)
        self.assertIn("/usr/local/bin/brew", self.content)
        self.assertIn("NONINTERACTIVE", self.content)

    def test_macos_installs_core_tooling_parity(self) -> None:
        for package in [
            "- bat",
            "- eza",
            "- fd",
            "- fzf",
            "- git",
            "- lazygit",
            "- neovim",
            "- node",
            "- python",
            "- ripgrep",
            "- stow",
            "- tmux",
            "- zoxide",
            "- zsh",
        ]:
            with self.subTest(package=package):
                self.assertIn(package, self.content)

    def test_macos_installs_shell_and_dotfiles_workflow(self) -> None:
        self.assertIn("KEEP_ZSHRC: \"yes\"", self.content)
        self.assertIn("https://github.com/saadmarcelo/dotfiles.git", self.content)
        self.assertIn("https://github.com/zsh-users/zsh-autosuggestions", self.content)
        self.assertIn("https://github.com/zsh-users/zsh-completions", self.content)
        self.assertIn("https://github.com/zsh-users/zsh-syntax-highlighting.git", self.content)
        self.assertIn('stow -R -d "{{ dotfiles_path }}" -t "{{ target_home }}"', self.content)

    def test_macos_installs_tmux_and_fzf_integrations(self) -> None:
        self.assertIn("https://github.com/tmux-plugins/tpm.git", self.content)
        self.assertIn("install_plugins", self.content)
        self.assertIn("{{ homebrew_prefix }}/opt/fzf/install --all --no-bash --no-fish", self.content)

    def test_macos_keeps_python_venv_and_neovim_validation(self) -> None:
        self.assertIn("{{ homebrew_prefix }}/bin/python3 -m venv {{ venv_path }}", self.content)
        self.assertIn("name: isort", self.content)
        self.assertIn("- name: Consultar versao do Neovim no macOS", self.content)
        self.assertIn('ansible.builtin.command: "{{ homebrew_prefix }}/bin/nvim --version"', self.content)
        self.assertIn("register: macos_neovim_version", self.content)
        self.assertIn("- name: Validar Neovim 0.12+ no macOS", self.content)
        self.assertIn("ansible.builtin.assert:", self.content)
        self.assertIn("^NVIM v0\\.(1[2-9]|[2-9][0-9])\\.", self.content)
        self.assertIn("Neovim no macOS precisa ser 0.12+", self.content)


if __name__ == "__main__":
    unittest.main()
