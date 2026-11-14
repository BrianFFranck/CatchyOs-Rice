#!/usr/bin/env python3
"""Synthesises the 'Junji Ito' freedesktop sound theme (no samples, no downloads).

  notifications      an ink drip falling in a stone room (sometimes two)
  warnings           a slow wooden creak, like a beam taking weight
  errors             two dull knocks and a low, beating minor second
  battery            a heartbeat (faster when it's urgent)
  login / logout     a struck rin (temple bowl) over a dark tritone drone
  trash              paper crumpling;  screenshot: an old mechanical shutter
  devices / power    a wooden tick and a small bowl, rising (in) or falling (out)
Anything not listed falls back to Ocean (Inherits=ocean).
usage: gen-sounds.py OUT_DIR        (writes OUT_DIR/index.theme and OUT_DIR/stereo/*.oga)
"""
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

SR = 48000
OUT = sys.argv[1]
rng = np.random.default_rng(1998)


def t_(dur):
    return np.arange(int(dur * SR)) / SR


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], btype='band', fs=SR, output='sos'), x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, btype='low', fs=SR, output='sos'), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, btype='high', fs=SR, output='sos'), x)


def place(dst, src, at):
    i = int(at * SR)
    n = min(len(src), len(dst) - i)
    if n > 0:
        dst[i:i + n] += src[:n]
    return dst


def reverb(x, decay=1.2, mix=0.3, tone=4500, pre=0.012, seed=0):
    """Stereo: x (mono) -> (N, 2). Exponentially decaying filtered noise IR, decorrelated L/R."""
    r = np.random.default_rng(seed)
    n = int(decay * 1.6 * SR)
    tt = np.arange(n) / SR
    out = []
    for ch in range(2):
        ir = r.standard_normal(n) * np.exp(-tt * 6.9 / decay)
        ir = lp(ir, tone)
        ir[: int(pre * SR)] = 0
        for d, g in ((0.017, 0.5), (0.029, 0.35), (0.041, 0.25)):     # a few early reflections
            k = int((d + 0.004 * ch) * SR); ir[k] += g * 30
        ir /= np.sqrt(np.sum(ir ** 2)) + 1e-9
        wet = fftconvolve(x, ir)[: len(x) + n]
        dry = np.pad(x, (0, len(wet) - len(x)))
        out.append(dry * (1 - mix) + wet * mix * 2.2)
    return np.stack(out, axis=1)


def finish(st, peak=0.5, tail_ms=40):
    st = st / (np.max(np.abs(st)) + 1e-9) * peak
    k = int(tail_ms * SR / 1000)
    st[-k:] *= np.linspace(1, 0, k)[:, None]
    # trim trailing silence
    e = np.max(np.abs(st), axis=1)
    last = np.nonzero(e > 1e-4)[0]
    return st[: (last[-1] + 1 if len(last) else len(st))]


# ------------------------------------------------------------------ instruments
def drip(pitch=1.0, amp=1.0):
    t = t_(0.18)
    f0 = 480 * pitch
    f = f0 * (1 + 1.7 * (1 - np.exp(-t / 0.011)))
    ph = 2 * np.pi * np.cumsum(f) / SR
    env = (1 - np.exp(-t / 0.0015)) * np.exp(-t / 0.042)
    plop = np.sin(2 * np.pi * 170 * pitch * t) * np.exp(-t / 0.012) * 0.35
    return (np.sin(ph) * env + plop) * amp


def rin(f=660, dur=3.5, amp=1.0, bright=1.0):
    t = t_(dur)
    ratios = (1.0, 2.71, 5.12, 8.21, 11.9)
    amps = (1.0, 0.55 * bright, 0.33 * bright, 0.18 * bright, 0.09 * bright)
    decs = (dur * 0.9, dur * 0.5, dur * 0.3, dur * 0.18, dur * 0.12)
    x = np.zeros_like(t)
    for r, a, d in zip(ratios, amps, decs):
        for det in (-0.55, 0.55):                        # beating, as a real bowl does
            x += a * 0.5 * np.sin(2 * np.pi * (f * r + det * r) * t + rng.uniform(0, 6.28)) * np.exp(-t / d)
    strike = bp(rng.standard_normal(len(t)), 2000, 6000) * np.exp(-t / 0.004) * 0.6
    return (x * (1 - np.exp(-t / 0.002)) + strike) * amp


