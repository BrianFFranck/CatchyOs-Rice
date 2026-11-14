import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

RowLayout {
    id: row
    property string value
    signal edited(string v)
    signal browse()
    QQC2.TextField {
        Layout.preferredWidth: Kirigami.Units.gridUnit * 22
        text: row.value
        placeholderText: "empty: repeats an earlier desktop"
        onEditingFinished: row.edited(text)
    }
    QQC2.Button {
        icon.name: "document-open"
        onClicked: row.browse()
    }
}
