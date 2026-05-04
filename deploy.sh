#!/usr/bin/env bash
# deploy.sh — Claude Kit 배포 스크립트
#
# 사용법:
#   ./deploy.sh <kit-name> global                     # ~/.claude/ 에 배포
#   ./deploy.sh <kit-name> project /path/to/project   # <project>/.claude/ 에 배포
#   ./deploy.sh <kit-name> remove global              # 전역 배포 제거
#   ./deploy.sh <kit-name> remove project /path/to/project
#
# 예시:
#   ./deploy.sh ppt-generator global
#   ./deploy.sh ppt-generator project ~/work/my-project
#
# 배포 내용 (모두 심링크):
#   skills/<name>/   → <target>/skills/<kit-name>-<name>/
#   agents/<name>.md → <target>/agents/<kit-name>-<name>.md
#   rules/<name>.md  → <target>/rules/<kit-name>-<name>.md
#
# kit명을 prefix로 붙이므로 여러 kit를 같은 대상에 배포해도 충돌하지 않습니다.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  echo "사용법:"
  echo "  $0 <kit-name> global"
  echo "  $0 <kit-name> project /path/to/project"
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
  local kit_dir="$REPO_ROOT/$kit_name"

  [[ -d "$kit_dir" ]] || { echo "오류: kit '$kit_name' 을 찾을 수 없습니다."; usage; }

  # skills/ — 심링크
  if [[ -d "$kit_dir/skills" ]]; then
    mkdir -p "$target/skills"
    for skill_dir in "$kit_dir/skills"/*/; do
      [[ -d "$skill_dir" ]] || continue
      skill_name="$(basename "$skill_dir")"
      dest="$target/skills/${kit_name}-${skill_name}"
      ln -sfn "$skill_dir" "$dest"
      echo "  ✓ skills/${kit_name}-${skill_name}"
    done
  fi

  # agents/ — 심링크
  if [[ -d "$kit_dir/agents" ]]; then
    mkdir -p "$target/agents"
    for agent_file in "$kit_dir/agents"/*.md; do
      [[ -f "$agent_file" ]] || continue
      agent_name="$(basename "$agent_file" .md)"
      dest="$target/agents/${kit_name}-${agent_name}.md"
      ln -sf "$agent_file" "$dest"
      echo "  ✓ agents/${kit_name}-${agent_name}.md"
    done
  fi

  # rules/ — 심링크
  if [[ -d "$kit_dir/rules" ]]; then
    mkdir -p "$target/rules"
    for rule_file in "$kit_dir/rules"/*.md; do
      [[ -f "$rule_file" ]] || continue
      rule_name="$(basename "$rule_file" .md)"
      dest="$target/rules/${kit_name}-${rule_name}.md"
      ln -sf "$rule_file" "$dest"
      echo "  ✓ rules/${kit_name}-${rule_name}.md"
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

  # skills
  if [[ -d "$kit_dir/skills" ]]; then
    for skill_dir in "$kit_dir/skills"/*/; do
      [[ -d "$skill_dir" ]] || continue
      skill_name="$(basename "$skill_dir")"
      dest="$target/skills/${kit_name}-${skill_name}"
      [[ -L "$dest" ]] && rm "$dest" && echo "  ✓ 제거: skills/${kit_name}-${skill_name}"
    done
  fi

  # agents
  if [[ -d "$kit_dir/agents" ]]; then
    for agent_file in "$kit_dir/agents"/*.md; do
      [[ -f "$agent_file" ]] || continue
      agent_name="$(basename "$agent_file" .md)"
      dest="$target/agents/${kit_name}-${agent_name}.md"
      [[ -L "$dest" ]] && rm "$dest" && echo "  ✓ 제거: agents/${kit_name}-${agent_name}.md"
    done
  fi

  # rules
  if [[ -d "$kit_dir/rules" ]]; then
    for rule_file in "$kit_dir/rules"/*.md; do
      [[ -f "$rule_file" ]] || continue
      rule_name="$(basename "$rule_file" .md)"
      dest="$target/rules/${kit_name}-${rule_name}.md"
      [[ -L "$dest" ]] && rm "$dest" && echo "  ✓ 제거: rules/${kit_name}-${rule_name}.md"
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
else
  MODE="$ACTION"
  PROJECT_PATH="${1:-}"
  TARGET="$(resolve_target "$MODE" "$PROJECT_PATH")"
  deploy "$KIT_NAME" "$TARGET"
fi
