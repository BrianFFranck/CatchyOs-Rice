import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import QtQuick.Dialogs
import org.kde.kirigami as Kirigami

Kirigami.FormLayout {
    id: root

    property string cfg_Video1
    property string cfg_Video2
    property string cfg_Video3
    property string cfg_Video4
    property string cfg_Video5
    property int cfg_TransitionMs
    property bool cfg_PauseWhenMaximized
    property int cfg_PauseBatteryLevel
    property bool cfg_SpiralEnabled
    property double cfg_SpiralHours
    property double cfg_SpiralLevelOverride

    property string picking: ""

    FileDialog {
        id: dialog
        title: "Choose a video or image"
        nameFilters: ["Videos and images (*.mp4 *.webm *.mkv *.mov *.png *.jpg *.jpeg *.webp)", "All files (*)"]
        onAccepted: root["cfg_" + root.picking] = selectedFile.toString().replace("file://", "")
    }

    PickRow {
        Kirigami.FormData.label: "Desktop 1:"
        value: root.cfg_Video1
        onEdited: v => root.cfg_Video1 = v
        onBrowse: { root.picking = "Video1"; dialog.open(); }
    }
    PickRow {
        Kirigami.FormData.label: "Desktop 2:"
        value: root.cfg_Video2
        onEdited: v => root.cfg_Video2 = v
        onBrowse: { root.picking = "Video2"; dialog.open(); }
    }
    PickRow {
        Kirigami.FormData.label: "Desktop 3:"
        value: root.cfg_Video3
        onEdited: v => root.cfg_Video3 = v
        onBrowse: { root.picking = "Video3"; dialog.open(); }
    }
    PickRow {
        Kirigami.FormData.label: "Desktop 4:"
        value: root.cfg_Video4
        onEdited: v => root.cfg_Video4 = v
        onBrowse: { root.picking = "Video4"; dialog.open(); }
    }
    PickRow {
        Kirigami.FormData.label: "Desktop 5:"
        value: root.cfg_Video5
        onEdited: v => root.cfg_Video5 = v
        onBrowse: { root.picking = "Video5"; dialog.open(); }
    }

    Item { Kirigami.FormData.isSection: true }

    QQC2.SpinBox {
        Kirigami.FormData.label: "Ink bleed (ms):"
        from: 0; to: 5000; stepSize: 100
        value: root.cfg_TransitionMs
        onValueModified: root.cfg_TransitionMs = value
    }
    QQC2.CheckBox {
        Kirigami.FormData.label: "Rest:"
        text: "Pause behind maximized and fullscreen windows"
        checked: root.cfg_PauseWhenMaximized
        onToggled: root.cfg_PauseWhenMaximized = checked
    }
    QQC2.SpinBox {
        Kirigami.FormData.label: "Pause on battery below (%):"
        from: 0; to: 100
        value: root.cfg_PauseBatteryLevel
        onValueModified: root.cfg_PauseBatteryLevel = value
    }

    Item { Kirigami.FormData.isSection: true }

    QQC2.CheckBox {
        Kirigami.FormData.label: "The spiral spreads:"
        text: "Spirals creep in from the edges while the machine stays awake"
        checked: root.cfg_SpiralEnabled
        onToggled: root.cfg_SpiralEnabled = checked
    }
    QQC2.SpinBox {
        Kirigami.FormData.label: "Hours until fully spread:"
        from: 1; to: 48
        value: Math.round(root.cfg_SpiralHours)
        onValueModified: root.cfg_SpiralHours = value
    }
    RowLayout {
        Kirigami.FormData.label: "Preview spread:"
        QQC2.Slider {
            id: prev
            Layout.preferredWidth: Kirigami.Units.gridUnit * 14
            from: -0.05; to: 1
            value: root.cfg_SpiralLevelOverride
            onMoved: root.cfg_SpiralLevelOverride = value < 0 ? -1 : value
        }
        QQC2.Label {
            text: root.cfg_SpiralLevelOverride < 0 ? "follows uptime" : Math.round(root.cfg_SpiralLevelOverride * 100) + "%"
        }
    }
}
