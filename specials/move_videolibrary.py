# -*- coding: utf-8 -*-

import xbmcgui, xbmc, os, sys
from platformcode import platformtools, xbmc_videolibrary, config
from core import filetools, scrapertools
from core.support import log, dbg
from distutils import dir_util, file_util
from xml.dom import minidom

global p
p = 0
progress = platformtools.dialog_progress('Spostamento Videoteca','Spostamento File')
progress.update(p, '')

def set_videolibrary_path(item):
    log()
    previous_path = config.get_setting('videolibrarypath')
    path = xbmcgui.Dialog().browse(3, 'Seleziona la cartella', 'files', '', False, False, config.get_setting('videolibrarypath'))
    log('New Videolibrary path:', path)
    log('Previous Videolibrary path:', previous_path)
    if path != previous_path:
        config.set_setting('videolibrarypath', path)
        set_new_path(path, previous_path)
        if platformtools.dialog_yesno('Spostare la Videoteca?', 'vuoi postare la videoteca e il relativo contenuto nella nuova posizione?'):
            move_videolibrary(path, previous_path)
            move_db(path, previous_path)
        progress.close()
        platformtools.dialog_ok('Spostamento Completato','')

def move_videolibrary(new, old):
    old = xbmc.translatePath(old)
    new = xbmc.translatePath(new)

    move_list = filetools.listdir(old)
    for d in move_list:
        od = filetools.join(old, d)
        nd = filetools.join(new, d)
        dir_util.copy_tree(od,nd)
        dir_util.remove_tree(od,1)
        global p
        p += 30
        progress.update(p, '')

def move_db(new, old):
    NEW = new
    OLD = old

    if new.startswith("special://") or scrapertools.find_single_match(new, r'(^\w+:\/\/)'):
        new = new.replace('/profile/', '/%/').replace('/home/userdata/', '/%/')
        sep = '/'
    else:
        sep = os.sep
    if not new.endswith(sep):
        new += sep

    if old.startswith("special://") or scrapertools.find_single_match(old, r'(^\w+:\/\/)'):
        old = old.replace('/profile/', '/%/').replace('/home/userdata/', '/%/')
        sep = '/'
    else:
        sep = os.sep
    if not old.endswith(sep):
        old += sep


    sql = 'SELECT idPath, strPath FROM path where strPath LIKE "%s"' % old
    nun_records, records = xbmc_videolibrary.execute_sql_kodi(sql)
    if records:
        idPath = records[0][0]
        strPath = records[0][1].replace(OLD, NEW)
        sql = 'UPDATE path SET strPath="%s" WHERE idPath=%s' % (strPath, idPath)
        nun_records, records = xbmc_videolibrary.execute_sql_kodi(sql)

    old += '%'
    sql = 'SELECT idPath, strPath FROM path where strPath LIKE "%s"' % old
    nun_records, records = xbmc_videolibrary.execute_sql_kodi(sql)
    if records:
        for record in records:
            idPath = record[0]
            strPath = record[1].replace(OLD, NEW)
            sql = 'UPDATE path SET strPath="%s"WHERE idPath=%s' % (strPath, idPath)
            nun_records, records = xbmc_videolibrary.execute_sql_kodi(sql)
    # dbg()
    sql = 'SELECT idMovie, c22 FROM movie where c22 LIKE "%s"' % old
    nun_records, records = xbmc_videolibrary.execute_sql_kodi(sql)
    if records:
        for record in records:
            idMovie = record[0]
            strPath = record[1].replace(OLD, NEW)
            sql = 'UPDATE movie SET c22="%s" WHERE idMovie=%s' % (strPath, idMovie)
            nun_records, records = xbmc_videolibrary.execute_sql_kodi(sql)
    sql = 'SELECT idEpisode, c18 FROM episode where c18 LIKE "%s"' % old
    nun_records, records = xbmc_videolibrary.execute_sql_kodi(sql)
    if records:
        for record in records:
            idEpisode = record[0]
            strPath = record[1].replace(OLD, NEW)
            sql = 'UPDATE episode SET c18="%s" WHERE idEpisode=%s' % (strPath, idEpisode)
            nun_records, records = xbmc_videolibrary.execute_sql_kodi(sql)
    global p
    p += 30
    progress.update(p, '')

def set_new_path(new, old):
    write = False
    SOURCES_PATH = xbmc.translatePath("special://userdata/sources.xml")
    if filetools.isfile(SOURCES_PATH):
        xmldoc = minidom.parse(SOURCES_PATH)

        # collect nodes
        # nodes = xmldoc.getElementsByTagName("video")
        video_node = xmldoc.childNodes[0].getElementsByTagName("video")[0]
        paths_node = video_node.getElementsByTagName("path")

        # delete old path
        for node in paths_node:
            if node.firstChild.data == old:
                parent = node.parentNode
                remove = parent.parentNode
                remove.removeChild(parent)

        # write changes
        if sys.version_info[0] >= 3: #PY3
            filetools.write(SOURCES_PATH, '\n'.join([x for x in xmldoc.toprettyxml().encode("utf-8").splitlines() if x.strip()]))
        else:
            filetools.write(SOURCES_PATH, b'\n'.join([x for x in xmldoc.toprettyxml().encode("utf-8").splitlines() if x.strip()]), vfs=False)

        # create new path
        list_path = [p.firstChild.data for p in paths_node]
        if new in list_path:
            log("path %s already exists in sources.xml" % new)
            return
        log("path %s does not exist in sources.xml" % new)

        # if the path does not exist we create one
        source_node = xmldoc.createElement("source")

        # <name> Node
        name_node = xmldoc.createElement("name")
        sep = os.sep
        if new.startswith("special://") or scrapertools.find_single_match(new, r'(^\w+:\/\/)'):
            sep = "/"
        name = new
        if new.endswith(sep):
            name = new[:-1]
        name_node.appendChild(xmldoc.createTextNode(name.rsplit(sep)[-1]))
        source_node.appendChild(name_node)

        # <path> Node
        path_node = xmldoc.createElement("path")
        path_node.setAttribute("pathversion", "1")
        path_node.appendChild(xmldoc.createTextNode(new))
        source_node.appendChild(path_node)

        # <allowsharing> Node
        allowsharing_node = xmldoc.createElement("allowsharing")
        allowsharing_node.appendChild(xmldoc.createTextNode('true'))
        source_node.appendChild(allowsharing_node)

        # Añadimos <source>  a <video>
        video_node.appendChild(source_node)

        # write changes
        if sys.version_info[0] >= 3: #PY3
            filetools.write(SOURCES_PATH, '\n'.join([x for x in xmldoc.toprettyxml().encode("utf-8").splitlines() if x.strip()]))
        else:
            filetools.write(SOURCES_PATH, b'\n'.join([x for x in xmldoc.toprettyxml().encode("utf-8").splitlines() if x.strip()]), vfs=False)

    else:
        xmldoc = minidom.Document()
        source_nodes = xmldoc.createElement("sources")

        for type in ['programs', 'video', 'music', 'picture', 'files']:
            nodo_type = xmldoc.createElement(type)
            element_default = xmldoc.createElement("default")
            element_default.setAttribute("pathversion", "1")
            nodo_type.appendChild(element_default)
            source_nodes.appendChild(nodo_type)
        xmldoc.appendChild(source_nodes)