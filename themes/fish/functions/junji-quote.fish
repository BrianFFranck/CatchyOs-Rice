function junji-quote --description 'Print a random line from the Junji Ito universe'
    set -l lines \
        "The spiral is not a shape. It is a curse, and the town is inside it." \
        "However many pieces you cut her into, each one grows back into Tomie." \
        "Don't look at the spiral for too long. It looks back." \
        "There is a hole in the mountainside shaped exactly like you." \
        "The balloons drifting over town each wear a familiar face." \
        "Something is walking out of the sea on metal legs. It smells of death." \
        "Souichi drives nails into his mouth and calls it a curse." \
        "Everyone who loves Tomie ends up wanting to kill her." \
        "The lighthouse turns, and the whole town turns with it." \
        "Kurouzu-cho: the wind blows in circles here." \
        "Her hair moves on its own. It always has." \
        "You will dream of the long hallway again tonight."
    set -l pick $lines[(random 1 (count $lines))]
    set_color 464646; echo -n '  〝 '
    set_color --italics a39d8c; echo -n $pick
    set_color 464646; echo ' 〟'
    set_color normal
end
