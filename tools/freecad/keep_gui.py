"""Keep the GUI settings (colours, materials, transparency, visibility) of an .FCStd that a
script rewrites.

FreeCADCmd has no GUI, so a document it saves has no GuiDocument.xml and FreeCAD opens it
with default colours. A generator calls take() before it overwrites the file and put()
after saving: the old GuiDocument.xml and the files it points to (ShapeAppearance,
DiffuseColor, ...) go back into the new file. View providers are matched by object Name,
which the generators keep stable; new objects get FreeCAD's defaults.
"""
import os
import re
import shutil
import tempfile
import zipfile


def take(path):
    """The GUI part of an existing .FCStd, or None if it has none."""
    if not os.path.exists(path):
        return None
    with zipfile.ZipFile(path) as z:
        if "GuiDocument.xml" not in z.namelist():
            return None
        xml = z.read("GuiDocument.xml")
        # FreeCAD reads these files in the order GuiDocument.xml names them, from a stream:
        # any other order and it skips them (colours lost, while inline values survive)
        order = list(dict.fromkeys(n.decode() for n in re.findall(rb'file="([^"]+)"', xml)))
        files = {n: z.read(n) for n in order if n in z.namelist()}
        thumb = "thumbnails/Thumbnail.png"
        if thumb in z.namelist():
            files = {thumb: z.read(thumb), **files}
    return xml, files


def put(path, gui):
    """Write `gui` (from take) into the .FCStd at `path`, replacing any GUI part it has."""
    if not gui:
        return 0
    xml, files = gui
    fd, tmp = tempfile.mkstemp(suffix=".FCStd", dir=os.path.dirname(path))
    os.close(fd)
    with zipfile.ZipFile(path) as src, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as dst:
        # the layout of a GUI save: the document's files, GuiDocument.xml, the thumbnail,
        # then the GUI files in the order GuiDocument.xml names them
        for item in src.infolist():
            if item.filename != "GuiDocument.xml" and item.filename not in files:
                dst.writestr(item, src.read(item.filename))
        dst.writestr("GuiDocument.xml", xml)
        for n, data in files.items():       # dicts keep insertion order: thumbnail, then as named
            dst.writestr(n, data)
    shutil.move(tmp, path)
    return len(re.findall(rb"<ViewProvider ", xml))
