function fish_greeting --description 'Uzumaki fastfetch + a line from the Junji Ito universe'
    # Yakuake / tiny windows: just the quote
    if test (tput cols) -lt 90
        junji-quote
        return
    end
    command -q fastfetch; and fastfetch
    junji-quote
    echo
end