def drone(dur, f=55.0, swell=1.6, fall=None):
    t = t_(dur)
    glide = 1.0 if fall is None else (1 - fall * t / dur)
    x = np.zeros_like(t)
    for r, a in ((1.0, 1.0), (1.414, 0.55), (2.0, 0.35), (2.83, 0.18), (3.0, 0.12)):
        ph = 2 * np.pi * np.cumsum(f * r * glide * (1 + 0.003 * np.sin(2 * np.pi * 0.21 * r * t))) / SR
        x += a * np.sin(ph)
    breath = lp(rng.standard_normal(len(t)), 380) * 0.9
    env = np.clip(t / swell, 0, 1) ** 2 * np.clip((dur - t) / (dur * 0.45), 0, 1)
    return (x * 0.5 + breath) * env


def knock(f=1.0, amp=1.0):
    t = t_(0.16)
    x = sum(a * np.sin(2 * np.pi * fr * f * t) * np.exp(-t / d)
            for fr, a, d in ((185, 1.0, 0.055), (415, 0.6, 0.032), (690, 0.35, 0.022), (1240, 0.15, 0.012)))
    click = hp(rng.standard_normal(len(t)), 1500) * np.exp(-t / 0.0015) * 0.5
    return (x + click) * amp


def creak(dur=0.75, base=26, amp=1.0, seed=3):
    r = np.random.default_rng(seed)
    t = t_(dur)
    rate = base * (1 + 0.55 * np.sin(np.pi * t / dur) + 0.25 * np.sin(2 * np.pi * 3.1 * t))
    ph = np.cumsum(rate / SR)
    pulses = np.zeros_like(t)
    idx = np.nonzero(np.diff(np.floor(ph)) > 0)[0]
    pulses[idx] = r.uniform(0.5, 1.0, len(idx))
    pulses = np.convolve(pulses, np.exp(-np.arange(int(0.004 * SR)) / (0.0008 * SR)), mode='same')
    x = bp(pulses, 170, 260, 2) * 1.0 + bp(pulses, 420, 520, 2) * 0.7 + bp(pulses, 1050, 1300, 2) * 0.35
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.7
    return x * env * amp


def heartbeat(beats=2, period=0.75, amp=1.0, soft=1.0):
    t_total = beats * period + 0.4
    out = np.zeros(int(t_total * SR))
    for b in range(beats):
        for dt, a, f0, f1 in ((0.0, 1.0, 85, 46), (0.27, 0.62, 95, 55)):
            t = t_(0.22)
            f = f1 + (f0 - f1) * np.exp(-t / 0.035)
            ph = 2 * np.pi * np.cumsum(f) / SR
            th = np.sin(ph) * (1 - np.exp(-t / 0.004)) * np.exp(-t / 0.075)
            th += lp(rng.standard_normal(len(t)), 300) * np.exp(-t / 0.01) * 0.25
            place(out, th * a * soft ** b, b * period + dt)
    return out * amp


def crumple(dur=0.7):
    t = t_(dur)
    x = np.zeros_like(t)
    n = int(dur * 380)
    for at in np.sort(rng.uniform(0, dur * 0.9, n)):
        L = int(rng.uniform(0.0008, 0.004) * SR)
        burst = rng.standard_normal(L) * np.exp(-np.arange(L) / (L / 3)) * rng.uniform(0.2, 1.0)
        place(x, burst, at)
    env = np.clip(t / 0.05, 0, 1) * np.clip((dur - t) / 0.25, 0, 1)
    return bp(x, 900, 7000) * env


