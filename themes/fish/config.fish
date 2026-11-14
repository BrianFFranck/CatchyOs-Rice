# ── Junji Ito fish config ────────────────────────────────────────────
# Keep everything CachyOS sets up (aliases, done.fish, PATH, ...)
if test -f /usr/share/cachyos-fish-config/cachyos-config.fish
    source /usr/share/cachyos-fish-config/cachyos-config.fish
end

# bat (used for man pages) follows the terminal's monochrome palette
set -gx BAT_THEME ansi

# Monochrome syntax highlighting: commands white, args grey, errors blood.
set -g fish_color_normal d9d7d2
set -g fish_color_command f2f0eb --bold
set -g fish_color_keyword f2f0eb --bold
set -g fish_color_param b0b0b0
set -g fish_color_option 9a9a9a
set -g fish_color_quote c9c3b2
set -g fish_color_redirection 9aa0a0
set -g fish_color_end 6e6e6e
set -g fish_color_error b52a2a --underline
set -g fish_color_comment 4a4a4a --italics
set -g fish_color_operator 9a9a9a
set -g fish_color_escape a39494
set -g fish_color_autosuggestion 444444
set -g fish_color_valid_path --underline
set -g fish_color_search_match --background=262626
set -g fish_color_selection --reverse
set -g fish_pager_color_prefix f2f0eb --bold
set -g fish_pager_color_completion 9a9a9a
set -g fish_pager_color_description 5a5a5a
set -g fish_pager_color_progress 070707 --background=d9d7d2
set -g fish_pager_color_selected_background --background=262626

# Little rituals
alias spiral 'cava'                      # stare into it
alias uzumaki 'fastfetch'
abbr -a ito 'junji-quote'
