/*
 * Junji Ito: Haunted Desktops
 *  - one looping video (or image) per virtual desktop
 *  - switching desktops soaks the next one in through an ink bleed (from the right going
 *    forward, from the left going back)
 *  - each video runs on a shared clock, so a desktop has moved on while you were away
 *  - hand-inked spirals creep in from the edges the longer the machine has been up
 *    (/proc/uptime: a reboot clears them)
 *  - everything stops while a maximized/fullscreen window covers the desktop or the
 *    battery is low
 */
pragma ComponentBehavior: Bound
import QtQuick
import QtMultimedia
import org.kde.plasma.plasmoid
import org.kde.plasma.plasma5support as P5Support
import org.kde.taskmanager as TaskManager

WallpaperItem {
    id: main
    anchors.fill: parent

    readonly property var cfg: main.configuration
    readonly property var files: [cfg.Video1, cfg.Video2, cfg.Video3, cfg.Video4, cfg.Video5]
        .filter(f => f && String(f).length > 0)
        .map(f => String(f).startsWith("file:") ? String(f) : "file://" + String(f))

    // ------------------------------------------------------------------ desktops
    TaskManager.VirtualDesktopInfo { id: vdi }
    TaskManager.ActivityInfo { id: activityInfo }
    readonly property int desk: Math.max(0, vdi.desktopIds.indexOf(vdi.currentDesktop))

    property int shown: -1
    property int front: 0
    readonly property var slots: [slotA, slotB]

    function fileFor(i) {
        return files.length ? files[i % files.length] : "";
    }

    function go(instant) {
        if (!files.length)
            return;
        const target = desk;
        if (target === shown && !instant)
            return;
        if (bleeding) {                               // switched again mid-bleed: settle it
            slots[1 - front].progress = 1;
            waitReady.stop();
            bleed.stop();
            endBleed();
        }
        const outgoing = slots[front];
        const incoming = slots[1 - front];
        const file = fileFor(target);
        const dir = shown < 0 ? 0 : (target > shown ? 1 : -1);
        shown = target;
        if (!instant && file === outgoing.file)
            return;                                   // same picture: nothing to do
        incoming.file = file;
        incoming.z = 2;
        outgoing.z = 1;
        if (instant || outgoing.file === "") {
            incoming.progress = 1;
            incoming.transitioning = false;
            finish();
            return;
        }
        incoming.origin = dir > 0 ? Qt.point(1.12, 0.45) : dir < 0 ? Qt.point(-0.12, 0.45) : Qt.point(0.5, 0.5);
        incoming.seed = Math.random();
        incoming.progress = 0;
        incoming.transitioning = true;
        bleeding = true;
        waitReady.slot = incoming;
        waitReady.tries = 0;
        waitReady.restart();
    }

    property bool bleeding: false
    function endBleed() {
        if (!bleeding)
            return;
        bleeding = false;
        finish();
    }

    function finish() {
        const incoming = slots[1 - front];
        const outgoing = slots[front];
        incoming.transitioning = false;
        front = 1 - front;
        outgoing.file = "";                           // free the decoder
        outgoing.z = 0;
    }

    Timer {
        id: waitReady
        property var slot: null
        property int tries: 0
        interval: 40
        repeat: true
        onTriggered: {
            tries++;
            if (slot && (slot.ready || tries > 40)) {
                stop();
                bleed.target = slot;
                bleed.start();
            }
        }
    }

    NumberAnimation {
        id: bleed
        property: "progress"
        from: 0
        to: 1
        duration: main.cfg.TransitionMs
        easing.type: Easing.InOutSine
        onFinished: main.endBleed()
        onStopped: main.endBleed()
    }

    onDeskChanged: {
        Qt.callLater(go, false);
        Qt.callLater(updateCovered);
    }
    onFilesChanged: Qt.callLater(go, true)
    Component.onCompleted: Qt.callLater(go, true)

    // ------------------------------------------------------------------ when to rest
    TaskManager.TasksModel {
        id: tasks
        sortMode: TaskManager.TasksModel.SortDisabled
        groupMode: TaskManager.TasksModel.GroupDisabled
        activity: activityInfo.currentActivity
        filterByActivity: true
        filterMinimized: true
        screenGeometry: main.parent?.screenGeometry ?? Qt.rect(0, 0, 0, 0)
        filterByScreen: true
        onDataChanged: Qt.callLater(main.updateCovered)
        onCountChanged: Qt.callLater(main.updateCovered)
        Component.onCompleted: {
            if (tasks.hasOwnProperty("filterByCurrentVirtualDesktop")) {
                tasks.filterByCurrentVirtualDesktop = true;
            } else {
                tasks.virtualDesktop = Qt.binding(() => vdi.currentDesktop);
                tasks.filterByVirtualDesktop = true;
            }
        }
    }
    property bool covered: false
    function updateCovered() {
        let c = false;
        for (let i = 0; i < tasks.count; i++) {
            const idx = tasks.index(i, 0);
            if (!tasks.data(idx, TaskManager.AbstractTasksModel.IsWindow))
                continue;
            if (tasks.data(idx, TaskManager.AbstractTasksModel.IsMaximized) ||
                tasks.data(idx, TaskManager.AbstractTasksModel.IsFullScreen)) {
                c = true;
                break;
            }
        }
        covered = c;
    }

    P5Support.DataSource {
        id: pm
        engine: "powermanagement"
        connectedSources: ["Battery"]
    }
    readonly property bool batteryLow: {
        const b = pm.data["Battery"];
        if (!b || !b["Has Cumulative"] || b["State"] !== "Discharging")
            return false;
        return b["Percent"] < cfg.PauseBatteryLevel;
    }
    readonly property bool shouldPlay: !(cfg.PauseWhenMaximized && covered) && !batteryLow

    // ------------------------------------------------------------------ the two slots
    component Slot: Item {
        id: slot
        property string file: ""
        readonly property bool isImage: /\.(png|jpe?g|webp|bmp|avif)$/i.test(file)
        property real progress: 1
        property real seed: 0
        property point origin: Qt.point(0.5, 0.5)
        property bool transitioning: false
        property bool hasFrame: false
        property bool shouldPlay: true
        readonly property bool ready: isImage ? still.status === Image.Ready : hasFrame
        readonly property bool active: file !== ""
        anchors.fill: parent
        visible: active

        onFileChanged: hasFrame = false

        MediaPlayer {
            id: player
            source: (!slot.isImage && slot.file) ? slot.file : ""
            loops: MediaPlayer.Infinite
            videoOutput: out
            onMediaStatusChanged: {
                if (mediaStatus === MediaPlayer.LoadedMedia) {
                    // shared clock: the scene kept going while you were elsewhere
                    if (duration > 0)
                        setPosition(Date.now() % duration);
                    play();
                    if (!slot.shouldPlay && !slot.transitioning)
                        pauseLater.restart();
                } else if (mediaStatus === MediaPlayer.BufferedMedia) {
                    firstFrame.restart();
                }
            }
        }
        Timer { id: firstFrame; interval: 70; onTriggered: slot.hasFrame = true }
        Timer { id: pauseLater; interval: 250; onTriggered: if (!slot.shouldPlay) player.pause() }

        onShouldPlayChanged: {
            if (isImage || !active)
                return;
            if (shouldPlay)
                player.play();
            else if (!transitioning)
                player.pause();
        }
        onTransitioningChanged: {
            if (!transitioning && !shouldPlay && !isImage && active)
                pauseLater.restart();
        }

        VideoOutput {
            id: out
            anchors.fill: parent
            fillMode: VideoOutput.PreserveAspectCrop
            visible: !slot.isImage
        }
        Image {
            id: still
            anchors.fill: parent
            source: slot.isImage ? slot.file : ""
            fillMode: Image.PreserveAspectCrop
            asynchronous: true
            cache: false
            visible: slot.isImage
        }

        layer.enabled: transitioning
        layer.effect: ShaderEffect {
            property variant source
            property real progress: slot.progress
            property real seed: slot.seed
            property real aspect: width / Math.max(1, height)
            property point origin: slot.origin
            fragmentShader: Qt.resolvedUrl("../shaders/inkbleed.frag.qsb")
        }
    }

    Rectangle {
        anchors.fill: parent
        color: "black"
        z: -1
    }
    Slot { id: slotA; shouldPlay: main.shouldPlay }
    Slot { id: slotB; shouldPlay: main.shouldPlay }

    // ------------------------------------------------------------------ the spiral spreads
    property real uptime: 0          // seconds since boot
    P5Support.DataSource {
        id: uptimeSrc
        engine: "executable"
        connectedSources: ["cat /proc/uptime"]
        interval: 60000
        onNewData: (source, data) => {
            const v = parseFloat(String(data["stdout"]).split(" ")[0]);
            if (!isNaN(v))
                main.uptime = v;
        }
    }
    readonly property real targetLevel: {
        if (cfg.SpiralLevelOverride >= 0)
            return Math.min(1, cfg.SpiralLevelOverride);
        const h = uptime / 3600;
        return Math.max(0, Math.min(1, (h - 0.33) / Math.max(0.1, cfg.SpiralHours)));
    }

    ShaderEffect {
        id: spiral
        anchors.fill: parent
        z: 10
        property real time: 0
        property real level: main.targetLevel
        Behavior on level { NumberAnimation { duration: 6000; easing.type: Easing.InOutSine } }
        property real aspect: width / Math.max(1, height)
        visible: main.cfg.SpiralEnabled && level > 0.002
        blending: true
        fragmentShader: Qt.resolvedUrl("../shaders/spiral.frag.qsb")
    }
    Timer {
        interval: 50
        repeat: true
        running: spiral.visible && main.shouldPlay
        triggeredOnStart: true
        onTriggered: spiral.time = (Date.now() / 1000) % 86400
    }
}
