#!/usr/bin/env bash
# deploy.sh — Claude Kit 배포 스크립트
#
# 사용법:
#   ./deploy.sh <kit-name> add global                     # ~/.claude/ 에 배포
#   ./deploy.sh <kit-name> add project /path/to/project   # <project>/.claude/ 에 배포
#   ./deploy.sh <kit-name> remove global                  # 전역 배포 제거
#   ./deploy.sh <kit-name> remove project /path/to/project
#
# 예시:
#   ./deploy.sh ppt-generator add global
#   ./deploy.sh ppt-generator add project ~/work/my-project
#   ./deploy.sh ppt-generator remove global
#
# 배포 내용:
#   모든 파일을 복사(copy)로 배포한다.
#   __PROJECT_ROOT__ placeholder가 있는 파일은 복사 후 실제 경로로 치환한다.
#     - global 배포: __PROJECT_ROOT__ → $HOME
#     - project 배포: __PROJECT_ROOT__ → /path/to/project
#
# kit명을 prefix로 붙이므로 여러 kit를 같은 대상에 배포해도 충돌하지 않습니다.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# SKILL.md frontmatter에서 deploy-scope 값을 읽는다. 없으면 "both" 반환.
read_deploy_scope() {
  local skill_dir="$1"
  local skill_md="${skill_dir}/SKILL.md"
  if [[ -f "$skill_md" ]]; then
    local scope
    scope=$(grep "^deploy-scope:" "$skill_md" | sed 's/^deploy-scope:[[:space:]]*//')
    echo "${scope:-both}"
  else
    echo "both"
  fi
}

# 배포 모드(global/project)와 선언된 scope가 맞는지 검증한다.
check_scope() {
  local skill_name="$1"
  local scope="$2"
  local mode="$3"

  case "$scope" in
    global)
      if [[ "$mode" == "project" ]]; then
        echo "오류: '${skill_name}' 은 global 전용입니다 (deploy-scope: global)."
        echo "       → ./deploy.sh <kit> global 로 배포하세요."
        exit 1
      fi
      ;;
    project)
      if [[ "$mode" == "global" ]]; then
        echo "오류: '${skill_name}' 은 project 전용입니다 (deploy-scope: project)."
        echo "       → ./deploy.sh <kit> project /path/to/project 로 배포하세요."
        exit 1
      fi
      ;;
    both|"") ;;
    *)
      echo "경고: '${skill_name}' deploy-scope 값 '${scope}' 를 알 수 없습니다. both로 처리합니다."
      ;;
  esac
}

# 파일을 대상 경로에 복사한다. __PROJECT_ROOT__ 가 있으면 치환한다.
deploy_file() {
  local src="$1"           # 원본 파일
  local dest="$2"          # 배포 대상 경로
  local project_root="$3"  # 치환할 경로 (global=$HOME, project=실제경로)
  local label="$4"         # 출력용 레이블

  rm -f "$dest"
  if grep -q "__PROJECT_ROOT__" "$src" 2>/dev/null; then
    sed "s|__PROJECT_ROOT__|${project_root}|g" "$src" > "$dest"
    echo "  ✓ $label (PROJECT_ROOT=${project_root})"
  else
    cp "$src" "$dest"
    echo "  ✓ $label"
  fi
}

