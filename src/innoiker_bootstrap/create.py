from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from .config import Config

_SLUG = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def validate_project_name(value: str) -> None:
    if not value.strip():
        raise ValueError("project name은 비어 있을 수 없습니다")
    if Path(value).name != value or value in {".", ".."}:
        raise ValueError("project name은 단일 경로 이름이어야 합니다")


def normalize_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-.").lower()
    if not slug or not _SLUG.fullmatch(slug):
        raise ValueError(f"project slug를 만들 수 없습니다: {value}")
    return slug


def create_project(config: Config, project_name: str, project_dir: Path | None, slug: str | None) -> Path:
    validate_project_name(project_name)
    destination = (project_dir or Path.cwd() / project_name).expanduser().resolve()
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError(f"프로젝트 대상 경로가 비어 있지 않습니다: {destination}")
    if not destination.exists():
        destination.mkdir(parents=True)

    project_slug = slug or normalize_slug(project_name)
    env = os.environ.copy()
    env.update(
        {
            "INNOIKER_ORGANIZATION_REPO": str(config.organization_repo),
            "INNOIKER_AGENT_OS": str(config.agent_os_dir),
            "INNOIKER_AGENT_OS_PROFILE": config.agent_os_profile,
            "PLATFORMS": ",".join(config.platforms),
        }
    )
    command = [
        "asdf",
        "exec",
        "python",
        "-m",
        "copier",
        "copy",
        "--vcs-ref",
        config.template_ref,
        "--trust",
        "--defaults",
        "--data",
        f"project_name={project_name}",
        "--data",
        f"project_slug={project_slug}",
        "--data",
        f"organization_profile={config.organization_profile}",
        "--data",
        f"organization_url={config.organization_url}",
        "--data",
        f"organization_ref={config.organization_ref}",
        "--data",
        f"platforms={','.join(config.platforms)}",
        config.template_url,
        str(destination),
    ]
    try:
        subprocess.run(command, env=env, check=True)
    except Exception:
        if destination.exists() and not any(destination.iterdir()):
            destination.rmdir()
        raise
    return destination
