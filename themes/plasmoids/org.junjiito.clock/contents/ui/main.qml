/*
    Ito Clock: time in brush script, the date in kanji, and a line from the
    Junji Ito universe that changes every quarter hour.
*/
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore

PlasmoidItem {
    id: root
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    preferredRepresentation: fullRepresentation

    property date now: new Date()
    Timer {
        interval: 1000; running: true; repeat: true; triggeredOnStart: true
        onTriggered: root.now = new Date()
    }

    readonly property var digits: ["〇", "一", "二", "三", "四", "五", "六", "七", "八", "九"]
    readonly property var weekdays: ["日", "月", "火", "水", "木", "金", "土"]
    readonly property var lines: [
        "the spiral is a curse, and the town is inside it",
        "however many pieces, each one grows back into her",
        "don't look at the spiral too long. it looks back",
        "there is a hole in the mountain shaped like you",
        "the balloons over town each wear a familiar face",
        "something walks out of the sea on metal legs",
        "everyone who loves her ends up wanting to kill her",
        "the lighthouse turns, and the town turns with it",
        "the wind blows in circles here",
        "her hair moves on its own. it always has",
        "you will dream of the long hallway again tonight",
        "the eye in the ceiling has not blinked in years"
    ]

    function kanjiNumber(n) {
        if (n <= 10) return n === 10 ? "十" : digits[n];
        if (n < 20) return "十" + digits[n - 10];
        const tens = Math.floor(n / 10), ones = n % 10;
        return digits[tens] + "十" + (ones ? digits[ones] : "");
    }

    fullRepresentation: ColumnLayout {
        Layout.preferredWidth: 420
        Layout.preferredHeight: 230
        spacing: 2

        Text {
            Layout.alignment: Qt.AlignRight
            text: Qt.formatTime(root.now, "HH:mm")
            color: "#e4e2dd"
            font.family: "Yuji Syuku"
            font.pixelSize: 96
            style: Text.Raised
            styleColor: "#000000"
        }
        Text {
            Layout.alignment: Qt.AlignRight
            text: root.kanjiNumber(root.now.getMonth() + 1) + "月" + root.kanjiNumber(root.now.getDate()) + "日"
                  + "　" + root.weekdays[root.now.getDay()] + "曜日"
            color: "#9a9a9a"
            font.family: "Zen Old Mincho"
            font.pixelSize: 24
            font.letterSpacing: 4
        }
        Rectangle {
            Layout.alignment: Qt.AlignRight
            Layout.topMargin: 10
            Layout.preferredWidth: 180
            Layout.preferredHeight: 1
            color: "#3a3a3a"
        }
        Text {
            Layout.alignment: Qt.AlignRight
            Layout.topMargin: 6
            Layout.maximumWidth: 420
            horizontalAlignment: Text.AlignRight
            wrapMode: Text.WordWrap
            text: root.lines[Math.floor(root.now.getTime() / 900000) % root.lines.length]
            color: "#6a6a6a"
            font.family: "Special Elite"
            font.pixelSize: 15
            font.letterSpacing: 1
        }
    }
}
