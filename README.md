# innoiker-bootstrap

빈 개발 환경에서 Innoiker 프로젝트를 생성하기 위한 bootstrapper이다.

`innoiker-copier-template`은 생성된 프로젝트의 lifecycle을 책임지고, 이 저장소는 그 이전의 **host environment lifecycle**을 책임진다.

## 목표 UX

```text
빈 머신
  ↓
innoiker-bootstrap installer
  ↓
Git + asdf + Python + Node
  ↓
Copier + OpenSpec + Agent-independent project
  ↓
Organization Knowledge SoT
  ↓
innoiker create
  ↓
검증된 Innoiker 프로젝트
```

설치 후 사용자는 다음만 기억하면 된다. `create`는 필요한 bootstrap을 자동으로 수행한다.

```bash
innoiker doctor
innoiker create my-project --platforms android,web
```

## CLI 계약

### `innoiker doctor`

호스트 환경과 Innoiker toolchain을 읽기 전용으로 검사한다.

- Git
- asdf
- Python
- Node.js
- Copier
- OpenSpec
- Organization repository
- Organization toolchain/template contract

실패 시 non-zero를 반환하며 자동 변경은 하지 않는다.

### `innoiker bootstrap`

현재 머신에 필요한 환경을 설치/준비한다. 이미 준비된 구성요소는 재사용한다.

```bash
innoiker bootstrap
```

기본값은 Organization `main`, template `main`, Organization profile `innoiker`이다. 다른 환경을 사용해야 하면 옵션 또는 환경변수로 명시한다.

### `innoiker create <project-name>`

환경이 준비되지 않았으면 필요한 bootstrap을 먼저 수행한 뒤 Copier로 새 프로젝트를 생성하고, 현재 `innoiker-copier-template`의 post-generation lifecycle을 그대로 실행한다.

```bash
innoiker create my-project
innoiker create my-project --platforms android,web,server
```

`platforms`는 현재 template과 동일하게 `android,web,server`만 허용하며 공백은 허용하고 중복/빈 값은 거부한다. 저장 순서는 canonical order를 따른다.

### `innoiker doctor --json`

자동화 환경을 위한 machine-readable 상태를 출력한다. stdout은 JSON만 사용한다.

### 공통 옵션

- `--organization-repo PATH`
- `--organization-url URL`
- `--organization-ref REF`
- `--organization-profile NAME`
- `--agent-os-dir PATH`
- `--agent-os-profile NAME`
- `--template-url URL`
- `--template-ref REF`
- `--platforms LIST`
- `--json` (`doctor` 전용)

환경변수는 `INNOIKER_*` 이름을 사용하며 CLI 옵션이 우선한다.

## 책임 경계

| 영역 | 책임 |
|---|---|
| bootstrapper | host toolchain 설치, Organization checkout, Agent-independent 프로젝트 생성 준비, Copier 실행 |
| copier-template | 프로젝트 구조, Organization materialization, verify, org-update, project Git lifecycle |
| organization | Context / Standards / Agent Skills의 Source of Truth |

`./innoiker`는 host bootstrapper를 대체하지 않는다. 반대로 bootstrapper는 생성 프로젝트의 Organization lifecycle을 재구현하지 않는다.

## 결정 사항

1. Bootstrapper는 project repo 안에 설치되지 않는다.
2. Bootstrapper는 프로젝트를 자동으로 GitHub에 생성하지 않는다. 로컬 프로젝트 생성까지만 수행한다.
3. Git 인증/SSH credential은 자동 생성하거나 저장하지 않는다. private Organization 접근이 필요한 경우 기존 Git credential을 사용한다.
4. shell startup 파일을 자동 수정하지 않는다. 설치 스크립트는 실행 중 필요한 PATH를 자체 구성하고, 사용자가 새 셸에서 `innoiker`를 사용하도록 안내한다.
5. Tool version은 Organization `toolchain.lock`을 SoT로 사용한다. `python`과 `nodejs`는 template의 `.tool-versions`와 정확히 일치해야 하며, 충돌하는 경우 bootstrap을 실패시킨다.
6. Agent runtime은 bootstrap이 선택하거나 고정하지 않는다. 생성 프로젝트의 Agent Skills는 Agent Skills 형식으로 materialize되며, 작업마다 호환되는 Agent를 독립적으로 선택할 수 있다. 기존 `INNOIKER_AGENT_OS` 및 `INNOIKER_AGENT_OS_PROFILE` 설정은 호환성을 위해 유지하지만 bootstrap의 필수 조건이 아니다.

## 공식 설치

macOS / Linux:

```bash
curl -fsSL https://raw.githubusercontent.com/innoiker/innoiker-bootstrap/main/install.sh | bash
```

Windows PowerShell:

```powershell
irm https://raw.githubusercontent.com/innoiker/innoiker-bootstrap/main/installer/install.ps1 | iex
```

설치 후 새 셸에서:

```bash
innoiker doctor
innoiker create my-project
```
