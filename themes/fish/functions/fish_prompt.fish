function fish_prompt --description 'Junji Ito prompt: spiral, path, git; the arrow bleeds on error'
    set -l last_status $status
    set -l ink 464646
    set -l paper d9d7d2
    set -l grey 8c8c8c
    set -l blood b52a2a

    # line 1: ╭─ ꩜ ~/path  branch*
    set_color $ink; echo -n '╭─ '
    set_color $paper; echo -n '꩜ '
    set_color --bold f2f0eb; echo -n (prompt_pwd --full-length-dirs 2)
    set_color normal

    if command -q git; and git rev-parse --is-inside-work-tree &>/dev/null
        set -l branch (git symbolic-ref --short HEAD 2>/dev/null; or git rev-parse --short HEAD 2>/dev/null)
        set -l dirty ''
        if test -n "$(git status --porcelain --ignore-submodules 2>/dev/null | head -1)"
            set dirty ' ✱'
        end
        set_color $ink; echo -n '  ⟡ '
        set_color $grey; echo -n $branch
        set_color $blood; echo -n $dirty
    end

    if test $CMD_DURATION -gt 5000
        set_color $ink; echo -n '  ⧗ '(math -s1 $CMD_DURATION / 1000)'s'
    end
    echo

    # line 2: ╰─❯  (blood red when the last command failed)
    set_color $ink; echo -n '╰─'
    if test $last_status -ne 0
        set_color --bold $blood; echo -n "[$last_status]❯ "
    else
        set_color --bold $paper; echo -n '❯ '
    end
    set_color normal
end
