#!/usr/bin/env bash
# Link ppach into ~/.local/bin and the skill into ~/.claude/skills.
# Re-running is safe; anything that is not already our own link is left alone.
set -euo pipefail

root=$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)

link() {
  local target=$1 dest=$2
  mkdir -p "$(dirname "$dest")"
  if [ -L "$dest" ]; then
    if [ "$(readlink "$dest")" = "$target" ]; then
      echo "ok       $dest"
      return
    fi
    case $(readlink "$dest") in
      */phoenix-point-achievements/*) ;;  # an older checkout of this repo
      *) echo "skip     $dest (links elsewhere: $(readlink "$dest"))"; return ;;
    esac
  elif [ -e "$dest" ]; then
    echo "skip     $dest (exists and is not a link)"
    return
  fi
  ln -sfn "$target" "$dest"
  echo "linked   $dest -> $target"
}

link "$root/bin/ppach" "$HOME/.local/bin/ppach"
link "$root/skills/phoenix-point-achievements" "$HOME/.claude/skills/phoenix-point-achievements"

case ":$PATH:" in
  *":$HOME/.local/bin:"*) ;;
  *) echo "note: add ~/.local/bin to PATH, or run $root/bin/ppach directly" ;;
esac
