"""Structural unit tests: parse the YAML and assert on tasks, not on raw text.

Needs PyYAML (`pip install pyyaml`, or run with the Python that ships with Ansible).
Tests marked `expectedFailure` document known defects (see docs/PRD.md, section
"Known issues"). When a defect is fixed the test turns into an "unexpected
success", which tells you to remove the decorator.
"""
import configparser
import re
import unittest
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


ROOT = Path(__file__).resolve().parents[1]

TASK_KEYWORDS = {
    "name", "args", "become", "become_user", "changed_when", "failed_when",
    "environment", "loop", "when", "register", "until", "retries", "delay",
    "vars", "tags", "block", "rescue", "always", "notify", "with_items",
    "ignore_errors", "no_log", "delegate_to", "check_mode", "diff",
}


def load_tasks(relative_path: str) -> list:
    with (ROOT / relative_path).open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data or []


def module_of(task: dict) -> str:
    return next(key for key in task if key not in TASK_KEYWORDS)


def find_task(tasks: list, name: str) -> dict:
    for task in tasks:
        if task.get("name") == name:
            return task
    raise AssertionError(f"task not found: {name}")


def index_of(tasks: list, name: str) -> int:
    return tasks.index(find_task(tasks, name))


@unittest.skipIf(yaml is None, "PyYAML not installed")
class YamlHygieneTests(unittest.TestCase):
    FILES = [
        "playbook.yaml",
        "roles/linux/tasks/main.yaml",
        "roles/macos/tasks/main.yaml",
    ]

    def test_files_parse_as_yaml_lists(self) -> None:
        for path in self.FILES:
            with self.subTest(path=path):
                self.assertIsInstance(load_tasks(path), list)

    def test_every_task_has_a_name(self) -> None:
        for path in self.FILES[1:]:
            for task in load_tasks(path):
                with self.subTest(path=path, task=task):
                    self.assertTrue(task.get("name"))

    def test_task_names_are_unique_per_file(self) -> None:
        for path in self.FILES[1:]:
            names = [task["name"] for task in load_tasks(path)]
            with self.subTest(path=path):
                self.assertEqual(len(names), len(set(names)))

    def test_modules_use_fully_qualified_names(self) -> None:
        for path in self.FILES[1:]:
            for task in load_tasks(path):
                with self.subTest(path=path, task=task["name"]):
                    self.assertIn(".", module_of(task))


@unittest.skipIf(yaml is None, "PyYAML not installed")
class PlaybookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.play = load_tasks("playbook.yaml")[0]

    def test_play_targets_all_hosts_and_gathers_facts(self) -> None:
        self.assertEqual(self.play["hosts"], "all")
        self.assertTrue(self.play["gather_facts"])

    def test_venv_path_is_defined_for_both_roles(self) -> None:
        self.assertEqual(self.play["vars"]["venv_path"], "/opt/venv")

    def test_each_os_family_includes_exactly_one_role(self) -> None:
        includes = {
            task["ansible.builtin.include_tasks"]: task["when"]
            for task in self.play["tasks"]
            if "ansible.builtin.include_tasks" in task
        }
        self.assertEqual(set(includes), {
            "roles/macos/tasks/main.yaml",
            "roles/linux/tasks/main.yaml",
        })
        self.assertIn("'Darwin'", includes["roles/macos/tasks/main.yaml"])
        self.assertIn("'Debian'", includes["roles/linux/tasks/main.yaml"])

    def test_included_role_files_exist(self) -> None:
        for task in self.play["tasks"]:
            path = task.get("ansible.builtin.include_tasks")
            if path:
                with self.subTest(path=path):
                    self.assertTrue((ROOT / path).is_file())

    def test_unsupported_os_message_covers_the_complement(self) -> None:
        task = find_task(self.play["tasks"], "Mensagem para sistema operacional não suportado")
        self.assertIn("not in ['Darwin', 'Debian']", task["when"])


