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

# 파일 안의 placeholder를 실제 값으로 치환한다 (in-place).
#   __PROJECT_ROOT__ → 배포 대상 경로 (global=$HOME, project=실제경로)
#   __KIT_NAME__     → kit 디렉토리 이름 (배포 시 붙는 prefix와 항상 일치)
# sed -i 는 GNU/BSD 문법이 달라 임시 파일 + mv 로 처리한다.
substitute_placeholders() {
  local file="$1"
  local project_root="$2"
  local kit_name="$3"

  grep -q "__PROJECT_ROOT__\|__KIT_NAME__" "$file" 2>/dev/null || return 1

  local tmp="${file}.tmp.$$"
  sed -e "s|__PROJECT_ROOT__|${project_root}|g" \
      -e "s|__KIT_NAME__|${kit_name}|g" "$file" > "$tmp"
  mv "$tmp" "$file"
  return 0
}

# 배포 이름을 만든다. kit명을 prefix로 붙이되, 이름이 이미 kit명으로 시작하면 그대로 쓴다.
# kit 내부 파일명에 kit명을 반복하지 않아도 되게 해준다 (stutter 방지).
#   kit=terraform-generator, name=terraform-generator → terraform-generator
#   kit=terraform-generator, name=conventions         → terraform-generator-conventions
prefixed_name() {
  local kit="$1"
  local name="$2"
  case "$name" in
    "$kit"|"$kit"-*) echo "$name" ;;
    *)              echo "${kit}-${name}" ;;
  esac
}

# 파일을 대상 경로에 복사한 뒤 placeholder를 치환한다.
deploy_file() {
  local src="$1"           # 원본 파일
  local dest="$2"          # 배포 대상 경로
  local project_root="$3"  # __PROJECT_ROOT__ 치환값
  local kit_name="$4"      # __KIT_NAME__ 치환값
  local label="$5"         # 출력용 레이블

  rm -f "$dest"
  cp "$src" "$dest"
  if substitute_placeholders "$dest" "$project_root" "$kit_name"; then
    echo "  ✓ $label (PROJECT_ROOT=${project_root}, KIT_NAME=${kit_name})"
  else
    echo "  ✓ $label"
  fi
}

