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
        self.update_tooltip()
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

        available_profiles = self.get_available_profiles()

        # Add menu items based on available profiles
        radio_group = None
        for profile in available_profiles:
            profile_label = profile.capitalize()
            profile_mode = profile.lower().replace(" ", "-")
            perf_mode = gtk.RadioMenuItem(label=profile_label, group=radio_group)
            if not radio_group:
                radio_group = perf_mode  # Set the first radio button as the group leader
            menu.append(perf_mode)
            if self.vp == profile_mode:
                perf_mode.set_active(True)
            perf_mode.connect("activate", self.change_performance_mode, profile_mode)

        menu.append(gtk.SeparatorMenuItem())

        quit_item = gtk.MenuItem(label="Quit")
        quit_item.connect('activate', self.destroy_cb, 'quit')
        menu.append(quit_item)

        menu.show_all()
        return menu

    def get_available_profiles(self):
        """ Fetch available power profiles from powerprofilesctl """

        try:
            result = subprocess.run(['powerprofilesctl', 'list'], stdout=subprocess.PIPE, text=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"An error occurred: {e}")

        lines = result.stdout.splitlines()
        profiles = [line.replace('* ', '').replace(':', '').strip() for line in lines if line.endswith(':')]
        return profiles

    def change_performance_mode(self, source, string):
        """ Change performance mode """

        subprocess.call(
            f"powerprofilesctl set {string}".split(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.vpc()
        self.indicator.set_icon_full(self.filenames[self.vp], '')
        self.update_tooltip()

    def update_tooltip(self):
        """ Update the tray icon tooltip with the current profile name """

        profile_names = {
            "ic": "Balanced",
            "bs": "Battery Saving",
            "ep": "Performance",
        }
        current_profile = profile_names.get(self.vp, "Unknown")
        self.indicator.set_title(f"Current Profile: {current_profile}")

    def change_icon(self):
        """ Change tray icon """

        initial_vp = self.vp
        self.vpc()
        self.indicator.set_icon_full(self.filenames[self.vp], '')

        if initial_vp != self.vp:
            self.indicator.set_icon_full(self.filenames[self.vp], '')
            self.indicator.set_menu(self.menu())
            self.update_tooltip()
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