@unittest.skipIf(yaml is None, "PyYAML not installed")
class MacOSRoleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tasks = load_tasks("roles/macos/tasks/main.yaml")

    def test_homebrew_and_user_space_tasks_do_not_inherit_become(self) -> None:
        user_modules = {
            "community.general.homebrew",
            "community.general.homebrew_cask",
            "ansible.builtin.git",
        }
        for task in self.tasks:
            is_brew_install = task["name"] == "Instalar Homebrew"
            if module_of(task) in user_modules or is_brew_install:
                with self.subTest(task=task["name"]):
                    self.assertIs(task.get("become"), False)

    def test_brew_modules_receive_homebrew_environment(self) -> None:
        for task in self.tasks:
            if module_of(task).startswith("community.general.homebrew"):
                with self.subTest(task=task["name"]):
                    self.assertEqual(task["environment"], "{{ homebrew_environment }}")

    def test_homebrew_bootstrap_only_runs_when_missing(self) -> None:
        task = find_task(self.tasks, "Instalar Homebrew")
        self.assertEqual(task["when"], "not homebrew_exists")
        self.assertEqual(task["environment"]["NONINTERACTIVE"], "1")

    def test_homebrew_is_verified_before_use(self) -> None:
        self.assertLess(
            index_of(self.tasks, "Falhar se o Homebrew nao estiver disponivel"),
            index_of(self.tasks, "Atualizar Homebrew"),
        )

    def test_cask_and_formula_lists_have_no_duplicates(self) -> None:
        for name in ["Instalar casks do Homebrew", "Instalar pacotes base no macOS"]:
            packages = list(next(
                value["name"] for key, value in find_task(self.tasks, name).items()
                if key.startswith("community.general.")
            ))
            with self.subTest(task=name):
                self.assertEqual(len(packages), len(set(packages)))

    def test_expected_casks_and_formulae(self) -> None:
        casks = find_task(self.tasks, "Instalar casks do Homebrew")[
            "community.general.homebrew_cask"]["name"]
        formulae = find_task(self.tasks, "Instalar pacotes base no macOS")[
            "community.general.homebrew"]["name"]
        self.assertTrue({"kitty", "flycut", "raycast", "rectangle"} <= set(casks))
        self.assertTrue(
            {"neovim", "git", "stow", "tmux", "fzf", "lazygit", "node", "python"} <= set(formulae)
        )

    def test_stow_packages(self) -> None:
        task = find_task(self.tasks, "Aplicar dotfiles com stow")
        self.assertEqual(task["loop"], ["nvim", "tmux", "zshrc", "kitty"])

    def test_zshrc_is_backed_up_before_stow(self) -> None:
        self.assertLess(
            index_of(self.tasks, "Preservar .zshrc local antes do stow"),
            index_of(self.tasks, "Aplicar dotfiles com stow"),
        )

    def test_dotfiles_are_cloned_before_stow(self) -> None:
        self.assertLess(
            index_of(self.tasks, "Clonar dotfiles"),
            index_of(self.tasks, "Aplicar dotfiles com stow"),
        )

    def test_tmux_plugins_install_after_stow(self) -> None:
        self.assertGreater(
            index_of(self.tasks, "Instalar plugins do tmux"),
            index_of(self.tasks, "Aplicar dotfiles com stow"),
        )

    def test_neovim_assert_regex_accepts_only_0_12_plus(self) -> None:
        task = find_task(self.tasks, "Validar Neovim 0.12+ no macOS")
        expression = task["ansible.builtin.assert"]["that"][0]
        pattern = re.search(r"match\('([^']+)'\)", expression).group(1)
        for banner, ok in [
            ("NVIM v0.12.0", True),
            ("NVIM v0.12.3-dev", True),
            ("NVIM v0.19.1", True),
            ("NVIM v0.20.0", True),
            ("NVIM v0.11.5", False),
            ("NVIM v0.9.0", False),
            ("NVIM v0.120.0", False),
            ("NVIM v1.0.0", False),
            ("", False),
        ]:
            with self.subTest(banner=banner):
                self.assertEqual(bool(re.match(pattern, banner)), ok)

    def test_macos_neovim_check_is_read_only(self) -> None:
        self.assertIs(find_task(self.tasks, "Consultar versao do Neovim no macOS")["changed_when"], False)

    def test_fzf_installer_does_not_touch_stowed_zshrc(self) -> None:
        # `fzf/install --all` edits ~/.zshrc, which is a symlink into the dotfiles repo.
        command = find_task(self.tasks, "Instalar integracoes do fzf")[
            "ansible.builtin.shell"]
        self.assertNotIn("--all", command)

    @unittest.expectedFailure
    def test_ansible_lint_is_installed_like_on_linux(self) -> None:
        self.assertTrue(any("ansible-lint" in str(task) for task in self.tasks))

    def test_user_is_not_taken_only_from_ansible_user(self) -> None:
        # ansible_user is undefined when the inventory line is the commented-out localhost.
        task = find_task(self.tasks, "Definir usuario alvo no macOS")
        fact = task["ansible.builtin.set_fact"]["target_user"]
        self.assertNotEqual(fact.strip(), "{{ ansible_user }}")


