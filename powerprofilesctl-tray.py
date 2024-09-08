#!/usr/bin/env python3
# based on https://github.com/ervinpopescu/dots/blob/lenovo/configs/bin/systray_profile.py
"""Python 3 script providing tray icon indicator for powerprofilesctl,
supports both legacy Application Indicator and modern Ayatana Application Indicator."""

import signal
import subprocess
import gi

from gi.repository import GLib
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk as gtk

try:
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import AppIndicator3 as appindicator
except ValueError:
    gi.require_version('AyatanaAppIndicator3', '0.1')
    from gi.repository import AyatanaAppIndicator3 as appindicator


class Indicator:
    """ Class for tray icon indicator"""

    def __init__(self):
        self.vp = None
        self.vpc()

        icons_folder = "/usr/share/icons/Adwaita/scalable/status"
        self.filenames = {
             "ic": f"{icons_folder}/power-profile-balanced-symbolic.svg",
             "bs": f"{icons_folder}/power-profile-power-saver-symbolic.svg",
             "ep": f"{icons_folder}/power-profile-performance-symbolic.svg",
        }
        self.icon_filename: str = self.filenames[self.vp]

        self.indicator = appindicator.Indicator.new(
            "customtray",
            "radio-symbolic",
            appindicator.IndicatorCategory.APPLICATION_STATUS,
        )
        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.menu())
        self.vpc()
        self.change_icon()
        self.start_timer()

    def vpc(self):
        """ Get current power profile"""

        vpcheck = (
            subprocess.check_output("powerprofilesctl get".split()).decode("utf-8").strip()
        )
        if vpcheck == "performance":
            self.vp = "ep"
        elif vpcheck == "balanced":
            self.vp = "ic"
        elif vpcheck == "power-saver":
            self.vp = "bs"

    def menu(self):
        """Handle indicator menu"""

        menu = gtk.Menu()

        title = gtk.MenuItem(label="Power profile")
        title.set_sensitive(False)
        menu.append(title)

        # TODO - include only available profiles as "powerprofilesctl list" reports
        perf_mode_1 = gtk.RadioMenuItem(label="Performance")
        menu.append(perf_mode_1)
        if self.vp == "ep":
            perf_mode_1.set_active(True)
        perf_mode_1.connect("activate", self.change_performance_mode, "performance")

        perf_mode_2 = gtk.RadioMenuItem(label="Balanced", group=perf_mode_1)
        menu.append(perf_mode_2)
        if self.vp == "ic":
            perf_mode_2.set_active(True)
        perf_mode_2.connect("activate", self.change_performance_mode, "balanced")

        perf_mode_3 = gtk.RadioMenuItem(label="Battery Saving", group=perf_mode_1)
        menu.append(perf_mode_3)
        if self.vp == "bs":
            perf_mode_3.set_active(True)
        perf_mode_3.connect("activate", self.change_performance_mode, "power-saver")

        menu.append(gtk.SeparatorMenuItem())

        quit_item = gtk.MenuItem(label="Quit")
        quit_item.connect('activate', self.destroy_cb, 'quit')
        menu.append(quit_item)

        menu.show_all()
        return menu

    def change_performance_mode(self, source, string):
        """ Change performance mode """

        subprocess.call(
            f"powerprofilesctl set {string}".split(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.vpc()
        self.indicator.set_icon_full(self.filenames[self.vp], '')

    def change_icon(self):
        """ Change tray icon """

        initial_vp = self.vp
        self.vpc()
        self.indicator.set_icon_full(self.filenames[self.vp], '')

        if initial_vp != self.vp:
            self.indicator.set_icon_full(self.filenames[self.vp], '')
            self.indicator.set_menu(self.menu())
        # for timer
        return True

    def start_timer(self):
        """ Create timer """

        GLib.timeout_add(5000, self.change_icon)

    def destroy_cb(self, widget, data=None):
        """ Handle Quit menu item """

        gtk.main_quit()


if __name__ == "__main__":
    indicator = Indicator()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    gtk.main()
