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
