# DeepGallery - Show all media associated with the active person
#
# Copyright (C) 2021  Hans Boldt
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""
Module deepgallery.py

Gramplet to show all media associated with the active person

Exports:

class DeepGallery

"""

#-------------------#
# Python modules    #
#-------------------#
import os
# import pdb

# import warnings
# warnings.simplefilter('always')

#-------------------#
# Gramps modules    #
#-------------------#
from gramps.gen.plug import Gramplet
from gramps.gen.const import GRAMPS_LOCALE as glocale
from gramps.gen.utils.file import media_path_full
from gramps.gui.utils import (is_right_click,
                              open_file_with_default_application)
from gramps.gen.utils.thumbnails import (get_thumbnail_image,
                                         SIZE_NORMAL, SIZE_LARGE)
from gramps.gui.editors import EditMedia
from gramps.gui.widgets.menuitem import add_menuitem

#------------------#
# Gtk modules      #
#------------------#
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

#------------------#
# Translation      #
#------------------#
try:
    _trans = glocale.get_addon_translator(__file__)
    _ = _trans.gettext
except ValueError:
    _ = glocale.translation.sgettext
ngettext = glocale.translation.ngettext # else "nearby" comments are ignored

#-------------#
# Messages    #
#-------------#
MSG_PHOTO_TOOLTIP = _('Double-click on the picture to edit the media object.')
MSG_VIEW = _('View')
MSG_OPEN_CONTAINING_FOLDER = _('Open Containing Folder')
MSG_EDIT = _('Edit')
MSG_MAKE_ACTIVE_MEDIA = _('Make Active Media')


#-------------------#
#                   #
# DeepGallery class #
#                   #
#-------------------#
class DeepGallery(Gramplet):
    """
    Images gramplet.
    """

    def init(self):
        """
        Gramplet initialization. Overrides method in class Gramplet.
        """
        self.gui.WIDGET = self.build_gui()
        self.gui.get_container_widget().remove(self.gui.textview)
        self.gui.get_container_widget().add(self.gui.WIDGET)
        self.image_list = list()


    def active_changed(self, handle):
        """
        Called when the active object is changed.

        Overrides method in class Gramplet.
        """
        self.update()


    def build_gui(self):
        """
        Build user interface.
        """
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.content_box.homogenous = False
        self.content_box.set_border_width(10)
        return self.content_box


    def add_image(self, media_handle):
        """
        Add one image from the media handle
        """
        media = self.dbstate.db.get_media_from_handle(media_handle)
        image = ImageBox(self.dbstate, self.uistate, media)
        self.content_box.pack_start(image, False, False, 5)
        self.image_list.append(image)


    def clear_images(self):
        """
        Remove all images from the Gramplet.
        """
        for image in self.image_list:
            self.content_box.remove(image)
        self.image_list = []


    def process_media(self, gobj):
        """
        Loop through items of media list, and save all media handles.
        """
        for media_ref in gobj.get_media_list():
            media_handle = media_ref.get_reference_handle()
            if not media_handle in self.all_media:
                media = self.dbstate.db.get_media_from_handle(media_handle)
                self.all_media[media_handle] = media.get_description()


    def process_citations(self, gobj):
        """
        Loop through citation list for specified object.
        """
        for cit_handle in gobj.get_citation_list():
            cit = self.dbstate.db.get_citation_from_handle(cit_handle)
            self.process_media(cit)


    def process_events(self, gobj):
        """
        Process events.
        """
        for event_ref in gobj.get_event_ref_list():
            event_handle = event_ref.get_reference_handle()
            event = self.dbstate.db.get_event_from_handle(event_handle)
            self.process_citations(event)


    def db_changed(self):
        """
        Overrides method in class Gramplet.

        Note: If an person, family, or event changes, the gallery may change.
        """
        self.connect(self.dbstate.db, 'person-update', self.update)
        self.connect(self.dbstate.db, 'family-add', self.update)
        self.connect(self.dbstate.db, 'family-update', self.update)
        self.connect(self.dbstate.db, 'family-delete', self.update)
        self.connect(self.dbstate.db, 'event-add', self.update)
        self.connect(self.dbstate.db, 'event-delete', self.update)
        self.connect(self.dbstate.db, 'event-update', self.update)
        self.connect(self.dbstate.db, 'citation-add', self.update)
        self.connect(self.dbstate.db, 'citation-delete', self.update)
        self.connect(self.dbstate.db, 'citation-update', self.update)
        self.connect(self.dbstate.db, 'media-add', self.update)
        self.connect(self.dbstate.db, 'media-delete', self.update)
        self.connect(self.dbstate.db, 'media-update', self.update)


    def main(self): # return false finishes
        """
        Generator which will be run in the background.

        Overrides method in class Gramplet.
        """
        self.clear_images()

        active_handle = self.get_active('Person')
        if not active_handle:
            return

        active = self.dbstate.db.get_person_from_handle(active_handle)
        self.all_media = dict()

        # Get all media for person
        self.process_media(active)

        # Get all media for person citations
        self.process_citations(active)

        # Get all media for person's name citations
        self.process_citations(active.get_primary_name())
        for name in active.get_alternate_names():
            self.process_citations(name)

        # Get all media for event citations
        self.process_events(active)

        # Get all media for family, and family event citations
        for family_handle in active.get_family_handle_list():
            family = self.dbstate.db.get_family_from_handle(family_handle)
            self.process_media(family)
            self.process_events(family)

        # Display all media
        media_list = list(self.all_media.items())
        media_list.sort(key=lambda x: x[1])
        for media in media_list:
            self.add_image(media[0])

        self.content_box.show_all()


class ImageBox(Gtk.Box):
    """
    Graphic for one image on the screen.
    """

    def __init__(self, dbstate, uistate, media):
        """
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        desc = media.get_description()

        photo = DeepPhoto(dbstate, uistate, media)
        photo.set_halign(Gtk.Align.START)
        self.pack_start(photo, False, False, 5)

        desc_label = Gtk.Label(label=desc)
        desc_label.set_halign(Gtk.Align.START)
        desc_label.set_justify(Gtk.Justification.LEFT)
        self.pack_start(desc_label, False, False, 5)

        self.show_all()


