from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_ORGANIZATION_URL = "https://github.com/innoiker/innoiker-organization.git"
DEFAULT_TEMPLATE_URL = "https://github.com/innoiker/innoiker-copier-template.git"
DEFAULT_ORGANIZATION_REF = "main"
DEFAULT_TEMPLATE_REF = "main"
DEFAULT_ORGANIZATION_PROFILE = "innoiker"
DEFAULT_PLATFORMS = "android"
SUPPORTED_PLATFORMS = ("android", "web", "server")


@dataclass(frozen=True)
class Config:
    organization_repo: Path
    organization_url: str
    organization_ref: str
    organization_profile: str
    template_url: str
    template_ref: str
    template_cache: Path
    platforms: tuple[str, ...]


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def parse_platforms(raw: str) -> tuple[str, ...]:
    values = [item.strip() for item in raw.split(",") if item.strip()]
    if not values:
        raise ValueError("platform을 하나 이상 선택해야 합니다")
    duplicates = sorted({item for item in values if values.count(item) > 1})
    if duplicates:
        raise ValueError(f"중복된 플랫폼: {', '.join(duplicates)}")
    invalid = [item for item in values if item not in SUPPORTED_PLATFORMS]
    if invalid:
        raise ValueError(f"지원하지 않는 플랫폼: {', '.join(invalid)}")
    return tuple(platform for platform in SUPPORTED_PLATFORMS if platform in values)


def build_config(
    *,
    organization_repo: str | None = None,
    organization_url: str | None = None,
    organization_ref: str | None = None,
    organization_profile: str | None = None,
    template_url: str | None = None,
    template_ref: str | None = None,
    platforms: str | None = None,
) -> Config:
    org_profile = organization_profile or _env("INNOIKER_ORGANIZATION_PROFILE", DEFAULT_ORGANIZATION_PROFILE)
    return Config(
        organization_repo=Path(organization_repo or _env("INNOIKER_ORGANIZATION_REPO", str(Path.home() / "work/innoiker-organization"))).expanduser(),
        organization_url=organization_url or _env("INNOIKER_ORGANIZATION_URL", DEFAULT_ORGANIZATION_URL),
        organization_ref=organization_ref or _env("INNOIKER_ORGANIZATION_REF", DEFAULT_ORGANIZATION_REF),
        organization_profile=org_profile,
        template_url=template_url or _env("INNOIKER_TEMPLATE_URL", DEFAULT_TEMPLATE_URL),
        template_ref=template_ref or _env("INNOIKER_TEMPLATE_REF", DEFAULT_TEMPLATE_REF),
        template_cache=Path(_env("INNOIKER_TEMPLATE_CACHE", str(Path.home() / ".innoiker" / "template"))).expanduser(),
        platforms=parse_platforms(platforms or _env("INNOIKER_PLATFORMS", DEFAULT_PLATFORMS)),
    )
