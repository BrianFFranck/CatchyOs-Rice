#!/usr/bin/env bash
# Builds the per-desktop wallpaper loops (desktop 1 = tomie-loop.mp4 from build-assets.sh).
#   desktop 2  uzumaki   the hair spiral sinks into itself forever
#   desktop 3  remina    Hellstar Remina, balloons removed, the star alive
#   desktop 4  ink       a brush spiral that writes itself and blows away as ash
#   desktop 5  amigara   a torch searching the human-shaped holes of Amigara Fault
# usage: build-desktops.sh [uzumaki|remina|ink|amigara ...]   (default: all)
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT=$PWD
A=$ROOT/assets; B=$A/build; D=$A/desktops
mkdir -p "$B" "$D"
VENV=$HOME/.local/share/junji-ito-rice/venv
PY="$VENV/bin/python -I"
FONTS=$HOME/.local/share/fonts/junji-ito
BRUSH=$FONTS/YujiSyuku-Regular.ttf
MINCHO=$FONTS/ZenOldMincho-SemiBold.ttf
TYPE=$FONTS/SpecialElite-Regular.ttf
W=1920; H=1080; FPS=24; LOOP=16

# shared finish (same as Tomie): candle flicker, vignette, film grain
FINISH="eq=eval=frame:brightness='-abs(0.020*sin(2*PI*t/$LOOP)+0.012*sin(2*PI*t*23/$LOOP)+0.007*sin(2*PI*t*61/$LOOP))',vignette=angle=PI/4.4,noise=c0s=7:c0f=t,format=yuv420p"
ENC=(-r $FPS -c:v libx264 -preset slow -crf 22 -profile:v high -g 48 -movflags +faststart)

# kanji overlay: kanji <out> <panel-x> <panel-w> <big> <small> <small-colour> <line> <typewriter> <big-y> <small-y>
kanji() {
  local out=$1 px=$2 pw=$3 big=$4 small=$5 scol=$6 line=$7 tw=$8 by=$9 sy=${10}
  magick -size ${W}x${H} xc:none \
    \( +size -background none -fill '#d8d8d8' -font "$BRUSH" -pointsize 104 -interline-spacing -8 label:"$big" \) \
      -geometry +$((px+pw+70))+$by -composite \
    \( +size -background none -fill "$scol" -font "$MINCHO" -pointsize 26 -interline-spacing 2 label:"$small" \) \
      -geometry +$((px+pw+108))+$sy -composite \
    \( +size -background none -fill '#8a8a8a' -font "$BRUSH" -pointsize 40 -interline-spacing 6 label:"$line" \) \
      -geometry +$((px-118))+300 -composite \
    \( +size -background none -fill '#4a4a4a' -font "$TYPE" -pointsize 17 label:"$tw" -rotate 90 +repage \) \
      -geometry +$((px-62))+330 -composite \
    "$out"
}

build_uzumaki() {
  echo ">> desktop 2: uzumaki (spiral flow, ~2 min)"
  # art 847x1210 scaled to 960 high -> 672 wide, centred
  kanji "$B/kanji-uzumaki.png" 624 672 $'渦\n巻' $'伊\n藤\n潤\n二' '#6c6c6c' $'渦\nに\n呪\nわ\nれ\nた\n町' 'U Z U M A K I   ·   1 9 9 8' 190 470
  $PY scripts/animate-uzumaki.py "$A/uzumaki-original.png" --fps $FPS --loop $LOOP |
  ffmpeg -v error -stats -y -f rawvideo -pix_fmt gray -s ${W}x${H} -r $FPS -i - \
    -loop 1 -framerate $FPS -t $LOOP -i "$B/kanji-uzumaki.png" \
    -filter_complex "[0]format=rgb24[a];[a][1]overlay=0:0,$FINISH[out]" -map "[out]" "${ENC[@]}" "$D/2-uzumaki.mp4"
}

