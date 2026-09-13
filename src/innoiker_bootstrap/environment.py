from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from .config import Config
from .toolchain import Toolchain


ASDF_BINARY_CANDIDATES = (
    Path.home() / ".local" / "bin" / "asdf",
    Path.home() / ".asdf" / "bin" / "asdf",
)


def _command(name: str, *extra: str) -> list[str]:
    path = shutil.which(name)
    if path:
        return [path, *extra]
    for candidate in ASDF_BINARY_CANDIDATES:
        if candidate.is_file() and candidate.stat().st_mode & 0o111:
            return [str(candidate), *extra]
    raise FileNotFoundError(f"명령 없음: {name}")


def run(command: list[str], *, cwd: Path | None = None) -> None:
    env = os.environ.copy()
    env.setdefault("PIP_DISABLE_PIP_VERSION_CHECK", "1")
    subprocess.run(command, cwd=cwd, check=True, env=env)


def command_output(command: list[str]) -> str:
    env = os.environ.copy()
    env.setdefault("PIP_DISABLE_PIP_VERSION_CHECK", "1")
    return subprocess.check_output(command, text=True, stderr=subprocess.STDOUT, env=env).strip()


def ensure_asdf() -> None:
    _command("asdf")


def ensure_asdf_plugin(name: str, repository: str) -> None:
    plugins = command_output(_command("asdf", "plugin", "list")).splitlines()
    if name not in plugins:
        run(_command("asdf", "plugin", "add", name, repository))


def ensure_runtime(tool: str, version: str) -> None:
    installed = command_output(_command("asdf", "list", tool)).splitlines()
    normalized = version.strip()
    if not any(line.strip() == normalized for line in installed):
        run(_command("asdf", "install", tool, normalized))


def ensure_runtimes(toolchain: dict[str, str]) -> None:
    ensure_asdf()
    ensure_asdf_plugin("python", "https://github.com/asdf-community/asdf-python.git")
    ensure_asdf_plugin("nodejs", "https://github.com/asdf-vm/asdf-nodejs.git")
    ensure_runtime("python", toolchain["python"])
    ensure_runtime("nodejs", toolchain["nodejs"])


def asdf_exec(tool: str, version: str, command: list[str]) -> list[str]:
    return _command("asdf", "exec", *command)


def ensure_python_tools(toolchain: Toolchain) -> None:
    python = _command("asdf", "exec", "python", "--version")
    run([*python[:3], "-m", "pip", "install", "--upgrade", f"pip<26"])
    run([*python[:3], "-m", "pip", "install", f"copier=={toolchain.copier}"])
    run(_command("asdf", "reshim", "python"))


def ensure_openspec(toolchain: Toolchain) -> None:
    npm = _command("asdf", "exec", "npm")
    env = os.environ.copy()
    env["npm_config_fund"] = "false"
    subprocess.run(
        [*npm, "install", "--global", f"@fission-ai/openspec@{toolchain.openspec}"],
        check=True,
        env=env,
    )
    run(_command("asdf", "reshim", "nodejs"))


def seed_agent_os_profile(config: Config) -> None:
    profile = config.agent_os_dir / "profiles" / config.agent_os_profile
    if profile.is_dir():
        return
    default = config.agent_os_dir / "profiles" / "default"
    if not default.is_dir():
        raise FileNotFoundError(f"Agent OS default profile 없음: {default}")
    profile.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(default, profile)


def ensure_agent_os(config: Config, expected_ref: str) -> None:
    root = config.agent_os_dir
    if not (root / ".git").is_dir():
        if root.exists() and any(root.iterdir()):
            raise RuntimeError(
                f"Agent OS 경로가 Git 저장소가 아니며 비어 있지 않습니다: {root}"
            )
        root.parent.mkdir(parents=True, exist_ok=True)
        run(["git", "clone", "https://github.com/buildermethods/agent-os.git", str(root)])
    run(["git", "-C", str(root), "fetch", "origin", expected_ref])
    run(["git", "-C", str(root), "checkout", "--detach", expected_ref])
    if not (root / "scripts" / "project-install.sh").is_file():
        raise RuntimeError("지원하는 Agent OS project-install.sh가 없습니다")
    seed_agent_os_profile(config)


def verify_host(config: Config, toolchain: Toolchain) -> dict[str, str]:
    checks = {
        "git": command_output(["git", "--version"]),
        "asdf": command_output(_command("asdf", "version")),
        "python": command_output(_command("asdf", "exec", "python", "--version")),
        "nodejs": command_output(_command("asdf", "exec", "node", "--version")),
        "copier": command_output(_command("asdf", "exec", "copier", "--version")),
        "openspec": command_output(_command("asdf", "exec", "openspec", "--version")),
        "agent_os_profile": config.agent_os_profile,
    }
    return checks
