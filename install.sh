#!/usr/bin/env bash
set -euo pipefail

ASDF_VERSION="0.20.0"
BOOTSTRAP_URL="https://github.com/innoiker/innoiker-bootstrap.git"
INSTALL_ROOT="${INNOIKER_BOOTSTRAP_HOME:-$HOME/.innoiker/bootstrap}"
BIN_DIR="${INNOIKER_BIN_DIR:-$HOME/.local/bin}"
ASDF_BIN="$BIN_DIR/asdf"

say() { printf '[innoiker] %s\n' "$*"; }
fail() { printf '[innoiker] ERROR: %s\n' "$*" >&2; exit 1; }

install_os_dependencies() {
  if command -v git >/dev/null 2>&1 && command -v curl >/dev/null 2>&1; then
    return
  fi
  case "$(uname -s)" in
    Darwin)
      command -v brew >/dev/null 2>&1 || fail 'macOS에서는 Homebrew가 필요합니다.'
      brew install git curl
      ;;
    Linux)
      if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update
        sudo apt-get install -y git curl ca-certificates build-essential
      elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y git curl ca-certificates gcc make
      elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -Sy --needed --noconfirm git curl ca-certificates base-devel
      else
        fail '지원하는 Linux 패키지 관리자를 찾을 수 없습니다.'
      fi
      ;;
    *) fail "지원하지 않는 운영체제: $(uname -s)" ;;
  esac
}

install_asdf() {
  mkdir -p "$BIN_DIR"
  if command -v asdf >/dev/null 2>&1 || [ -x "$ASDF_BIN" ]; then
    return
  fi
  local os arch asset url tmp
  case "$(uname -s)" in
    Darwin) os="darwin" ;;
    Linux) os="linux" ;;
    *) fail "지원하지 않는 운영체제: $(uname -s)" ;;
  esac
  case "$(uname -m)" in
    x86_64|amd64) arch="amd64" ;;
    arm64|aarch64) arch="arm64" ;;
    *) fail "지원하지 않는 CPU 아키텍처: $(uname -m)" ;;
  esac
  asset="asdf-${ASDF_VERSION}-${os}-${arch}.tar.gz"
  url="https://github.com/asdf-vm/asdf/releases/download/v${ASDF_VERSION}/${asset}"
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN
  curl -fsSL "$url" -o "$tmp/$asset"
  tar -xzf "$tmp/$asset" -C "$tmp"
  install -m 0755 "$tmp/asdf" "$ASDF_BIN"
  trap - RETURN
}

prepare_path() {
  export PATH="$BIN_DIR:$HOME/.asdf/shims:$PATH"
}

clone_bootstrap() {
  if [ -d "$INSTALL_ROOT/.git" ]; then
    git -C "$INSTALL_ROOT" fetch origin main
    git -C "$INSTALL_ROOT" checkout --detach origin/main
  else
    mkdir -p "$(dirname "$INSTALL_ROOT")"
    git clone --branch main --single-branch "$BOOTSTRAP_URL" "$INSTALL_ROOT"
  fi
}

install_bootstrap_cli() {
  asdf plugin list | grep -qx python || asdf plugin add python https://github.com/asdf-community/asdf-python.git
  asdf plugin list | grep -qx nodejs || asdf plugin add nodejs https://github.com/asdf-vm/asdf-nodejs.git
  asdf install python 3.14.7
  asdf install nodejs 24.20.0
  asdf set -u python 3.14.7
  asdf set -u nodejs 24.20.0
  asdf exec python -m pip install --upgrade 'pip<26'
  asdf exec python -m pip install --force-reinstall "$INSTALL_ROOT"

  # asdf의 실행 파일 탐색에 의존하지 않고 설치된 Python 환경에서
  # 실제 console script를 사용자 PATH에 materialize한다.
  local python_bin console_script
  python_bin="$(asdf which python)"
  console_script="$(dirname "$python_bin")/innoiker"
  if [ ! -x "$console_script" ]; then
    fail "innoiker CLI가 Python 환경에 설치되지 않았습니다: $console_script"
  fi
  mkdir -p "$BIN_DIR"
  ln -sfn "$console_script" "$BIN_DIR/innoiker"
  chmod +x "$console_script"
}

verify_installation() {
  local cli="$BIN_DIR/innoiker"
  [ -x "$cli" ] || fail "설치 후 innoiker 실행 파일을 찾을 수 없습니다: $cli"
  "$cli" --version >/dev/null || fail 'innoiker CLI 실행 검증에 실패했습니다.'
}

main() {
  install_os_dependencies
  install_asdf
  prepare_path
  clone_bootstrap
  install_bootstrap_cli
  verify_installation
  say '설치 완료.'
  say "export PATH=\"$BIN_DIR:\$PATH\""
  say 'innoiker doctor'
  say 'innoiker create my-project'
}

main "$@"