def shutter():
    out = np.zeros(int(0.35 * SR))
    for at, a in ((0.0, 1.0), (0.072, 0.75)):
        t = t_(0.05)
        c = hp(rng.standard_normal(len(t)), 1800) * np.exp(-t / 0.0025) + np.sin(2 * np.pi * 3100 * t) * np.exp(-t / 0.008) * 0.6
        place(out, c * a, at)
    t = t_(0.2)
    place(out, np.sin(2 * np.pi * 1750 * t) * np.exp(-t / 0.05) * 0.08, 0.075)    # spring
    return out


# ------------------------------------------------------------------ the theme
def S(dur):
    return np.zeros(int(dur * SR))


sounds = {}


def make(name, mono, decay=1.0, mix=0.3, peak=0.5, tone=4500):
    sounds[name] = finish(reverb(mono, decay, mix, tone, seed=sum(map(ord, name))), peak)


# drips
x = S(0.6); place(x, drip(1.0), 0); place(x, drip(1.19, 0.45), 0.16)
make('message-new-instant', x, 1.1, 0.38, 0.42)
make('dialog-information', drip(1.0), 1.0, 0.38, 0.40)
x = S(0.5); place(x, drip(0.92), 0); place(x, drip(1.22, 0.7), 0.13)
make('dialog-question', x, 1.0, 0.36, 0.40)
x = S(0.6); place(x, drip(0.85), 0); place(x, drip(0.85, 0.6), 0.2); place(x, drip(1.05, 0.4), 0.33)
make('message-new-email', x, 1.1, 0.38, 0.40)
make('message-highlight', drip(1.3), 0.9, 0.35, 0.40)
x = S(0.6); place(x, drip(1.1), 0); place(x, drip(1.1, 0.8), 0.12)
make('message-attention', x, 1.0, 0.36, 0.44)
make('message-sent-instant', drip(1.45, 0.8), 0.6, 0.3, 0.30)
# creaks
make('dialog-warning', creak(0.8, 24), 0.7, 0.22, 0.42, 3500)
x = S(1.2); place(x, creak(0.7, 30, seed=5), 0); place(x, knock(0.9, 0.7), 0.72)
make('dialog-warning-auth', x, 0.7, 0.22, 0.42, 3500)
# errors: knock knock, then a low minor second that beats
def err(depth=1.0, scrape=False):
    x = S(2.2)
    place(x, knock(0.95 * depth), 0); place(x, knock(0.9 * depth, 0.8), 0.15)
    t = t_(1.6)
    f = 110 * depth
    tone = (np.sin(2 * np.pi * f * t) + np.sin(2 * np.pi * f * 1.0595 * t) + 0.5 * np.sin(2 * np.pi * f / 2 * t))
    tone *= np.clip(t / 0.06, 0, 1) * np.exp(-t / 0.55) * 0.55
    place(x, tone, 0.3)
    if scrape:
        place(x, creak(0.9, 18, 0.8, seed=8), 0.5)
    return x
make('dialog-error', err(1.0), 1.2, 0.28, 0.48, 3000)
make('completion-fail', err(1.1), 1.0, 0.25, 0.42, 3000)
make('outcome-failure', err(1.1), 1.0, 0.25, 0.42, 3000)
make('dialog-error-serious', err(0.85, True), 1.4, 0.3, 0.5, 2800)
make('dialog-error-critical', err(0.7, True), 1.6, 0.32, 0.55, 2500)
# heartbeat
make('battery-caution', heartbeat(3, 0.62, soft=0.9), 0.5, 0.15, 0.62, 2000)
make('battery-low', heartbeat(2, 0.9, soft=0.8), 0.5, 0.15, 0.55, 2000)
make('battery-full', rin(784, 2.2, 0.8), 1.6, 0.3, 0.32)
# bowls
make('completion-success', rin(990, 2.0), 1.5, 0.3, 0.32)
make('outcome-success', rin(990, 2.0), 1.5, 0.3, 0.32)
make('complete-media-burn', rin(880, 2.4), 1.6, 0.3, 0.32)
make('bell', rin(1320, 0.7, bright=0.5), 0.6, 0.2, 0.28)
make('bell-window-system', rin(1320, 0.6, bright=0.5), 0.5, 0.2, 0.26)
x = S(3.2)
for i in range(3):
    place(x, rin(880, 1.6, 1.0 - 0.15 * i), i * 0.9)
