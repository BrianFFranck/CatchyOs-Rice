#!/usr/bin/env bash
# Builds every generated image/video used by the Junji Ito rice.
#   TOMIE_SRC   = Tomie artwork  (desktop video wallpaper + lock screen)
#   UZUMAKI_SRC = Uzumaki artwork (GRUB, Plymouth boot splash, SDDM login)
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT=$PWD
A=$ROOT/assets
B=$A/build
mkdir -p "$A" "$B"

TOMIE_SRC=${TOMIE_SRC:-$HOME/Desktop/1794044404583_image.png}
UZUMAKI_SRC=${UZUMAKI_SRC:-$HOME/Desktop/1794044517004_image.png}
FONTS=$HOME/.local/share/fonts/junji-ito
BRUSH=$FONTS/YujiSyuku-Regular.ttf
MINCHO=$FONTS/ZenOldMincho-SemiBold.ttf
TYPE=$FONTS/SpecialElite-Regular.ttf

W=1920; H=1080; FPS=24; LOOP=16          # 16 s seamless loop
PH=960                                    # portrait height on screen
PW=$(( 451 * PH / 927 ))                  # keep aspect (467)
PX=$(( (W - PW) / 2 )); PY=$(( (H - PH) / 2 ))

cp "$TOMIE_SRC"   "$A/tomie-original.png"
cp "$UZUMAKI_SRC" "$A/uzumaki-original.png"

echo ">> 1/7 spiral texture (hand-inked wobble, Uzumaki style)"
# Archimedean spiral, pitch 70px, radius wobble so it looks inked rather than computed.
ffmpeg -v error -y -f lavfi -i "color=black:s=2400x2400,format=gray" -frames:v 1 \
  -vf "geq=lum='st(0,X-W/2);st(1,Y-H/2);st(2,hypot(ld(0),ld(1)));st(3,atan2(ld(1),ld(0)));st(4,ld(2)+3.5*sin(9*ld(3)+ld(2)/37)+2*sin(23*ld(3)));255*pow(0.5+0.5*cos(2*PI*ld(4)/70-ld(3)),7)*min(1,ld(2)/90)'" \
  "$B/spiral.png"

echo ">> 2/7 portrait (upscaled, crushed blacks so it melts into the background)"
magick "$TOMIE_SRC" -colorspace Gray -filter Lanczos -resize ${PW}x${PH}! \
  -unsharp 0x0.8+0.6+0.02 -level 5%,97% "$B/portrait.png"

echo ">> 2b/7 animating the portrait (fake face peels, its eyes roll, both of them breathe)"
VENV=$HOME/.local/share/junji-ito-rice/venv
if ! "$VENV/bin/python" -c "import numpy, scipy, cv2" 2>/dev/null; then
  python3 -m venv --system-site-packages "$VENV"
  "$VENV/bin/pip" install -q numpy scipy opencv-python-headless
fi
rm -rf "$B/tomie-frames"
"$VENV/bin/python" -I "$ROOT/scripts/animate-tomie.py" "$B/portrait.png" "$B/tomie-frames" \
  --fps $FPS --loop $LOOP

echo ">> 3/7 spiral mask (spiral never touches Tomie, fades toward screen edges)"
magick -size ${W}x${H} xc:white -fill black \
  -draw "rectangle $((PX-14)),$((PY-14)) $((PX+PW+14)),$((PY+PH+14))" -blur 0x55 \
  \( -size ${W}x${H} radial-gradient:white-gray35 \) -compose Multiply -composite \
  -colorspace Gray "$B/mask.png"

echo ">> 4/7 kanji overlay"
# 富江 = Tomie · 伊藤潤二 = Junji Ito · 何度でも蘇る = "returns again and again"
magick -size ${W}x${H} xc:none \
  \( +size -background none -fill '#d8d8d8' -font "$BRUSH" -pointsize 104 -interline-spacing -8 label:$'富\n江' \) \
    -geometry +$((PX+PW+70))+190 -composite \
  \( +size -background none -fill '#6c6c6c' -font "$MINCHO" -pointsize 26 -interline-spacing 2 label:$'伊\n藤\n潤\n二' \) \
    -geometry +$((PX+PW+108))+470 -composite \
  \( +size -background none -fill '#8a8a8a' -font "$BRUSH" -pointsize 40 -interline-spacing 6 label:$'何\n度\nで\nも\n蘇\nる' \) \
    -geometry +$((PX-118))+300 -composite \
  \( +size -background none -fill '#4a4a4a' -font "$TYPE" -pointsize 17 label:'T O M I E   ·   1 9 8 7' -rotate 90 +repage \) \
    -geometry +$((PX-62))+330 -composite \
  "$B/kanji.png"

