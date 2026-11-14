/* One reading in the panel: grey typewriter label, paper-white value, and a thin
   ink line underneath that fills with the value. Turns blood red (and breathes)
   when `hot` is set. Standalone so it can be previewed without Plasma. */
import QtQuick

Item {
    id: cell
    property string label
    property string value
    property real fraction: -1          // 0..1 for the ink line, -1 hides it
    property bool hot: false
    property color paper: "#e4e2dd"
    property color ink: "#7a7a7a"
    property color blood: "#b52a2a"
    property real fontScale: 1

    implicitWidth: row.implicitWidth + 4
    implicitHeight: row.implicitHeight + 6

    Row {
        id: row
        anchors.centerIn: parent
        anchors.verticalCenterOffset: cell.fraction >= 0 ? -2 : 0
        spacing: 4
        Text {
            anchors.baseline: val.baseline
            text: cell.label
            color: cell.hot ? cell.blood : cell.ink
            font.family: "Special Elite"
            font.pixelSize: Math.round(10 * cell.fontScale)
        }
        Text {
            id: val
            text: cell.value
            color: cell.hot ? cell.blood : cell.paper
            font.family: "Special Elite"
            font.pixelSize: Math.round(14 * cell.fontScale)
            SequentialAnimation on opacity {
                running: cell.hot
                loops: Animation.Infinite
                alwaysRunToEnd: true
                NumberAnimation { to: 0.45; duration: 900; easing.type: Easing.InOutSine }
                NumberAnimation { to: 1.0; duration: 900; easing.type: Easing.InOutSine }
            }
        }
    }

    // ink line
    Rectangle {
        visible: cell.fraction >= 0
        anchors { left: row.left; right: row.right; top: row.bottom; topMargin: 2 }
        height: 1
        color: cell.ink
        opacity: 0.35
    }
    Rectangle {
        visible: cell.fraction >= 0
        anchors { left: row.left; top: row.bottom; topMargin: 1 }
        height: 2
        width: row.width * Math.max(0, Math.min(1, cell.fraction))
        color: cell.hot ? cell.blood : cell.paper
        opacity: 0.85
        Behavior on width { NumberAnimation { duration: 600; easing.type: Easing.OutCubic } }
    }
}