make('alarm-clock-elapsed', x, 1.6, 0.3, 0.42)
# devices & power
x = S(1.8); place(x, knock(1.3, 0.5), 0); place(x, rin(740, 1.5, 0.8), 0.08); place(x, rin(988, 1.3, 0.6), 0.22)
make('device-added', x, 1.2, 0.28, 0.34)
x = S(1.8); place(x, rin(988, 1.3, 0.6), 0); place(x, rin(740, 1.5, 0.8), 0.14); place(x, knock(1.0, 0.5), 0.3)
make('device-removed', x, 1.2, 0.28, 0.34)
x = S(1.6); place(x, rin(660, 1.4, 0.8), 0); place(x, rin(880, 1.2, 0.5), 0.12)
make('power-plug', x, 1.2, 0.28, 0.32)
x = S(1.6); place(x, rin(660, 1.2, 0.7), 0); place(x, knock(0.8, 0.6), 0.16)
make('power-unplug', x, 1.0, 0.25, 0.32)
make('media-insert-request', drip(0.8), 1.0, 0.35, 0.38)
# small things
make('audio-volume-change', knock(2.4, 1.0)[: int(0.06 * SR)] * np.hanning(int(0.06 * SR) * 2)[int(0.06 * SR):], 0.3, 0.12, 0.30)
make('trash-empty', crumple(0.75), 0.6, 0.2, 0.45)
make('camera-shutter', shutter(), 0.5, 0.15, 0.45)
make('screen-capture', shutter(), 0.5, 0.15, 0.45)
# login / logout
x = S(5.0)
place(x, drone(4.8, 55.0, swell=1.8), 0)
whisper = bp(rng.standard_normal(int(1.3 * SR)), 2500, 6500) * np.linspace(0, 1, int(1.3 * SR)) ** 3 * 0.25
place(x, whisper, 0.0)
place(x, rin(330, 4.0, 1.4), 1.25)
login_mono = x
make('desktop-login', x, 2.2, 0.35, 0.5)
x = S(4.0)
place(x, rin(294, 3.2, 1.3), 0.0)
place(x, drone(3.6, 55.0, swell=0.3, fall=0.12), 0.1)
make('desktop-logout', x, 2.0, 0.35, 0.48)
make('service-login', rin(587, 1.4, 0.7), 1.2, 0.3, 0.3)
make('service-logout', rin(440, 1.4, 0.7), 1.2, 0.3, 0.3)
make('theme-demo', login_mono, 2.2, 0.35, 0.5)

# ------------------------------------------------------------------ write
os.makedirs(os.path.join(OUT, 'stereo'), exist_ok=True)
with open(os.path.join(OUT, 'index.theme'), 'w') as f:
    f.write('[Sound Theme]\nName=Junji Ito\n'
            'Comment=Ink drips, creaking wood, a heartbeat and a temple bell in the dark\n'
            'Inherits=ocean\nDirectories=stereo\nExample=theme-demo\n\n[stereo]\nOutputProfile=stereo\n')
with tempfile.TemporaryDirectory() as tmp:
    for name, st in sounds.items():
        wav = os.path.join(tmp, name + '.wav')
        with wave.open(wav, 'wb') as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((np.clip(st, -1, 1) * 32767).astype('<i2').tobytes())
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', wav, '-c:a', 'libvorbis', '-q:a', '5',
                        os.path.join(OUT, 'stereo', name + '.oga')], check=True)
print(len(sounds), 'sounds written to', OUT)
