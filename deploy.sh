#!/usr/bin/env bash
# deploy.sh — Claude config 배포 스크립트
#
# 사용법:
#   ./deploy.sh global                     # ~/.claude/ 에 배포 (전역)
#   ./deploy.sh project /path/to/project   # <project>/.claude/ 에 배포
#   ./deploy.sh remove global              # 전역 배포 제거
#   ./deploy.sh remove project /path/to/project
#
# 동작 방식:
#   1. commands/*.md.template → <target>/commands/*.md (경로 치환 후 심링크 or 복사)
#   2. settings.json → <target>/settings.json 심링크
#   3. agents/ → <target>/agents/ 심링크
#
# 심링크를 사용하므로 git pull 후 재배포 없이 즉시 반영됩니다.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  echo "사용법:"
  echo "  $0 global"
  echo "  $0 project /path/to/project"
  echo "  $0 remove global"
  echo "  $0 remove project /path/to/project"
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
  local target="$1"
  mkdir -p "$target/commands"

  # settings.json — 심링크
  ln -sf "$REPO_ROOT/settings.json" "$target/settings.json"
  echo "  ✓ settings.json → $target/settings.json"

  # agents/ — 심링크
  ln -sf "$REPO_ROOT/agents" "$target/agents"
  echo "  ✓ agents/ → $target/agents"

  # commands/*.md.template → commands/*.md (경로 치환)
  for tmpl in "$REPO_ROOT/commands"/*.md.template; do
    [[ -f "$tmpl" ]] || continue
    filename="$(basename "${tmpl%.template}")"
    dest="$target/commands/$filename"
    sed "s|__SKILL_ROOT__|$REPO_ROOT|g" "$tmpl" > "$dest"
    echo "  ✓ commands/$filename → $dest"
  done

  echo ""
  echo "배포 완료: $target"
  echo "Claude Code를 재시작하면 slash command가 활성화됩니다."
}

remove_deploy() {
  local target="$1"

  [[ -L "$target/settings.json" ]] && rm "$target/settings.json" && echo "  ✓ 제거: settings.json"
  [[ -L "$target/agents" ]] && rm "$target/agents" && echo "  ✓ 제거: agents/"

  for tmpl in "$REPO_ROOT/commands"/*.md.template; do
    [[ -f "$tmpl" ]] || continue
    filename="$(basename "${tmpl%.template}")"
    dest="$target/commands/$filename"
    [[ -f "$dest" ]] && rm "$dest" && echo "  ✓ 제거: commands/$filename"
  done

  echo "제거 완료: $target"
}

# ── 진입점 ──────────────────────────────────────────────────────────────

ACTION="${1:-}"
[[ -z "$ACTION" ]] && usage

if [[ "$ACTION" == "remove" ]]; then
  MODE="${2:-}"
  PROJECT_PATH="${3:-}"
  TARGET="$(resolve_target "$MODE" "$PROJECT_PATH")"
  remove_deploy "$TARGET"
else
  MODE="$ACTION"
  PROJECT_PATH="${2:-}"
  TARGET="$(resolve_target "$MODE" "$PROJECT_PATH")"
  deploy "$TARGET"
fi
