#!/usr/bin/env bash
# Claude Code statusLine command
# Reads JSON from stdin and prints a formatted status line.

input=$(cat)

# --- Working directory ---
cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // ""')

# --- Git branch (skip locking to avoid blocking) ---
git_branch=""
if [ -n "$cwd" ] && git -C "$cwd" rev-parse --is-inside-work-tree --no-optional-locks >/dev/null 2>&1; then
  git_branch=$(git -C "$cwd" --no-optional-locks symbolic-ref --short HEAD 2>/dev/null ||
    git -C "$cwd" --no-optional-locks rev-parse --short HEAD 2>/dev/null)
fi

# --- Model ---
model=$(echo "$input" | jq -r '.model.display_name // ""')

# --- Context usage ---
used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
if [ -n "$used_pct" ]; then
  context_str=$(printf "ctx:%.0f%%" "$used_pct")
else
  context_str="ctx:--"
fi

# --- Rate limits (5h and 7d) ---
five_pct=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage  // empty')
five_reset=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at        // empty')
week_pct=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage  // empty')
week_reset=$(echo "$input" | jq -r '.rate_limits.seven_day.resets_at        // empty')

fmt_remaining() {
  local epoch="$1"
  [ -z "$epoch" ] && echo "" && return
  local now secs h m
  now=$(date +%s)
  secs=$((epoch - now))
  [ "$secs" -le 0 ] && echo "" && return
  h=$((secs / 3600))
  m=$(((secs % 3600) / 60))
  if [ "$h" -gt 0 ]; then
    echo "${h}h${m}min"
  else
    echo "${m}min"
  fi
}

fmt_reset_day() {
  local epoch="$1"
  [ -z "$epoch" ] && echo "" && return
  date -d "@$epoch" "+%d/%m %H:%M" 2>/dev/null || echo ""
}

limits_str=""
if [ -n "$five_pct" ]; then
  remaining=$(fmt_remaining "$five_reset")
  if [ -n "$remaining" ]; then
    limits_str=$(printf "5h: %.0f%% ( %s )" "$five_pct" "$remaining")
  else
    limits_str=$(printf "5h: %.0f%% " "$five_pct")
  fi
fi
if [ -n "$week_pct" ]; then
  reset_time=$(fmt_reset_day "$week_reset")
  if [ -n "$reset_time" ]; then
    week_str=$(printf "7 dias: %.0f %%( %s )" "$week_pct" "$reset_time")
  else
    week_str=$(printf "7 dias: %.0f%% " "$week_pct")
  fi
  [ -n "$limits_str" ] && limits_str="$limits_str $week_str" || limits_str="$week_str"
fi

# --- Assemble parts ---
parts=()

[ -n "$cwd" ] && parts+=("$cwd")
[ -n "$git_branch" ] && parts+=("branch:$git_branch")
[ -n "$model" ] && parts+=("$model")
parts+=("$context_str")
[ -n "$limits_str" ] && parts+=("$limits_str")

# Join with " | "
out=""
for part in "${parts[@]}"; do
  [ -z "$out" ] && out="$part" || out="$out | $part"
done

printf '%s' "$out"
