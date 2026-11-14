/* Ito Eye drawing: standalone so it can be previewed without Plasma. */
import QtQuick
import QtQuick.Layouts

Item {
    id: eye
    property bool inPanel: false
    property bool bloodVein: true
    Layout.minimumWidth: inPanel ? height * 1.9 : 80
    Layout.preferredWidth: inPanel ? height * 1.9 : 240
    Layout.minimumHeight: inPanel ? 16 : 50
    Layout.preferredHeight: inPanel ? height : 130

    // gaze in [-1, 1]
    property real gx: 0
    property real gy: 0
    property real targetX: 0
    property real targetY: 0
    property real openness: 1.0      // 0 = shut, 1 = open
    property real pupil: 1.0         // pupil scale (flinch shrinks it)
    property real shake: 0
    property bool watching: false

    Behavior on gx { SpringAnimation { spring: 3.2; damping: 0.32; epsilon: 0.002 } }
    Behavior on gy { SpringAnimation { spring: 3.2; damping: 0.32; epsilon: 0.002 } }
    onTargetXChanged: gx = targetX
    onTargetYChanged: gy = targetY
    onGxChanged: canvas.requestPaint()
    onGyChanged: canvas.requestPaint()
    onOpennessChanged: canvas.requestPaint()
    onPupilChanged: canvas.requestPaint()
    onShakeChanged: canvas.requestPaint()
    onWidthChanged: canvas.requestPaint()
    onHeightChanged: canvas.requestPaint()

    // wander when nobody is looking
    Timer {
        interval: 1800; running: !eye.watching; repeat: true
        onTriggered: {
            interval = 900 + Math.random() * 3200;
            if (Math.random() < 0.35) { eye.targetX = 0; eye.targetY = 0; return; }
            eye.targetX = Math.random() * 2 - 1;
            eye.targetY = (Math.random() * 2 - 1) * 0.6;
        }
    }
    // blink
    Timer {
        interval: 3500; running: true; repeat: true
        onTriggered: { interval = 1800 + Math.random() * 5200; blink.restart(); }
    }
    SequentialAnimation {
        id: blink
        NumberAnimation { target: eye; property: "openness"; to: 0; duration: 90; easing.type: Easing.InQuad }
        PauseAnimation { duration: 40 }
        NumberAnimation { target: eye; property: "openness"; to: 1; duration: 140; easing.type: Easing.OutQuad }
    }
    // flinch
    SequentialAnimation {
        id: flinch
        ParallelAnimation {
            NumberAnimation { target: eye; property: "pupil"; to: 0.35; duration: 70 }
            NumberAnimation { target: eye; property: "openness"; to: 1.25; duration: 70 }
        }
        NumberAnimation { target: eye; property: "shake"; from: 0; to: 1; duration: 420 }
        PauseAnimation { duration: 600 }
        ParallelAnimation {
            NumberAnimation { target: eye; property: "pupil"; to: 1; duration: 900; easing.type: Easing.OutCubic }
            NumberAnimation { target: eye; property: "openness"; to: 1; duration: 900; easing.type: Easing.OutCubic }
        }
        ScriptAction { script: eye.shake = 0 }
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        onEntered: eye.watching = true
        onExited: { eye.watching = false; eye.targetX = 0; eye.targetY = 0; }
        onPositionChanged: mouse => {
            eye.targetX = Math.max(-1, Math.min(1, (mouse.x - width / 2) / (width / 2)));
            eye.targetY = Math.max(-1, Math.min(1, (mouse.y - height / 2) / (height / 2)));
        }
        onClicked: flinch.restart()
    }

    Canvas {
        id: canvas
        anchors.fill: parent
        antialiasing: true
        renderStrategy: Canvas.Cooperative

        onPaint: {
            const ctx = getContext("2d");
            ctx.reset();
            const W = width, H = height;
            const ew = Math.min(W * 0.94, H * 2.1);          // eye width
            const eh = ew * 0.40;                             // eye height when open
            const jitter = eye.shake > 0 ? Math.sin(eye.shake * 60) * (1 - eye.shake) * ew * 0.03 : 0;
            const cx = W / 2 + jitter, cy = H / 2;
            const open = Math.max(0.02, eye.openness);
            const up = eh * 0.62 * open;   // upper lid bulge
            const lo = eh * 0.48 * Math.min(1, open * 1.2);
            const lw = Math.max(1, ew / 70);

            function almond() {
                ctx.beginPath();
                ctx.moveTo(cx - ew / 2, cy);
                ctx.bezierCurveTo(cx - ew * 0.25, cy - up * 1.3, cx + ew * 0.25, cy - up * 1.3, cx + ew / 2, cy);
                ctx.bezierCurveTo(cx + ew * 0.25, cy + lo * 1.3, cx - ew * 0.25, cy + lo * 1.3, cx - ew / 2, cy);
                ctx.closePath();
            }

            // sclera
            ctx.save();
            almond();
            ctx.fillStyle = "#e2dfd8";
            ctx.fill();
            ctx.clip();

            // veins
            ctx.lineWidth = Math.max(0.6, lw * 0.45);
            ctx.strokeStyle = "rgba(60,60,60,0.55)";
            for (let i = 0; i < 6; i++) {
                const side = i % 2 ? 1 : -1;
                const sx = cx + side * ew * 0.48, sy = cy + (i - 2.5) * eh * 0.07;
                ctx.beginPath();
                ctx.moveTo(sx, sy);
                ctx.quadraticCurveTo(cx + side * ew * 0.33, sy + (i % 3 - 1) * eh * 0.12,
                                     cx + side * ew * (0.2 + 0.03 * i), cy + (i - 2.5) * eh * 0.05);
                ctx.stroke();
            }
            if (eye.bloodVein) {
                ctx.strokeStyle = "rgba(150,22,22,0.75)";
                ctx.beginPath();
                ctx.moveTo(cx + ew * 0.47, cy + eh * 0.05);
                ctx.quadraticCurveTo(cx + ew * 0.36, cy - eh * 0.12, cx + ew * 0.24, cy - eh * 0.02);
                ctx.stroke();
            }

            // iris + pupil
            const ir = eh * 0.46;
            const ix = cx + eye.gx * (ew / 2 - ir * 1.15);
            const iy = cy + eye.gy * eh * 0.18;
            const g = ctx.createRadialGradient(ix, iy, ir * 0.2, ix, iy, ir);
            g.addColorStop(0, "#3a3a3a");
            g.addColorStop(0.75, "#141414");
            g.addColorStop(1, "#000000");
            ctx.beginPath();
            ctx.arc(ix, iy, ir, 0, Math.PI * 2);
            ctx.fillStyle = g;
            ctx.fill();
            // hand-inked iris hatching
            ctx.strokeStyle = "rgba(200,198,193,0.35)";
            ctx.lineWidth = Math.max(0.5, lw * 0.35);
            for (let a = 0; a < Math.PI * 2; a += Math.PI / 14) {
                ctx.beginPath();
                ctx.moveTo(ix + Math.cos(a) * ir * 0.42, iy + Math.sin(a) * ir * 0.42);
                ctx.lineTo(ix + Math.cos(a + 0.12) * ir * 0.9, iy + Math.sin(a + 0.12) * ir * 0.9);
                ctx.stroke();
            }
            ctx.beginPath();
            ctx.arc(ix, iy, ir * 0.38 * eye.pupil, 0, Math.PI * 2);
            ctx.fillStyle = "#000000";
            ctx.fill();
            // catch-light
            ctx.beginPath();
            ctx.arc(ix - ir * 0.32, iy - ir * 0.34, ir * 0.13, 0, Math.PI * 2);
            ctx.fillStyle = "#f5f3ee";
            ctx.fill();

            // upper-lid shadow
            const sh = ctx.createLinearGradient(0, cy - up, 0, cy - up * 0.2);
            sh.addColorStop(0, "rgba(0,0,0,0.55)");
            sh.addColorStop(1, "rgba(0,0,0,0)");
            ctx.fillStyle = sh;
            ctx.fillRect(cx - ew / 2, cy - up * 1.3, ew, up * 1.2);
            ctx.restore();

            // outline + heavy upper lid line
            almond();
            ctx.lineWidth = lw;
            ctx.strokeStyle = "#d9d7d2";
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(cx - ew / 2, cy);
            ctx.bezierCurveTo(cx - ew * 0.25, cy - up * 1.3, cx + ew * 0.25, cy - up * 1.3, cx + ew / 2, cy);
            ctx.lineWidth = lw * 2.2;
            ctx.strokeStyle = "#f2f0eb";
            ctx.stroke();

            // lashes (only when the eye is big enough to read them)
            if (ew > 70) {
                ctx.lineWidth = lw * 0.9;
                for (let k = 1; k < 8; k++) {
                    const t = k / 8;
                    // point on upper lid bezier
                    const x = (1 - t) ** 3 * (cx - ew / 2) + 3 * (1 - t) ** 2 * t * (cx - ew * 0.25)
                            + 3 * (1 - t) * t * t * (cx + ew * 0.25) + t ** 3 * (cx + ew / 2);
                    const y = (1 - t) ** 3 * cy + 3 * (1 - t) ** 2 * t * (cy - up * 1.3)
                            + 3 * (1 - t) * t * t * (cy - up * 1.3) + t ** 3 * cy;
                    const ang = -Math.PI / 2 + (t - 0.5) * 1.6;
                    ctx.beginPath();
                    ctx.moveTo(x, y);
                    ctx.lineTo(x + Math.cos(ang) * ew * 0.05, y + Math.sin(ang) * ew * 0.05);
                    ctx.stroke();
                }
            }
        }
    }
}