# 배포된 파일들이 참조하는 <target>/... 경로가 실제로 존재하는지 검증한다.
# placeholder 치환 결과가 실제 배포 파일명과 어긋나는 경우를 잡아낸다.
verify_references() {
  local target="$1"
  local project_root="$2"
  local missing=0
  local esc_root

  [[ -n "$project_root" ]] || return 0
  # grep 정규식에서 특수문자로 해석되지 않게 escape (구분자는 / 와 겹치지 않게 #)
  esc_root="$(printf '%s' "$project_root" | sed 's#[][\.*^$(){}?+|/]#\\&#g')"

  local search_dirs=()
  for d in skills agents rules; do
    if [[ -d "$target/$d" ]]; then search_dirs+=("$target/$d"); fi
  done
  [[ ${#search_dirs[@]} -gt 0 ]] || return 0

  while IFS= read -r -d '' f; do
    while IFS= read -r ref; do
      [[ -n "$ref" ]] || continue
      if [[ ! -e "$ref" ]]; then
        echo "  ⚠ 참조 경로 없음: ${ref}"
        echo "      ↳ 참조한 파일: ${f#"$target"/}"
        missing=$((missing + 1))
      fi
    done < <(grep -oE "${esc_root}/\.claude/[A-Za-z0-9_@./-]+" "$f" 2>/dev/null \
             | sed 's/[.,)]*$//' | sort -u)
  done < <(find "${search_dirs[@]}" -type f -print0 2>/dev/null)

  if [[ $missing -gt 0 ]]; then
    echo ""
    echo "  검증 실패: 존재하지 않는 경로 참조 ${missing}건."
    echo "  kit 파일에서 prefix를 하드코딩하지 말고 __KIT_NAME__ placeholder를 사용하세요."
    return 1
  fi
  echo "  ✓ 참조 경로 검증 통과"
  return 0
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
    [[ -d "$d/skills" || -d "$d/agents" || -d "$d/rules" ]] || continue

    # SKILL.md에서 description, deploy-scope 읽기
    skill_md="$(find "$d/skills" -name "SKILL.md" 2>/dev/null | head -1)"
    desc=""
    scope=""
    if [[ -f "$skill_md" ]]; then
      desc=$(grep "^description:" "$skill_md" | sed 's/^description:[[:space:]]*//' | cut -c1-60)
      scope=$(grep "^deploy-scope:" "$skill_md" | sed 's/^deploy-scope:[[:space:]]*//')
    fi

    printf "  %-22s" "$name"
    [[ -n "$scope" ]] && printf "[%-8s] " "$scope" || printf "[%-8s] " "both"
    [[ -n "$desc" ]] && printf "%s" "$desc"
    echo ""
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

  # skills/ — 디렉토리 단위 복사 후 placeholder 치환
  if [[ -d "$kit_dir/skills" ]]; then
    mkdir -p "$target/skills"
    for skill_dir in "$kit_dir/skills"/*/; do
      [[ -d "$skill_dir" ]] || continue
      skill_name="$(basename "$skill_dir")"
      deployed="$(prefixed_name "$kit_name" "$skill_name")"
      dest_dir="$target/skills/${deployed}"

      scope="$(read_deploy_scope "$skill_dir")"
      check_scope "$deployed" "$scope" "$MODE"

      rm -rf "$dest_dir"
      cp -r "$skill_dir" "$dest_dir"
      while IFS= read -r -d '' f; do
        substitute_placeholders "$f" "$project_root" "$kit_name" || true
      done < <(find "$dest_dir" -type f -print0)
      echo "  ✓ skills/${deployed}${project_root:+ (PROJECT_ROOT=${project_root}, KIT_NAME=${kit_name})}"
    done
  fi

  # agents/ — deploy_file로 개별 처리
  if [[ -d "$kit_dir/agents" ]]; then
    mkdir -p "$target/agents"
    for agent_file in "$kit_dir/agents"/*.md; do
      [[ -f "$agent_file" ]] || continue
      deployed="$(prefixed_name "$kit_name" "$(basename "$agent_file" .md)")"
      dest="$target/agents/${deployed}.md"
      deploy_file "$agent_file" "$dest" "$project_root" "$kit_name" "agents/${deployed}.md"
    done
  fi

  # rules/ — deploy_file로 개별 처리
  if [[ -d "$kit_dir/rules" ]]; then
    mkdir -p "$target/rules"
    for rule_file in "$kit_dir/rules"/*.md; do
      [[ -f "$rule_file" ]] || continue
      deployed="$(prefixed_name "$kit_name" "$(basename "$rule_file" .md)")"
      dest="$target/rules/${deployed}.md"
      deploy_file "$rule_file" "$dest" "$project_root" "$kit_name" "rules/${deployed}.md"
    done
  fi

  echo ""
  echo "참조 경로 검증 중..."
  if ! verify_references "$target" "$project_root"; then
    echo ""
    echo "배포는 완료되었으나 [$kit_name] 에 깨진 참조가 있습니다: $target"
    exit 1
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
      deployed="$(prefixed_name "$kit_name" "$(basename "$skill_dir")")"
      dest="$target/skills/${deployed}"
      if [[ -L "$dest" ]]; then
        rm "$dest" && echo "  ✓ 제거: skills/${deployed}"
      elif [[ -d "$dest" ]]; then
        rm -rf "$dest" && echo "  ✓ 제거: skills/${deployed}"
      fi
    done
  fi

  # agents — 심링크 또는 복사본(파일) 모두 제거
  if [[ -d "$kit_dir/agents" ]]; then
    for agent_file in "$kit_dir/agents"/*.md; do
      [[ -f "$agent_file" ]] || continue
      deployed="$(prefixed_name "$kit_name" "$(basename "$agent_file" .md)")"
      dest="$target/agents/${deployed}.md"
      if [[ -L "$dest" || -f "$dest" ]]; then
        rm "$dest" && echo "  ✓ 제거: agents/${deployed}.md"
      fi
    done
  fi

  # rules — 심링크 또는 복사본(파일) 모두 제거
  if [[ -d "$kit_dir/rules" ]]; then
    for rule_file in "$kit_dir/rules"/*.md; do
      [[ -f "$rule_file" ]] || continue
      deployed="$(prefixed_name "$kit_name" "$(basename "$rule_file" .md)")"
      dest="$target/rules/${deployed}.md"
      if [[ -L "$dest" || -f "$dest" ]]; then
        rm "$dest" && echo "  ✓ 제거: rules/${deployed}.md"
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
