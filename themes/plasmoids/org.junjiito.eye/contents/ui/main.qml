/*
    Ito Eye: a hand-inked eye. It wanders, blinks, looks at the cursor while the
    cursor is over it, and flinches (pupil shrinks, shudders) when clicked.
*/
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore

PlasmoidItem {
    id: root
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    preferredRepresentation: compactRepresentation
    toolTipMainText: "見ている"
    toolTipSubText: "it is watching"

    compactRepresentation: Eye {
        inPanel: Plasmoid.formFactor === PlasmaCore.Types.Horizontal
                 || Plasmoid.formFactor === PlasmaCore.Types.Vertical
        bloodVein: Plasmoid.configuration.bloodVein
    }
    fullRepresentation: compactRepresentation
}
