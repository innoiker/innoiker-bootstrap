from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Toolchain:
    python: str
    nodejs: str
    copier: str
    openspec: str
    agent_os: str
    agent_os_ref: str


_REQUIRED = ("copier", "openspec", "agent_os")


def _run(command: list[str], cwd: Path | None = None) -> str:
    return subprocess.check_output(command, cwd=cwd, text=True, stderr=subprocess.STDOUT).strip()


def read_toolchain_lock(organization_repo: Path) -> Toolchain:
    path = organization_repo / "toolchain.lock"
    if not path.is_file():
        raise FileNotFoundError(f"Organization toolchain.lock 없음: {path}")
    values: dict[str, str] = {}
    pattern = re.compile(r'^([a-z_]+)\s*=\s*"([^"]+)"\s*$')
    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line.strip())
        if match:
            values[match.group(1)] = match.group(2)
    missing = [key for key in _REQUIRED if key not in values]
    if missing:
        raise ValueError(f"toolchain.lock 필수 항목 없음: {', '.join(missing)}")
    agent_os_value = values["agent_os"]
    agent_os = agent_os_value.split("(", 1)[0].strip()
    ref_match = re.search(r"/\s*([0-9a-f]{40})\s*\)", agent_os_value)
    agent_os_ref = ref_match.group(1) if ref_match else agent_os
    return Toolchain(
        python=values.get("python", ""),
        nodejs=values.get("nodejs", ""),
        copier=values["copier"],
        openspec=values["openspec"],
        agent_os=agent_os,
        agent_os_ref=agent_os_ref,
    )


def command_version(command: list[str]) -> str:
    try:
        return _run(command)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return ""


def read_template_tool_versions(template_repo: Path) -> dict[str, str]:
    path = template_repo / "template" / ".tool-versions"
    if not path.is_file():
        raise FileNotFoundError(f"template .tool-versions 없음: {path}")
    text = path.read_text(encoding="utf-8")
    values: dict[str, str] = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 2 and not parts[0].startswith("#"):
            values[parts[0]] = parts[1]
    for required in ("python", "nodejs"):
        if required not in values:
            raise ValueError(f"template .tool-versions에 {required}가 없습니다")
    return values


def installed_versions() -> dict[str, str]:
    return {
        "git": command_version(["git", "--version"]),
        "asdf": command_version(["asdf", "version"]),
        "python": command_version(["python3", "--version"]),
        "nodejs": command_version(["node", "--version"]),
        "copier": command_version(["copier", "--version"]),
        "openspec": command_version(["openspec", "--version"]),
    }