@unittest.skipIf(yaml is None, "PyYAML not installed")
class LinuxRoleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tasks = load_tasks("roles/linux/tasks/main.yaml")

    def test_apt_cache_updated_before_packages(self) -> None:
        self.assertLess(
            index_of(self.tasks, "Update apt"), index_of(self.tasks, "Install packages"))

    def test_distro_neovim_removed_before_official_install(self) -> None:
        self.assertLess(
            index_of(self.tasks, "Remover a versão antiga nvim"),
            index_of(self.tasks, "Instalar Neovim oficial"),
        )

    def test_neovim_series_is_defined_once(self) -> None:
        facts = find_task(self.tasks, "Definir serie alvo do Neovim")[
            "ansible.builtin.set_fact"]
        self.assertEqual(facts["neovim_version_series"], "0.12")
        self.assertTrue(facts["neovim_fallback_version"].startswith("v" + facts["neovim_version_series"]))
        literals = [t for t in self.tasks if re.search(r"0\.1[12]", str(t)) and
                    t["name"] != "Definir serie alvo do Neovim"]
        self.assertEqual(literals, [])

    def test_neovim_tag_filter_selects_only_series_releases(self) -> None:
        series = "0.12"
        pattern = "^v" + series + r"\.\d+$"
        for tag, ok in [
            ("v0.12.0", True), ("v0.12.10", True), ("v0.11.5", False),
            ("v0.12.0-rc1", False), ("nightly", False), ("stable", False),
        ]:
            with self.subTest(tag=tag):
                self.assertEqual(bool(re.match(pattern, tag)), ok)

    def test_neovim_download_install_and_cleanup_share_one_condition(self) -> None:
        names = ["Baixar tarball oficial do Neovim", "Remover instalacao anterior do Neovim oficial",
                 "Instalar Neovim oficial", "Remover tarball temporario do Neovim"]
        conditions = {find_task(self.tasks, name)["when"] for name in names}
        self.assertEqual(len(conditions), 1)
        self.assertIn("neovim_official_binary.stat.exists", conditions.pop())

    def test_neovim_api_failure_falls_back_to_pinned_release(self) -> None:
        task = find_task(self.tasks, "Consultar releases do Neovim")
        self.assertIs(task["failed_when"], False)
        fact = find_task(self.tasks, "Definir release alvo do Neovim")[
            "ansible.builtin.set_fact"]["neovim_release_tag"]
        self.assertIn("neovim_fallback_version", fact)

    def test_neovim_final_version_is_validated(self) -> None:
        task = find_task(self.tasks, "Validar versao final do Neovim")
        self.assertIn("neovim_version_series", task["failed_when"])

    def test_nodesource_and_distro_npm_are_not_mixed_unconditionally(self) -> None:
        npm = find_task(self.tasks, "Install npm if running on Ubuntu Desktop")
        self.assertIn("ubuntu_desktop_status", npm["when"])
        packages = find_task(self.tasks, "Install packages")["loop"]
        self.assertIn("nodejs", packages)
        self.assertNotIn("npm", packages)

    def test_user_scoped_tasks_do_not_run_as_root(self) -> None:
        for name in ["Clonar repositório dotfiles", "Download TPM plugin",
                     "Instalar plugins do Tmux", "Instalar o ansible-lint via pipx"]:
            with self.subTest(task=name):
                self.assertIs(find_task(self.tasks, name).get("become"), False)

    def test_dotfiles_cloned_before_stow(self) -> None:
        self.assertLess(
            index_of(self.tasks, "Clonar repositório dotfiles"),
            index_of(self.tasks, "Criar os links simbólicos com o stow para ansible_user e root"),
        )

    def test_zshrc_backup_precedes_stow(self) -> None:
        self.assertLess(
            index_of(self.tasks, "Remover ou renomear .zshrc existente"),
            index_of(self.tasks, "Criar os links simbólicos com o stow para ansible_user e root"),
        )

    def test_stow_covers_user_and_root_for_all_packages(self) -> None:
        loop = find_task(self.tasks, "Criar os links simbólicos com o stow para ansible_user e root")["loop"]
        pairs = {(item["user"], item["config"]) for item in loop}
        expected = {(home, pkg) for home in ("{{ target_home }}", "/root")
                    for pkg in ("tmux", "nvim", "zshrc")}
        self.assertEqual(pairs, expected)

    def test_users_list_has_ansible_user_and_root(self) -> None:
        users = find_task(self.tasks, "Define list of users")["ansible.builtin.set_fact"]["users"]
        self.assertIn("target_user", users)
        self.assertIn("'/root'", users)
        self.assertIn("unique", users)

    def test_target_user_and_home_come_from_facts_not_hardcoded_home(self) -> None:
        self.assertIn("target_home", str(find_task(self.tasks, "Definir home do usuario alvo")))
        self.assertIn("getent", str(find_task(self.tasks, "Consultar home do usuario alvo")))
        for task in self.tasks:
            with self.subTest(task=task["name"]):
                self.assertNotIn("/home/{{ ansible_user }}", str(task))

    def test_font_is_downloaded_before_unzip_and_cache_refresh(self) -> None:
        order = [index_of(self.tasks, n) for n in [
            "Baixar SauceCodePro Nerd Font", "Descompactar o arquivo da fonte",
            "Atualizar cache de fontes", "Remover o arquivo ZIP"]]
        self.assertEqual(order, sorted(order))

    def test_oh_my_zsh_install_is_guarded_by_existing_check(self) -> None:
        task = find_task(self.tasks, "Install Oh My Zsh for users")
        self.assertIn("ohmyzsh_status", task["when"])
        self.assertIn("--unattended", task["ansible.builtin.shell"])

    def test_tmux_plugins_install_after_tmux_conf_is_stowed(self) -> None:
        self.assertGreater(
            index_of(self.tasks, "Instalar plugins do Tmux"),
            index_of(self.tasks, "Criar os links simbólicos com o stow para ansible_user e root"),
        )

    def test_zsh_plugins_are_cloned_as_their_owner(self) -> None:
        for name in ["Clone zsh-autosuggestions plugin", "Clone zsh-completions plugin",
                     "Clone zsh-syntax-highlighting plugin"]:
            with self.subTest(task=name):
                task = find_task(self.tasks, name)
                self.assertEqual(task["become_user"], "{{ item.name }}")

    @unittest.expectedFailure
    def test_chsh_runs_once_and_after_etc_shells_is_updated(self) -> None:
        chsh = [i for i, t in enumerate(self.tasks) if "chsh" in str(t)]
        self.assertEqual(len(chsh), 1)
        self.assertGreater(chsh[0], index_of(self.tasks, "Garantir que o zsh esta no /etc/shells"))

    @unittest.expectedFailure
    def test_shell_check_does_not_use_literal_dollar_shell_with_command_module(self) -> None:
        task = find_task(self.tasks, "Verificar o shell atual")
        self.assertNotEqual(task["ansible.builtin.command"], "echo $SHELL")

    @unittest.expectedFailure
    def test_locale_reload_is_not_a_noop_source(self) -> None:
        names = [t["name"] for t in self.tasks]
        self.assertNotIn("Recarregar locale", names)

    @unittest.expectedFailure
    def test_lazygit_install_is_idempotent(self) -> None:
        task = find_task(self.tasks, "Install lazygit")
        self.assertIn("creates", task.get("args", {}))

    @unittest.expectedFailure
    def test_fd_find_gets_fd_alias_like_bat(self) -> None:
        self.assertTrue(any("fdfind" in str(task) for task in self.tasks))

    @unittest.expectedFailure
    def test_architecture_is_asserted_before_amd64_downloads(self) -> None:
        self.assertTrue(any("ansible_architecture" in str(task) for task in self.tasks))