build_remina() {
  echo ">> desktop 3: remina (~1 min)"
  if [[ ! -f $A/remina-clean.png ]]; then
    # one-off: remove the balloons (needs venv-lama with torch + ~/.cache/junji-ito-rice/big-lama.pt)
    L=$HOME/.local/share/junji-ito-rice/venv-lama/bin/python
    cd src/remina
    $PY bubbles.py "$A/remina-original.jpg" body.png /dev/null 13
    $L -I -W ignore lama.py "$A/remina-original.jpg" body.png pass1.png
    $PY spikes.py pass1.png body.png spikes.png
    $L -I -W ignore lama.py pass1.png spikes.png pass2.png
    $PY skyline.py pass2.png seeded.png seam.png
    $L -I -W ignore lama.py seeded.png seam.png pass3.png
    magick body.png spikes.png -compose Lighten -composite seam.png -compose Lighten -composite repaired.png
    cp pass3.png "$A/remina-clean.png"; cp repaired.png "$A/remina-repaired.png"
    cd "$ROOT"
  fi
  # panel 659x929 scaled to 960 high -> 681 wide, centred
  kanji "$B/kanji-remina.png" 619 681 $'地\n獄\n星' $'レ\nミ\nナ' '#8e1b1b' $'あ\nの\n星\nが\n来\nる' 'H E L L S T A R   R E M I N A   ·   2 0 0 4' 170 600
  $PY scripts/animate-remina.py "$A/remina-clean.png" "$A/remina-repaired.png" --fps $FPS --loop $LOOP |
  ffmpeg -v error -stats -y -f rawvideo -pix_fmt rgb24 -s ${W}x${H} -r $FPS -i - \
    -loop 1 -framerate $FPS -t $LOOP -i "$B/kanji-remina.png" \
    -filter_complex "[0][1]overlay=0:0,$FINISH[out]" -map "[out]" "${ENC[@]}" "$D/3-remina.mp4"
}

build_ink() {
  echo ">> desktop 4: ink spiral (~1 min)"
  kanji "$B/kanji-ink.png" 500 800 '墨' $'す\nみ' '#6c6c6c' $'一\n筆\nの\n渦' 'S U M I   ·   O N E   S T R O K E' 220 360
  $PY scripts/animate-ink.py --fps $FPS --loop $LOOP |
  ffmpeg -v error -stats -y -f rawvideo -pix_fmt gray -s ${W}x${H} -r $FPS -i - \
    -loop 1 -framerate $FPS -t $LOOP -i "$B/kanji-ink.png" \
    -filter_complex "[0]format=rgb24[a];[a][1]overlay=0:0,$FINISH[out]" -map "[out]" "${ENC[@]}" "$D/4-ink.mp4"
}

build_amigara() {
  echo ">> desktop 5: amigara (~2 min)"
  kanji "$B/kanji-amigara.png" 560 800 '穴' $'ア\nミ\nガ\nラ\n断\n層' '#6c6c6c' $'こ\nこ\nは\n私\nの\n穴\nだ' 'T H E   E N I G M A   O F   A M I G A R A   F A U L T   ·   1 9 9 0' 220 360
  $PY scripts/animate-amigara.py --fps $FPS --loop $LOOP |
  ffmpeg -v error -stats -y -f rawvideo -pix_fmt gray -s ${W}x${H} -r $FPS -i - \
    -loop 1 -framerate $FPS -t $LOOP -i "$B/kanji-amigara.png" \
    -filter_complex "[0]format=rgb24[a];[a][1]overlay=0:0,$FINISH[out]" -map "[out]" "${ENC[@]}" "$D/5-amigara.mp4"
}

targets=("$@"); [[ ${#targets[@]} -eq 0 ]] && targets=(uzumaki remina ink amigara)
for t in "${targets[@]}"; do "build_$t"; done
cp "$A/tomie-loop.mp4" "$D/1-tomie.mp4"
ls -la "$D"
