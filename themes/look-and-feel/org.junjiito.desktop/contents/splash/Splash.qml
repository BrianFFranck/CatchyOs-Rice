/*
    Junji Ito login splash: a slowly turning Uzumaki spiral, 富江 in brush
    script, and a typewritten line that changes as Plasma loads.
*/
import QtQuick
import org.kde.kirigami as Kirigami

Rectangle {
    id: root
    color: "#000000"

    property int stage
    readonly property var lines: [
        "",
        "the eyes open",
        "the spiral turns",
        "she is coming back",
        "do not look behind you",
        "welcome home",
        "welcome home"
    ]

    onStageChanged: {
        if (stage === 2) {
            intro.running = true;
        } else if (stage === 5) {
            outro.running = true;
        }
        caption.opacity = 0;
        captionSwap.restart();
    }

    Item {
        id: content
        anchors.fill: parent
        opacity: 0

        Image {
            id: spiral
            anchors.centerIn: parent
            anchors.verticalCenterOffset: -Kirigami.Units.gridUnit * 2
            width: Math.min(parent.width, parent.height) * 0.36
            height: width
            source: "images/spiral.png"
            sourceSize.width: 512
            sourceSize.height: 512
            smooth: true
            opacity: 0.9
            RotationAnimator on rotation {
                from: 360; to: 0
                duration: 9000
                loops: Animation.Infinite
                running: true
            }
            SequentialAnimation on scale {
                loops: Animation.Infinite
                NumberAnimation { from: 0.96; to: 1.04; duration: 2600; easing.type: Easing.InOutSine }
                NumberAnimation { from: 1.04; to: 0.96; duration: 2600; easing.type: Easing.InOutSine }
            }
        }

        Text {
            id: title
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: spiral.bottom
            anchors.topMargin: Kirigami.Units.gridUnit * 1.5
            text: "富　江"
            color: "#e4e2dd"
            font.family: "Yuji Syuku"
            font.pixelSize: Kirigami.Units.gridUnit * 2.6
        }

        Text {
            id: caption
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: title.bottom
            anchors.topMargin: Kirigami.Units.gridUnit
            text: root.lines[Math.min(root.stage, root.lines.length - 1)]
            color: "#7a7a7a"
            font.family: "Special Elite"
            font.pixelSize: Kirigami.Units.gridUnit * 0.95
            font.letterSpacing: 3
            Behavior on opacity { NumberAnimation { duration: 450 } }
            Timer { id: captionSwap; interval: 120; onTriggered: caption.opacity = 1 }
        }

        // thin progress thread at the bottom
        Rectangle {
            anchors.bottom: parent.bottom
            anchors.bottomMargin: Kirigami.Units.gridUnit * 3
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width * 0.22
            height: 1
            color: "#1e1e1e"
            Rectangle {
                height: 1
                color: "#d9d7d2"
                width: parent.width * Math.min(1, root.stage / 5)
                Behavior on width { NumberAnimation { duration: 600; easing.type: Easing.OutCubic } }
            }
        }

        Text {
            anchors.bottom: parent.bottom
            anchors.right: parent.right
            anchors.margins: Kirigami.Units.gridUnit
            text: "伊藤潤二"
            color: "#3a3a3a"
            font.family: "Zen Old Mincho"
            font.pixelSize: Kirigami.Units.gridUnit * 0.9
        }
    }

    OpacityAnimator {
        id: intro
        target: content
        from: 0; to: 1
        duration: 900
        easing.type: Easing.InOutQuad
    }
    OpacityAnimator {
        id: outro
        target: spiral
        from: 0.9; to: 0
        duration: 900
        easing.type: Easing.InOutQuad
    }
}