@unittest.skipIf(yaml is None, "PyYAML not installed")
class RepositoryConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cfg = configparser.ConfigParser()
        self.cfg.read(ROOT / "ansible.cfg")

    def test_requirements_cover_collections_used_by_roles(self) -> None:
        with (ROOT / "collections/requirements.yml").open(encoding="utf-8") as handle:
            declared = {c["name"] for c in yaml.safe_load(handle)["collections"]}
        used = set()
        for path in ["roles/linux/tasks/main.yaml", "roles/macos/tasks/main.yaml"]:
            for task in load_tasks(path):
                parts = module_of(task).split(".")
                if len(parts) == 3 and parts[0] != "ansible":
                    used.add(".".join(parts[:2]))
        self.assertLessEqual(used, declared)

    def test_inventory_file_exists(self) -> None:
        self.assertTrue((ROOT / self.cfg["defaults"]["inventory"]).is_file())

    def test_roles_path_exists(self) -> None:
        self.assertTrue((ROOT / self.cfg["defaults"]["roles_path"]).is_dir())

    def test_inventory_has_at_least_one_active_host_with_user(self) -> None:
        lines = [l for l in (ROOT / "hosts").read_text().splitlines()
                 if l.strip() and not l.lstrip().startswith("#")]
        self.assertTrue(lines)
        for line in lines:
            with self.subTest(line=line):
                self.assertIn("ansible_user=", line)

    def test_requirements_declare_ansible_posix_for_profile_tasks(self) -> None:
        with (ROOT / "collections/requirements.yml").open(encoding="utf-8") as handle:
            declared = {c["name"] for c in yaml.safe_load(handle)["collections"]}
        if "profile_tasks" in self.cfg["defaults"].get("callbacks_enabled", ""):
            self.assertIn("ansible.posix", declared)

    @unittest.expectedFailure
    def test_library_path_exists(self) -> None:
        self.assertTrue(Path(self.cfg["defaults"]["library"]).exists())

    @unittest.expectedFailure
    def test_legacy_macos_yaml_is_not_left_as_dead_code(self) -> None:
        path = ROOT / "macOS.yaml"
        if path.exists():
            self.assertTrue(yaml.safe_load(path.read_text(encoding="utf-8")))

    @unittest.expectedFailure
    def test_gitignore_excludes_python_bytecode(self) -> None:
        content = (ROOT / ".gitignore").read_text()
        self.assertIn("__pycache__", content)


if __name__ == "__main__":
    unittest.main()
