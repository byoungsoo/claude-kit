#!/usr/bin/env bash
# Claude Code status line.
# Line 1: robbyrussell-style prompt (➜  dir git:(branch) ✗)
# Line 2: model, context window usage, cost, session duration

input=$(cat)

CYAN=$'\033[36m'
BCYAN=$'\033[1;36m'
BLUE=$'\033[34m'
RED=$'\033[31m'
YELLOW=$'\033[33m'
RESET=$'\033[0m'

# Palette (256-colour), all low-saturation so nothing shouts.
PATH_C=$'\033[38;5;252m'  # near-white, for the cwd on line 1
MODEL=$'\033[38;5;110m'   # pale steel blue
TOKENS=$'\033[38;5;175m'  # pale mauve
TRACK=$'\033[38;5;238m'   # separators
COST=$'\033[38;5;151m'    # pale mint
TIME=$'\033[38;5;183m'    # pale lilac
# The usage percentage shifts hue as context fills up.
PCT_LOW=$'\033[38;5;79m'  # pale teal
PCT_MID=$'\033[38;5;221m' # pale gold
PCT_HIGH=$'\033[38;5;210m' # pale coral

eval "$(printf '%s' "$input" | jq -r '
  @sh "dir=\(.workspace.current_dir // .cwd // "")
       model=\(.model.display_name // "")
       pct=\((.context_window.used_percentage // 0) | floor)
       used=\(((.context_window.total_input_tokens // 0) + (.context_window.total_output_tokens // 0)))
       size=\(.context_window.context_window_size // 200000)
       cost=\(.cost.total_cost_usd // 0)
       ms=\(.cost.total_duration_ms // 0)"
')"

# ---------- line 1: robbyrussell ----------
# Full path, with $HOME collapsed to ~ (zsh %~ rather than %c).
case "$dir" in
  "$HOME")   shown="~" ;;
  "$HOME"/*) shown="~${dir#"$HOME"}" ;;
  *)         shown="$dir" ;;
esac

line1="${CYAN}➜${RESET}  ${PATH_C}${shown}${RESET}"

if [ -n "$dir" ] && command -v git >/dev/null 2>&1 &&
   git -C "$dir" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  branch=$(git -C "$dir" symbolic-ref --short HEAD 2>/dev/null) ||
    branch=$(git -C "$dir" rev-parse --short HEAD 2>/dev/null) ||
    branch="(unknown)"
  line1+=" ${BLUE}git:(${RED}${branch}${BLUE})${RESET}"
  if [ -n "$(git -C "$dir" status --porcelain 2>/dev/null)" ]; then
    line1+=" ${YELLOW}✗${RESET}"
  fi
fi

# ---------- line 2: context usage ----------
# Colour by pressure: teal until 60%, gold to 85%, coral beyond.
if   [ "$pct" -ge 85 ]; then pct_c=$PCT_HIGH
elif [ "$pct" -ge 60 ]; then pct_c=$PCT_MID
else                         pct_c=$PCT_LOW
fi

# 15500 -> 15.5k, 200000 -> 200k
human() {
  awk -v n="$1" 'BEGIN{
    if (n < 1000) { printf "%d", n; exit }
    k = n / 1000
    if (k == int(k)) printf "%dk", k; else printf "%.1fk", k
  }'
}

# Separator carries its own leading space, so optional segments below can
# prepend it without ever leaving a dangling divider.
SEP="  ${TRACK}│${RESET}  "

line2="${MODEL}${model}${RESET}${SEP}${pct_c}${pct}%${RESET}"
line2+="${SEP}${TOKENS}$(human "$used")/$(human "$size")${RESET}"

# Cost and duration only once they are meaningful.
awk -v c="$cost" 'BEGIN{ exit !(c > 0) }' &&
  line2+="${SEP}${COST}\$$(awk -v c="$cost" 'BEGIN{printf "%.2f", c}')${RESET}"

if [ "$ms" -gt 0 ]; then
  line2+="${SEP}${TIME}$(( ms / 60000 ))m${RESET}"
fi

printf '%s\n%s\n' "$line1" "$line2"
