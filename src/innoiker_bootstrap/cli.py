from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .config import Config, build_config
from .create import create_project
from .doctor import check, healthy
from .environment import ensure_agent_os, ensure_openspec, ensure_python_tools, ensure_runtimes, verify_host
from .organization import ensure_checkout, ensure_template_checkout
from .toolchain import read_template_tool_versions, read_toolchain_lock


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--organization-repo")
    parser.add_argument("--organization-url")
    parser.add_argument("--organization-ref")
    parser.add_argument("--organization-profile")
    parser.add_argument("--agent-os-dir")
    parser.add_argument("--agent-os-profile")
    parser.add_argument("--template-url")
    parser.add_argument("--template-ref")
    parser.add_argument("--platforms")


def _config(args: argparse.Namespace) -> Config:
    return build_config(
        organization_repo=args.organization_repo,
        organization_url=args.organization_url,
        organization_ref=args.organization_ref,
        organization_profile=args.organization_profile,
        agent_os_dir=args.agent_os_dir,
        agent_os_profile=args.agent_os_profile,
        template_url=args.template_url,
        template_ref=args.template_ref,
        platforms=args.platforms,
    )


def command_bootstrap(config: Config) -> int:
    ensure_checkout(config.organization_repo, config.organization_url, config.organization_ref)
    ensure_template_checkout(config.template_cache, config.template_url, config.template_ref)
    toolchain = read_toolchain_lock(config.organization_repo)
    template_tools = read_template_tool_versions(config.template_cache)
    ensure_runtimes({"python": template_tools["python"], "nodejs": template_tools["nodejs"]})
    ensure_python_tools(toolchain)
    ensure_openspec(toolchain)
    ensure_agent_os(config, toolchain.agent_os_ref)
    report = check(config, toolchain, template_tools)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if healthy(report) else 1


def ensure_bootstrapped(config: Config) -> int:
    try:
        toolchain = read_toolchain_lock(config.organization_repo)
        template_tools = read_template_tool_versions(config.template_cache)
        if healthy(check(config, toolchain, template_tools)):
            return 0
    except Exception:
        pass
    return command_bootstrap(config)


def command_doctor(config: Config, as_json: bool) -> int:
    try:
        toolchain = read_toolchain_lock(config.organization_repo)
    except Exception as exc:
        report = {"toolchain": {"ok": False, "error": str(exc)}}
        if as_json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(f"FAIL toolchain: {exc}")
        return 1
    try:
        template_tools = read_template_tool_versions(config.template_cache)
    except Exception as exc:
        report = {"template_tool_versions": {"ok": False, "error": str(exc)}}
        if as_json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(f"FAIL template_tool_versions: {exc}")
        return 1
    report = check(config, toolchain, template_tools)
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for name, value in report.items():
            if isinstance(value, dict) and "ok" in value:
                status = "OK" if value["ok"] else "FAIL"
                detail = value.get("version") or value.get("error") or ""
                print(f"{status:4} {name}: {detail}")
            else:
                print(f"INFO {name}: {value}")
    return 0 if healthy(report) else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="innoiker", description="Innoiker host bootstrapper")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    bootstrap = sub.add_parser("bootstrap", help="host 환경을 설치하고 검증합니다")
    _add_common(bootstrap)

    doctor = sub.add_parser("doctor", help="host 환경을 읽기 전용으로 검사합니다")
    doctor.add_argument("--json", action="store_true")
    _add_common(doctor)

    create = sub.add_parser("create", help="새 Innoiker 프로젝트를 생성합니다")
    create.add_argument("project_name")
    create.add_argument("--project-dir", type=Path)
    create.add_argument("--slug")
    _add_common(create)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        config = _config(args)
        if args.command == "bootstrap":
            return command_bootstrap(config)
        if args.command == "doctor":
            return command_doctor(config, args.json)
        if args.command == "create":
            if ensure_bootstrapped(config) != 0:
                return 1
            destination = create_project(config, args.project_name, args.project_dir, args.slug)
            print(destination)
            return 0
        parser.error(f"지원하지 않는 command: {args.command}")
    except KeyboardInterrupt:
        print("중단되었습니다.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
