#!/usr/bin/env bash
set -euo pipefail

# 로컬 checkout에서 실행할 때도 원격 설치와 동일한 진입점을 사용한다.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "$ROOT/install.sh" "$@"
