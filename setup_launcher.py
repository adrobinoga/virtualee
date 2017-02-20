import os
import shutil

local_desktop = os.path.join(os.environ['HOME'], '.local', 'share', 'applications', 'virtualee.desktop')
default_icon_path = os.path.join(os.environ['HOME'], '.local', 'share', 'icons', 'logo_virtualee.png')


def update_launcher(exe_path, path_logo):
    """
    Saves a desktop file for current executable, given a logo and path of current executable.
    :param exe_path: Path of current executable.
    :param path_logo: Path of logo to save in default icons dir.
    :return: None
    """
    # desktop file contents
    desktop_entry = \
        """
[Desktop Entry]
Name=Virtualee
Version=2.0
Comment=Client for eie-virtual site
Exec={0}
Terminal=false
Type=Application
Icon={1}
Categories=Application; Network;
""".format(exe_path, default_icon_path)

    # create folders for desktop and icon files in case they don't exists
    if not os.path.exists(os.path.dirname(local_desktop)):
        os.makedirs(os.path.dirname(local_desktop))
    if not os.path.exists(os.path.dirname(default_icon_path)):
        os.makedirs(os.path.dirname(default_icon_path))

    # save desktop file
    with open(local_desktop, 'w') as f:
        f.write(desktop_entry)

    # copy logo to icons dir
    shutil.copy2(path_logo, default_icon_path)
