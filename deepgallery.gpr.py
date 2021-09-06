# File: images.gpr.py
register(GRAMPLET,
         id="DeepGallery",
         name=_("Deep Gallery"),
         description = _("Gramplet showing all media for active person"),
         version="0.0.1",
         gramps_target_version="5.1",
         status = STABLE,
         fname="deepgallery.py",
         height = 50,
         detached_width = 400,
         detached_height = 500,
         gramplet = 'DeepGallery',
         gramplet_title=_("Deep Gallery"),
         help_url="5.1_Addons#Addon_List",
         navtypes=['Person']
         )
