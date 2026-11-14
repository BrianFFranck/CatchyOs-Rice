// Junji Ito: desktop + panel layout (run through org.kde.PlasmaShell.evaluateScript).
// Placeholders __HOME__ and __PANEL_COLORIZER_JSON__ are filled in by install-user.sh.
var HOME = "__HOME__";
var RICE = HOME + "/.local/share/junji-ito-rice";

// ---------------------------------------------------------------- desktop
var ds = desktops();
for (var i = 0; i < ds.length; i++) {
    var d = ds[i];
    var plugin = "luisbocanegra.smart.video.wallpaper.reborn";
    d.wallpaperPlugin = plugin;
    d.currentConfigGroup = ["Wallpaper", plugin, "General"];
    d.writeConfig("VideoUrls", JSON.stringify([{
        filename: "file://" + RICE + "/tomie-loop.mp4", enabled: true, duration: 0,
        customDuration: 0, playbackRate: 0, alternativePlaybackRate: 0, loop: true,
        dayNightCycleAssignment: 0
    }]));
    d.writeConfig("FillMode", 2);            // crop to fill
    d.writeConfig("BackgroundColor", "#000000");
    d.writeConfig("PauseMode", 0);           // pause behind maximized / fullscreen windows
    d.writeConfig("MuteMode", 5);
    d.writeConfig("Volume", 0);
    d.writeConfig("BatteryPausesVideo", true);
    d.writeConfig("PauseBatteryLevel", 15);
    d.writeConfig("ResumeLastVideo", true);
    d.writeConfig("CrossfadeEnabled", false);

    // brush-script clock in the top-right corner (only once)
    if (d.widgets("org.junjiito.clock").length === 0) {
        var g = screenGeometry(d.screen);
        d.addWidget("org.junjiito.clock", g.width - 470, 34, 440, 250);
    }
}

// ---------------------------------------------------------------- panel
var old = panels();
for (var p = 0; p < old.length; p++) old[p].remove();

var panel = new Panel("org.kde.panel");
panel.location = "bottom";
panel.height = 40;
panel.floating = true;
panel.hiding = "none";

var kickoff = panel.addWidget("org.kde.plasma.kickoff");
kickoff.currentConfigGroup = ["General"];
kickoff.writeConfig("icon", RICE + "/junji-spiral.svg");
kickoff.writeConfig("favoritesPortedToKAstats", true);

panel.addWidget("org.junjiito.eye");

var pager = panel.addWidget("org.dhruv8sh.kara");

panel.addWidget("org.kde.plasma.panelspacer");

var tasks = panel.addWidget("org.kde.plasma.icontasks");
tasks.currentConfigGroup = ["General"];
tasks.writeConfig("launchers", "preferred://filemanager,preferred://browser,applications:Alacritty.desktop");
tasks.writeConfig("iconSpacing", 2);

panel.addWidget("org.kde.plasma.panelspacer");

var vis = panel.addWidget("org.kde.plasma.icon");
vis.currentConfigGroup = ["General"];
vis.writeConfig("url", "file://" + HOME + "/.local/share/applications/junji-visualizer-toggle.desktop");
vis.writeConfig("localPath", HOME + "/.local/share/applications/junji-visualizer-toggle.desktop");

panel.addWidget("org.junjiito.vitals");   // CPU / temperature / RAM / network

panel.addWidget("org.kde.plasma.systemtray");

var clock = panel.addWidget("org.kde.plasma.digitalclock");
clock.currentConfigGroup = ["Appearance"];
clock.writeConfig("autoFontAndSize", false);
clock.writeConfig("fontFamily", "Shippori Mincho B1");
clock.writeConfig("fontWeight", 600);
clock.writeConfig("fontSize", 11);
clock.writeConfig("dateFormat", "custom");
clock.writeConfig("customDateFormat", "ddd d");
clock.writeConfig("showSeconds", 0);

var pc = panel.addWidget("luisbocanegra.panel.colorizer");
pc.currentConfigGroup = ["General"];
pc.writeConfig("isEnabled", true);
pc.writeConfig("hideWidget", true);
pc.writeConfig("lastPreset", HOME + "/.config/panel-colorizer/presets/Junji Ito/");
pc.writeConfig("globalSettings", JSON.stringify(__PANEL_COLORIZER_JSON__));

print("layout applied: " + desktops().length + " desktop(s), 1 panel");
