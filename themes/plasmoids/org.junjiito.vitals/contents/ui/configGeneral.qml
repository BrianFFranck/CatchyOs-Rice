import QtQuick
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM

KCM.SimpleKCM {
    property alias cfg_showCpu: cpu.checked
    property alias cfg_showTemp: temp.checked
    property alias cfg_showRam: ram.checked
    property alias cfg_showGpu: gpu.checked
    property alias cfg_showNet: net.checked
    property alias cfg_hotTemp: hot.value
    property alias cfg_updateMs: rate.value

    Kirigami.FormLayout {
        QQC2.CheckBox { id: cpu; Kirigami.FormData.label: "Show in panel:"; text: "CPU usage" }
        QQC2.CheckBox { id: temp; text: "CPU temperature" }
        QQC2.CheckBox { id: ram; text: "Memory" }
        QQC2.CheckBox { id: gpu; text: "GPU usage" }
        QQC2.CheckBox { id: net; text: "Network speed" }
        QQC2.SpinBox { id: hot; Kirigami.FormData.label: "Fever at (°C):"; from: 50; to: 105 }
        QQC2.SpinBox { id: rate; Kirigami.FormData.label: "Refresh every (ms):"; from: 500; to: 10000; stepSize: 500 }
    }
}