echo ">> 5/7 rendering the loop (takes a minute or two)"
# Periods of every animated term divide LOOP, so frame N == frame 0 and the loop is seamless.
G1="between(t,5.00,5.23)"; G2="between(t,11.40,11.53)"
ffmpeg -v error -stats -y \
  -loop 1 -framerate $FPS -t $LOOP -i "$B/spiral.png" \
  -loop 1 -framerate $FPS -t $LOOP -i "$B/mask.png" \
  -framerate $FPS -i "$B/tomie-frames/%04d.png" \
  -loop 1 -framerate $FPS -t $LOOP -i "$B/kanji.png" \
  -filter_complex "
    [0]rotate=a='-2*PI*t/$LOOP':ow=$W:oh=$H:c=black,format=gray[sp];
    [1]format=gray[mk];
    [sp][mk]blend=all_mode=multiply,lut=y='val*0.24',format=rgb24[bg];
    [2]format=rgb24,split[p1][p2];
    [p2]format=rgba,colorchannelmixer=aa=0.38[ghost];
    [bg][p1]overlay=x='$PX+if($G1,floor(9*sin(t*157)),0)+if($G2,-13,0)':y=$PY[c1];
    [c1][ghost]overlay=x='$PX+if($G1,26,-34)':y='$PY+if($G1,0,3)':enable='$G1+$G2'[c2];
    [c2][3]overlay=0:0,split[c3][band];
    [band]crop=$W:46:0:410[bandc];
    [c3][bandc]overlay=x='if(between(t,5.06,5.16),38,-22)':y=410:enable='between(t,5.06,5.16)+between(t,11.43,11.50)'[c4];
    [c4]eq=eval=frame:brightness='-abs(0.020*sin(2*PI*t/$LOOP)+0.012*sin(2*PI*t*23/$LOOP)+0.007*sin(2*PI*t*61/$LOOP))',
        vignette=angle=PI/4.4,
        noise=c0s=7:c0f=t,
        format=yuv420p[out]" \
  -map "[out]" -r $FPS -c:v libx264 -preset slow -crf 23 -profile:v high -g 48 \
  -movflags +faststart "$A/tomie-loop.mp4"

echo ">> 6/7 stills (lock screen = Tomie, boot/login = Uzumaki)"
ffmpeg -v error -y -ss 2 -i "$A/tomie-loop.mp4" -frames:v 1 "$A/tomie-still.png"
# Uzumaki source has lots of empty black padding: trim it to the framed art (≈847x1210).
magick "$UZUMAKI_SRC" -fuzz 12% -trim +repage -colorspace Gray -level 4%,98% "$B/uzumaki-art.png"
# Login (SDDM): art on the right, left half free for the login form.
magick -size ${W}x${H} xc:black \
  \( "$B/uzumaki-art.png" -filter Lanczos -resize x960 \) -gravity east -geometry +170+0 -composite \
  "$A/uzumaki-login.png"
# GRUB: same layout plus title text; the menu sits on the left.
magick "$A/uzumaki-login.png" \
  \( +size -background none -fill '#d0d0d0' -font "$BRUSH" -pointsize 120 label:'うずまき' \) \
    -gravity northwest -geometry +150+80 -composite \
  \( +size -background none -fill '#5a5a5a' -font "$TYPE" -pointsize 22 label:'the town is cursed with spirals' \) \
    -gravity northwest -geometry +158+232 -composite \
  "$A/grub-background.png"
# Plymouth: the art alone (its black matches the splash background)
magick "$B/uzumaki-art.png" -filter Lanczos -resize x820 "$A/uzumaki-plymouth.png"

echo ">> 7/8 spiral sprites (white ink on transparent: splash, Plymouth, SDDM)"
magick "$B/spiral.png" -gravity center -crop 1000x1000+0+0 +repage \
  \( -size 1000x1000 radial-gradient:white-black -level 0%,60% \) -compose Multiply -composite \
  "$B/spiral-alpha.png"
for s in 512 128; do
  magick -size 1000x1000 xc:white \( "$B/spiral-alpha.png" \) -alpha off -compose CopyOpacity -composite \
    -filter Lanczos -resize ${s}x${s} "$A/spiral-$s.png"
done

echo ">> 8/8 terminal background (spiral creeping in from the bottom-right corner)"
magick -size ${W}x${H} xc:'#070707' \
  \( "$B/spiral.png" -level 0%,100%,0.8 +level 0%,9% -gravity center -crop 1600x1600+0+0 +repage \
     \( -size 1600x1600 radial-gradient:white-black \) -compose Multiply -composite \) \
  -gravity southeast -geometry -800-800 -compose Screen -composite \
  -colorspace sRGB -type TrueColor "$A/term-bg.png"

# GRUB / greeter PNG loaders need plain 8-bit RGB(A), not 16-bit or grayscale
"$(dirname "$0")/normalize-png.sh" "$A"/*.png

ls -la "$A"
