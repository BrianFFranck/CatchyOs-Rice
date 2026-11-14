// Junji Ito rice: windows open with Burn-My-Windows' TV glitch (paper white) and close by
// winding into an inked Uzumaki spiral. Window filtering and the KWin plumbing follow
// Burn-My-Windows' KWin port.
// SPDX-FileCopyrightText: Vlad Zahorodnii, Martin Flöser, Simon Schneegans
// SPDX-License-Identifier: GPL-3.0-or-later
'use strict';

const classBlacklist = [
  'ksmserver ksmserver', 'ksmserver-logout-greeter ksmserver-logout-greeter',
  'ksplashqml ksplashqml', 'spectacle org.kde.spectacle',
  'yakuake org.kde.yakuake'          // the drop-down terminal has its own slide
];

class JunjiUzumakiEffect {
  constructor() {
    effect.configChanged.connect(this.loadConfig.bind(this));
    effect.animationEnded.connect(this.cleanupForcedRoles.bind(this));
    effects.windowAdded.connect(this.slotWindowAdded.bind(this));
    effects.windowClosed.connect(this.slotWindowClosed.bind(this));
    effects.windowDataChanged.connect(this.slotWindowDataChanged.bind(this));
    this.openShader = effect.addFragmentShader(Effect.MapTexture, 'tv-glitch.frag');
    this.closeShader = effect.addFragmentShader(Effect.MapTexture, 'uzumaki.frag');
    this.loadConfig();
  }

  rgb(key, fallback) {
    const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(effect.readConfig(key, fallback)) ||
              /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(fallback);
    return [parseInt(m[1], 16) / 255, parseInt(m[2], 16) / 255, parseInt(m[3], 16) / 255];
  }

  loadConfig() {
    this.openDuration = animationTime(effect.readConfig('OpenDuration', 520));
    this.closeDuration = animationTime(effect.readConfig('CloseDuration', 640));
    const c = this.rgb('Color', '#d9d7d2');
    effect.setUniform(this.openShader, 'uDuration', this.openDuration * 0.001);
    effect.setUniform(this.openShader, 'uScale', 1.0);
    effect.setUniform(this.openShader, 'uStrength', effect.readConfig('Strength', 2.0));
    effect.setUniform(this.openShader, 'uSpeed', 2.0);
    effect.setUniform(this.openShader, 'uColor', [c[0], c[1], c[2], 1.0]);
    effect.setUniform(this.closeShader, 'uColor', c);
    effect.setUniform(this.closeShader, 'uTurns', effect.readConfig('Turns', 1.6));
  }

  static shouldAnimateWindow(window) {
    if (window.windowClass == 'plasmashell plasmashell' ||
        window.windowClass == 'plasmashell org.kde.plasmashell') {
      return window.hasDecoration;
    }
    if (!window.hasDecoration && window.onAllDesktops) return false;
    if (classBlacklist.indexOf(window.windowClass) != -1) return false;
    if (window.hasDecoration) return true;
    if (window.popupWindow) return false;
    if (window.lockScreen || window.outline) return false;
    if (!window.managed) return false;
    return window.normalWindow || window.dialog;
  }

  setupForcedRoles(window) {
    window.setData(Effect.WindowForceBackgroundContrastRole, true);
    window.setData(Effect.WindowForceBlurRole, true);
  }

  cleanupForcedRoles(window) {
    window.setData(Effect.WindowForceBackgroundContrastRole, null);
    window.setData(Effect.WindowForceBlurRole, null);
  }

  slotWindowAdded(window) {
    if (effects.hasActiveFullScreenEffect) return;
    if (!JunjiUzumakiEffect.shouldAnimateWindow(window) || !window.visible) return;
    if (effect.isGrabbed(window, Effect.WindowAddedGrabRole)) return;
    this.setupForcedRoles(window);
    effect.setUniform(this.openShader, 'uForOpening', 1.0);
    effect.setUniform(this.openShader, 'uIsFullscreen', window.fullScreen ? 1.0 : 0.0);
    effect.setUniform(this.openShader, 'uSeed', Math.random());
    window.junjiIn = animate({
      window: window,
      curve: QEasingCurve.Linear,
      duration: this.openDuration,
      animations: [{ type: Effect.ShaderUniform, fragmentShader: this.openShader,
                     uniform: 'uProgress', from: 0.0, to: 1.0 }]
    });
  }

  slotWindowClosed(window) {
    if (effects.hasActiveFullScreenEffect) return;
    if (!JunjiUzumakiEffect.shouldAnimateWindow(window)) return;
    if (!window.visible || window.skipsCloseAnimation) return;
    if (effect.isGrabbed(window, Effect.WindowClosedGrabRole)) return;
    if (window.junjiIn) { cancel(window.junjiIn); delete window.junjiIn; }
    this.setupForcedRoles(window);
    effect.setUniform(this.closeShader, 'uForOpening', 0.0);
    effect.setUniform(this.closeShader, 'uIsFullscreen', window.fullScreen ? 1.0 : 0.0);
    window.junjiOut = animate({
      window: window,
      curve: QEasingCurve.Linear,
      duration: this.closeDuration,
      animations: [{ type: Effect.ShaderUniform, fragmentShader: this.closeShader,
                     uniform: 'uProgress', from: 0.0, to: 1.0 }]
    });
  }

  slotWindowDataChanged(window, role) {
    if (role == Effect.WindowAddedGrabRole && window.junjiIn && effect.isGrabbed(window, role)) {
      cancel(window.junjiIn); delete window.junjiIn; this.cleanupForcedRoles(window);
    } else if (role == Effect.WindowClosedGrabRole && window.junjiOut && effect.isGrabbed(window, role)) {
      cancel(window.junjiOut); delete window.junjiOut; this.cleanupForcedRoles(window);
    }
  }
}

new JunjiUzumakiEffect();