#------------------#
#                  #
# DeepPhoto class  #
#                  #
#------------------#
class DeepPhoto(Gtk.EventBox):
    """
    Like class Photo, but with different actions.
    """

    def __init__(self, dbstate, uistate, media):
        """
        __init__()
        """
        super().__init__()

        self.dbstate = dbstate
        self.uistate = uistate
        self.media = media
        self.handle = media.get_handle()

        self.connect('button-press-event', self._handle_button_press)
        self.connect('enter-notify-event', self.enter_notify)
        self.connect('leave-notify-event', self.leave_notify)
        self.set_tooltip_text(MSG_PHOTO_TOOLTIP)
        self.full_path = media_path_full(dbstate.db, media.get_path())
        self.folder = os.path.split(self.full_path)[0]

        self.photo = Gtk.Image()
        self.add(self.photo)
        self.mime_type = media.get_mime_type()
        self.normal_pixbuf = get_thumbnail_image(self.full_path,
                                                 self.mime_type,
                                                 None, SIZE_NORMAL)
        self.large_pixbuf = None
        self.photo.set_from_pixbuf(self.normal_pixbuf)


    def enter_notify(self, widget, event):
        """
        """
        if not self.large_pixbuf:
            self.large_pixbuf = get_thumbnail_image(self.full_path,
                                                    self.mime_type,
                                                    None, SIZE_LARGE)
        self.photo.set_from_pixbuf(self.large_pixbuf)


    def leave_notify(self, widget, event):
        """
        """
        self.photo.set_from_pixbuf(self.normal_pixbuf)


    def _handle_button_press(self, widget, event):
        """
        """
        if (event.type == Gdk.EventType.DOUBLE_BUTTON_PRESS
                and event.button == 1):
            EditMedia(self.dbstate, self.uistate, [], self.media)
            return True

        if is_right_click(event):
            if self.handle and self.uistate:
                self._show_menu(widget, event)
                return True

        return False


    def _show_menu(self, widget, event):
        """
        Show right-click menu
        """
        menu = Gtk.Menu()
        add_menuitem(menu, MSG_VIEW, widget,
                     lambda obj: open_file_with_default_application
                     (self.full_path, self.uistate))
        add_menuitem(menu, MSG_OPEN_CONTAINING_FOLDER, widget,
                     lambda obj: open_file_with_default_application
                     (self.folder, self.uistate))
        self._add_menu_separator(menu)
        add_menuitem(menu, MSG_EDIT, widget,
                     lambda obj: EditMedia(self.dbstate, self.uistate,
                                           [], self.media))
        self._add_menu_separator(menu)
        add_menuitem(menu, MSG_MAKE_ACTIVE_MEDIA, widget,
                     lambda obj: self.uistate.set_active(self.handle,
                                                         "Media"))
        menu.popup(None, None, None, None, event.button, event.time)


    @classmethod
    def _add_menu_separator(cls, menu):
        """
        Add separator to menu
        """
        sep = Gtk.SeparatorMenuItem()
        sep.show()
        menu.append(sep)
