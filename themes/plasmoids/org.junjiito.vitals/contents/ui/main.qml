/*
    Ito Vitals: the machine's vital signs in the panel (CPU, temperature, memory,
    GPU, network). Readings turn blood red and breathe when the machine runs a
    fever. Click for the full chart: pen-line history, disk, swap, fan, and a
    button that opens btop.
*/
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as P5Support
import org.kde.ksysguard.sensors as Sensors

PlasmoidItem {
    id: root

    readonly property color paper: "#e4e2dd"
    readonly property color ink: "#7a7a7a"
    readonly property color blood: "#b52a2a"
    readonly property var cfg: Plasmoid.configuration
    readonly property int rate: Math.max(500, cfg.updateMs)

    // ------------------------------------------------------------ sensors
    component S: Sensors.Sensor { updateRateLimit: root.rate }
    S { id: cpu;      sensorId: "cpu/all/usage" }
    S { id: temp;     sensorId: "cpu/all/averageTemperature" }
    S { id: freq;     sensorId: "cpu/all/averageFrequency" }
    S { id: ram;      sensorId: "memory/physical/usedPercent" }
    S { id: ramUsed;  sensorId: "memory/physical/used" }
    S { id: ramTotal; sensorId: "memory/physical/total" }
    S { id: swap;     sensorId: "memory/swap/usedPercent" }
    S { id: gpu;      sensorId: "gpu/gpu0/usage" }
    S { id: disk;     sensorId: "disk/all/usedPercent" }
    S { id: down;     sensorId: "network/all/download" }
    S { id: up;       sensorId: "network/all/upload" }
    S { id: fan;      sensorId: "lmsensors/hp-isa-0000/fan1" }

    function n(s) { const v = Number(s.value); return isFinite(v) ? v : 0; }
    function pct(s) { return Math.round(n(s)) + "%"; }
    function bytes(b) {
        if (b < 1024) return Math.round(b) + "B";
        if (b < 1048576) return Math.round(b / 1024) + "K";
        if (b < 1073741824) return (b / 1048576).toFixed(1) + "M";
        return (b / 1073741824).toFixed(1) + "G";
    }
    function gib(b) { return (b / 1073741824).toFixed(1); }

    readonly property bool fever: n(temp) >= cfg.hotTemp
    readonly property bool cpuHot: n(cpu) >= 90
    readonly property bool ramHot: n(ram) >= 90

    // ------------------------------------------------------------ history for the popup
    readonly property int capacity: 60
    property var hCpu: []
    property var hTemp: []
    property var hRam: []
    property var hNet: []
    function push(arr, v) { const a = arr.slice(-(capacity - 1)); a.push(v); return a; }
    Timer {
        interval: root.rate; running: true; repeat: true; triggeredOnStart: true
        onTriggered: {
            root.hCpu = root.push(root.hCpu, root.n(cpu));
            root.hTemp = root.push(root.hTemp, root.n(temp));
            root.hRam = root.push(root.hRam, root.n(ram));
            root.hNet = root.push(root.hNet, root.n(down) + root.n(up));
        }
    }

    P5Support.DataSource {
        id: shell
        engine: "executable"
        onNewData: (source) => disconnectSource(source)
    }

    toolTipMainText: "体調  ·  vital signs"
    toolTipSubText: "CPU " + pct(cpu) + "   " + Math.round(n(temp)) + "°C   RAM " + gib(n(ramUsed))
                    + " / " + gib(n(ramTotal)) + " GiB   ↓" + bytes(n(down)) + "/s ↑" + bytes(n(up)) + "/s"

    // ------------------------------------------------------------ panel
    compactRepresentation: MouseArea {
        id: compact
        readonly property bool vertical: Plasmoid.formFactor === PlasmaCore.Types.Vertical
        Layout.minimumWidth: vertical ? -1 : grid.implicitWidth + 8
        Layout.preferredWidth: Layout.minimumWidth
        Layout.minimumHeight: vertical ? grid.implicitHeight + 8 : -1
        hoverEnabled: true
        onClicked: root.expanded = !root.expanded

        GridLayout {
            id: grid
            anchors.centerIn: parent
            flow: compact.vertical ? GridLayout.TopToBottom : GridLayout.LeftToRight
            rows: compact.vertical ? -1 : 1
            columns: compact.vertical ? 1 : -1
            columnSpacing: 10
            rowSpacing: 4

            VitalCell {
                visible: root.cfg.showCpu
                label: "cpu"; value: root.pct(cpu)
                fraction: root.n(cpu) / 100; hot: root.cpuHot
            }
            VitalCell {
                visible: root.cfg.showTemp
                label: "熱"; value: Math.round(root.n(temp)) + "°"
                fraction: Math.min(1, root.n(temp) / 100); hot: root.fever
            }
            VitalCell {
                visible: root.cfg.showRam
                label: "ram"; value: root.pct(ram)
                fraction: root.n(ram) / 100; hot: root.ramHot
            }
            VitalCell {
                visible: root.cfg.showGpu
                label: "gpu"; value: root.pct(gpu)
                fraction: root.n(gpu) / 100
            }
            VitalCell {
                visible: root.cfg.showNet
                label: "net"; value: "↓" + root.bytes(root.n(down)) + " ↑" + root.bytes(root.n(up))
            }
        }
    }

    // ------------------------------------------------------------ popup
    fullRepresentation: ColumnLayout {
        Layout.preferredWidth: 360
        Layout.minimumWidth: 320
        spacing: 10

        RowLayout {
            Layout.fillWidth: true
            Text {
                text: "体調"
                color: root.paper
                font.family: "Shippori Mincho B1"
                font.pixelSize: 26
                font.weight: Font.DemiBold
            }
            Text {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignBottom
                Layout.bottomMargin: 4
                text: root.fever ? "the machine has a fever" : "vital signs, all quiet"
                color: root.fever ? root.blood : root.ink
                font.family: "Special Elite"
                font.pixelSize: 12
                horizontalAlignment: Text.AlignRight
            }
        }
        Rectangle { Layout.fillWidth: true; height: 1; color: root.ink; opacity: 0.4 }

        component Reading: ColumnLayout {
            id: rd
            property string label
            property string value
            property string detail
            property var history: []
            property real maximum: 100
            property real hotAbove: -1
            property bool hot: false
            Layout.fillWidth: true
            spacing: 2
            RowLayout {
                Layout.fillWidth: true
                Text { text: rd.label; color: root.ink; font.family: "Special Elite"; font.pixelSize: 12 }
                Text {
                    Layout.fillWidth: true
                    text: rd.detail; color: root.ink; opacity: 0.8
                    font.family: "Special Elite"; font.pixelSize: 11
                    horizontalAlignment: Text.AlignRight
                }
                Text {
                    Layout.minimumWidth: 64
                    text: rd.value; color: rd.hot ? root.blood : root.paper
                    font.family: "Special Elite"; font.pixelSize: 17
                    horizontalAlignment: Text.AlignRight
                }
            }
            Sparkline {
                Layout.fillWidth: true
                values: rd.history; maximum: rd.maximum; hotAbove: rd.hotAbove
                capacity: root.capacity; stroke: root.paper; hotStroke: root.blood
            }
        }

        Reading {
            label: "cpu"; value: root.pct(cpu); hot: root.cpuHot
            detail: (root.n(freq) / 1000).toFixed(2) + " GHz"
            history: root.hCpu; hotAbove: 90
        }
        Reading {
            label: "熱  temperature"; value: Math.round(root.n(temp)) + "°C"; hot: root.fever
            detail: root.n(fan) > 0 ? "fan " + Math.round(root.n(fan)) + " rpm" : ""
            history: root.hTemp; hotAbove: root.cfg.hotTemp
        }
        Reading {
            label: "ram"; value: root.pct(ram); hot: root.ramHot
            detail: root.gib(root.n(ramUsed)) + " / " + root.gib(root.n(ramTotal)) + " GiB"
                    + (root.n(swap) > 0.5 ? "  ·  swap " + root.pct(swap) : "")
            history: root.hRam; hotAbove: 90
        }
        Reading {
            label: "net"; value: "↓" + root.bytes(root.n(down)) + "  ↑" + root.bytes(root.n(up))
            detail: "per second"
            history: root.hNet; maximum: Math.max(65536, ...root.hNet) * 1.15
        }

        Rectangle { Layout.fillWidth: true; height: 1; color: root.ink; opacity: 0.4 }
        GridLayout {
            Layout.fillWidth: true
            columns: 2
            columnSpacing: 12
            rowSpacing: 6
            VitalCell { Layout.fillWidth: true; label: "gpu"; value: root.pct(gpu); fraction: root.n(gpu) / 100 }
            VitalCell { Layout.fillWidth: true; label: "disk"; value: root.pct(disk); fraction: root.n(disk) / 100; hot: root.n(disk) >= 92 }
        }

        QQC2.Button {
            Layout.alignment: Qt.AlignRight
            text: "open btop"
            icon.name: "utilities-system-monitor"
            onClicked: { shell.connectSource("alacritty -e btop"); root.expanded = false; }
        }
    }
}
