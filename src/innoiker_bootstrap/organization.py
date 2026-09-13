from __future__ import annotations

import subprocess
from pathlib import Path


def _run(command: list[str], cwd: Path | None = None) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def ensure_checkout(path: Path, url: str, ref: str) -> None:
    if (path / ".git").is_dir():
        dirty = subprocess.check_output(["git", "-C", str(path), "status", "--porcelain"], text=True).strip()
        if dirty:
            raise RuntimeError(f"Organization repository에 미커밋 변경이 있습니다: {path}")
        remote = subprocess.check_output(["git", "-C", str(path), "remote", "get-url", "origin"], text=True).strip()
        if remote != url:
            raise RuntimeError(f"Organization remote 불일치: {remote} != {url}")
        _run(["git", "-C", str(path), "fetch", "origin", ref])
        _run(["git", "-C", str(path), "checkout", "--detach", f"origin/{ref}"])
        return
    if path.exists() and any(path.iterdir()):
        raise RuntimeError(f"Organization 경로가 비어 있지 않습니다: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    _run(["git", "clone", "--branch", ref, "--single-branch", url, str(path)])


def ensure_template_checkout(path: Path, url: str, ref: str) -> None:
    if (path / ".git").is_dir():
        dirty = subprocess.check_output(["git", "-C", str(path), "status", "--porcelain"], text=True).strip()
        if dirty:
            raise RuntimeError(f"template repository에 미커밋 변경이 있습니다: {path}")
        remote = subprocess.check_output(["git", "-C", str(path), "remote", "get-url", "origin"], text=True).strip()
        if remote != url:
            raise RuntimeError(f"template remote 불일치: {remote} != {url}")
        _run(["git", "-C", str(path), "fetch", "origin", ref])
        _run(["git", "-C", str(path), "checkout", "--detach", f"origin/{ref}"])
        return
    if path.exists() and any(path.iterdir()):
        raise RuntimeError(f"template 경로가 비어 있지 않습니다: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    _run(["git", "clone", "--branch", ref, "--single-branch", url, str(path)])


def current_revision(path: Path) -> str:
    return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
