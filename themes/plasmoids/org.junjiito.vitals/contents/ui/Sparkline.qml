/* A pen line of recent history, scaled to `maximum`. Last point gets an ink drop. */
import QtQuick

Canvas {
    id: c
    property var values: []
    property real maximum: 100
    property color stroke: "#e4e2dd"
    property color hotStroke: "#b52a2a"
    property real hotAbove: -1
    property int capacity: 60
    implicitHeight: 34
    onValuesChanged: requestPaint()
    onWidthChanged: requestPaint()

    onPaint: {
        const ctx = getContext("2d");
        ctx.reset();
        const n = values.length;
        if (n < 2) return;
        const step = width / (capacity - 1);
        const x0 = width - (n - 1) * step;
        const y = v => height - 2 - (Math.min(v, maximum) / maximum) * (height - 4);
        const last = values[n - 1];
        const hot = hotAbove >= 0 && last >= hotAbove;
        // faint wash under the line
        ctx.beginPath();
        ctx.moveTo(x0, height);
        for (let i = 0; i < n; i++) ctx.lineTo(x0 + i * step, y(values[i]));
        ctx.lineTo(width, height);
        ctx.closePath();
        ctx.fillStyle = Qt.rgba(stroke.r, stroke.g, stroke.b, 0.08);
        ctx.fill();
        // the line
        ctx.beginPath();
        for (let i = 0; i < n; i++) {
            const px = x0 + i * step, py = y(values[i]);
            if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
        }
        ctx.lineWidth = 1.4;
        ctx.lineJoin = "round";
        ctx.strokeStyle = hot ? hotStroke : stroke;
        ctx.stroke();
        // ink drop on the newest reading
        ctx.beginPath();
        ctx.arc(width - 2, y(last), 2.2, 0, 2 * Math.PI);
        ctx.fillStyle = hot ? hotStroke : stroke;
        ctx.fill();
    }
}
