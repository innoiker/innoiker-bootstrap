from __future__ import annotations

from .config import Config
from .environment import command_output, _command
from .organization import current_revision
from .toolchain import Toolchain


def check(config: Config, toolchain: Toolchain, template_tools: dict[str, str] | None = None) -> dict[str, object]:
    checks: dict[str, object] = {}
    commands = {
        "git": ["git", "--version"],
        "asdf": ["asdf", "version"],
        "python": ["asdf", "exec", "python", "--version"],
        "nodejs": ["asdf", "exec", "node", "--version"],
        "copier": ["asdf", "exec", "python", "-m", "copier", "--version"],
        "openspec": ["asdf", "exec", "openspec", "--version"],
    }
    for name, command in commands.items():
        try:
            checks[name] = {"ok": True, "version": command_output(_command(command[0], *command[1:]))}
        except Exception as exc:
            checks[name] = {"ok": False, "error": str(exc)}

    profile = config.agent_os_dir / "profiles" / config.agent_os_profile
    checks["agent_os"] = {
        "ok": (config.agent_os_dir / "scripts" / "project-install.sh").is_file(),
        "path": str(config.agent_os_dir),
        "profile": config.agent_os_profile,
        "profile_exists": profile.is_dir(),
    }
    checks["organization"] = {
        "ok": (config.organization_repo / ".git").is_dir(),
        "path": str(config.organization_repo),
    }
    if (config.organization_repo / ".git").is_dir():
        checks["organization"]["revision"] = current_revision(config.organization_repo)
    if template_tools:
        expected = {
            "python": template_tools["python"],
            "nodejs": template_tools["nodejs"],
            "copier": toolchain.copier,
            "openspec": toolchain.openspec,
        }
        for name, version in expected.items():
            actual = checks[name].get("version", "") if isinstance(checks.get(name), dict) else ""
            normalized = actual.removeprefix("v")
            checks[name]["expected"] = version
            checks[name]["ok"] = checks[name].get("ok", False) and version in normalized
        if (config.agent_os_dir / ".git").is_dir():
            checks["agent_os"]["revision"] = current_revision(config.agent_os_dir)
            checks["agent_os"]["expected_revision"] = toolchain.agent_os_ref
            checks["agent_os"]["ok"] = checks["agent_os"].get("ok", False) and checks["agent_os"]["revision"] == toolchain.agent_os_ref
    checks["platforms"] = list(config.platforms)
    checks["organization_profile"] = config.organization_profile
    return checks


def healthy(report: dict[str, object]) -> bool:
    return all(value.get("ok", False) for value in report.values() if isinstance(value, dict) and "ok" in value)