usage() {
  echo "사용법:"
  echo "  $0 <kit-name> add global"
  echo "  $0 <kit-name> add project /path/to/project"
  echo "  $0 <kit-name> remove global"
  echo "  $0 <kit-name> remove project /path/to/project"
  echo ""
  echo "사용 가능한 kit:"
  for d in "$REPO_ROOT"/*/; do
    name="$(basename "$d")"
    [[ "$name" == .* ]] && continue
    [[ -d "$d/skills" || -d "$d/agents" || -d "$d/rules" ]] && echo "  $name"
  done
  exit 1
}

resolve_target() {
  local mode="$1"
  local project_path="${2:-}"
  if [[ "$mode" == "global" ]]; then
    echo "$HOME/.claude"
  elif [[ "$mode" == "project" ]]; then
    [[ -z "$project_path" ]] && usage
    echo "$project_path/.claude"
  else
    usage
  fi
}

deploy() {
  local kit_name="$1"
  local target="$2"
  local project_root="${3:-}"
  local kit_dir="$REPO_ROOT/$kit_name"
  [[ -d "$kit_dir" ]] || { echo "오류: kit '$kit_name' 을 찾을 수 없습니다."; usage; }

  # skills/ — SKILL.md 등 개별 파일은 deploy_file로, 나머지 디렉토리는 심링크
  if [[ -d "$kit_dir/skills" ]]; then
    mkdir -p "$target/skills"
    for skill_dir in "$kit_dir/skills"/*/; do
      [[ -d "$skill_dir" ]] || continue
      skill_name="$(basename "$skill_dir")"
      dest_dir="$target/skills/${kit_name}-${skill_name}"

      scope="$(read_deploy_scope "$skill_dir")"
      check_scope "${kit_name}-${skill_name}" "$scope" "$MODE"

      # 디렉토리를 항상 복사 후 __PROJECT_ROOT__ 치환
      rm -rf "$dest_dir"
      cp -r "$skill_dir" "$dest_dir"
      while IFS= read -r -d '' f; do
        if grep -q "__PROJECT_ROOT__" "$f" 2>/dev/null; then
          sed -i "" "s|__PROJECT_ROOT__|${project_root}|g" "$f"
        fi
      done < <(find "$dest_dir" -type f -print0)
      echo "  ✓ skills/${kit_name}-${skill_name}${project_root:+ (PROJECT_ROOT=${project_root})}"
    done
  fi

  # agents/ — deploy_file로 개별 처리
  if [[ -d "$kit_dir/agents" ]]; then
    mkdir -p "$target/agents"
    for agent_file in "$kit_dir/agents"/*.md; do
      [[ -f "$agent_file" ]] || continue
      agent_name="$(basename "$agent_file" .md)"
      dest="$target/agents/${kit_name}-${agent_name}.md"
      deploy_file "$agent_file" "$dest" "$project_root" "agents/${kit_name}-${agent_name}.md"
    done
  fi

  # rules/ — deploy_file로 개별 처리
  if [[ -d "$kit_dir/rules" ]]; then
    mkdir -p "$target/rules"
    for rule_file in "$kit_dir/rules"/*.md; do
      [[ -f "$rule_file" ]] || continue
      rule_name="$(basename "$rule_file" .md)"
      dest="$target/rules/${kit_name}-${rule_name}.md"
      deploy_file "$rule_file" "$dest" "$project_root" "rules/${kit_name}-${rule_name}.md"
    done
  fi

  echo ""
  echo "배포 완료 [$kit_name]: $target"
  echo "Claude Code를 재시작하면 활성화됩니다."
}

remove_deploy() {
  local kit_name="$1"
  local target="$2"
  local kit_dir="$REPO_ROOT/$kit_name"

  [[ -d "$kit_dir" ]] || { echo "오류: kit '$kit_name' 을 찾을 수 없습니다."; usage; }

  # skills — 심링크 또는 복사본(디렉토리) 모두 제거
  if [[ -d "$kit_dir/skills" ]]; then
    for skill_dir in "$kit_dir/skills"/*/; do
      [[ -d "$skill_dir" ]] || continue
      skill_name="$(basename "$skill_dir")"
      dest="$target/skills/${kit_name}-${skill_name}"
      if [[ -L "$dest" ]]; then
        rm "$dest" && echo "  ✓ 제거: skills/${kit_name}-${skill_name}"
      elif [[ -d "$dest" ]]; then
        rm -rf "$dest" && echo "  ✓ 제거: skills/${kit_name}-${skill_name}"
      fi
    done
  fi

  # agents — 심링크 또는 복사본(파일) 모두 제거
  if [[ -d "$kit_dir/agents" ]]; then
    for agent_file in "$kit_dir/agents"/*.md; do
      [[ -f "$agent_file" ]] || continue
      agent_name="$(basename "$agent_file" .md)"
      dest="$target/agents/${kit_name}-${agent_name}.md"
      if [[ -L "$dest" || -f "$dest" ]]; then
        rm "$dest" && echo "  ✓ 제거: agents/${kit_name}-${agent_name}.md"
      fi
    done
  fi

  # rules — 심링크 또는 복사본(파일) 모두 제거
  if [[ -d "$kit_dir/rules" ]]; then
    for rule_file in "$kit_dir/rules"/*.md; do
      [[ -f "$rule_file" ]] || continue
      rule_name="$(basename "$rule_file" .md)"
      dest="$target/rules/${kit_name}-${rule_name}.md"
      if [[ -L "$dest" || -f "$dest" ]]; then
        rm "$dest" && echo "  ✓ 제거: rules/${kit_name}-${rule_name}.md"
      fi
    done
  fi

  echo "제거 완료 [$kit_name]: $target"
}

# ── 진입점 ──────────────────────────────────────────────────────────────

[[ $# -lt 2 ]] && usage

KIT_NAME="$1"
ACTION="$2"
shift 2

if [[ "$ACTION" == "remove" ]]; then
  MODE="${1:-}"
  PROJECT_PATH="${2:-}"
  TARGET="$(resolve_target "$MODE" "$PROJECT_PATH")"
  remove_deploy "$KIT_NAME" "$TARGET"
elif [[ "$ACTION" == "add" ]]; then
  MODE="${1:-}"
  PROJECT_PATH="${2:-}"
  TARGET="$(resolve_target "$MODE" "$PROJECT_PATH")"
  # __PROJECT_ROOT__ 치환값 결정: project → 해당 경로, global → $HOME
  if [[ "$MODE" == "project" && -n "$PROJECT_PATH" ]]; then
    PROJECT_ROOT="$(cd "$PROJECT_PATH" && pwd)"
  elif [[ "$MODE" == "global" ]]; then
    PROJECT_ROOT="$HOME"
  else
    PROJECT_ROOT=""
  fi
  deploy "$KIT_NAME" "$TARGET" "$PROJECT_ROOT"
else
  echo "오류: 알 수 없는 액션 '$ACTION'. 'add' 또는 'remove' 를 사용하세요."
  usage
fi
