# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# kod  - XBMC Plugin
# Canale polpotv
# ------------------------------------------------------------

from platformcode import logger
from core import scrapertools, httptools
from core.item import Item
from platformcode import config
from core import jsontools
import json
import datetime

host = "https://polpo.tv"

headers = [['Accept', 'application/ld+json']]

def mainlist(item):
    logger.info("kod.polpotv mainlist")
    itemlist = [Item(channel=item.channel,
                     title="[COLOR azure]Ultimi Film aggiunti[/COLOR]",
                     action="peliculas",
                     url="%s/api/movies?order[lastReleaseAt]=desc" %host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png",
                     extra="movie"),
                Item(channel=item.channel,
                     title="[COLOR azure]Film per anno[/COLOR]",
                     action="search_movie_by_year",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png",
                     extra="movie"),                       
                Item(channel=item.channel,
                     title="[COLOR azure]Film per genere[/COLOR]",
                     action="search_movie_by_genre",
                     url="%s/api/genres" %host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png",
                     extra="movie"),
                Item(channel=item.channel,
                     action="search",
                     title="[COLOR yellow]Cerca...[/COLOR]",
                     extra="movie",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),                                    
                ]
    return itemlist

def peliculas(item):
    logger.info("kod.polpotv peliculas")
    itemlist = []
    data = httptools.downloadpage(item.url, headers=headers).data
    json_object = jsontools.load(data)

    for movie in json_object['hydra:member']:
        itemlist.extend(get_itemlist_movie(movie,item))

    try:
        if json_object['hydra:view']['hydra:next'] is not None:
            itemlist.append(
                    Item(channel=item.channel,
                         action="peliculas",
                         title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                         url="%s"%host +json_object['hydra:view']['hydra:next'],
                         extra=item.extra,
                         thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png"))
    except:
        pass
    
    return itemlist
        
def search(item, texto):
    logger.info("kod.polpotv " + item.url + " search " + texto)
    itemlist=[]
    try:
        item.url = host + "/api/movies?originalTitle="+texto+"&translations.name=" +texto
        data = httptools.downloadpage(item.url, headers=headers).data
        json_object = jsontools.load(data)
        for movie in json_object['hydra:member']:
            itemlist.extend(get_itemlist_movie(movie,item))
        return itemlist
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
    
def search_movie_by_genre(item):
    logger.info("kod.polpotv search_movie_by_genre")
    itemlist = []
    data = httptools.downloadpage(item.url, headers=headers).data
    json_object = jsontools.load(data)
    for genre in json_object['hydra:member']:
        itemlist.append(
            Item(channel=item.channel,
             action="peliculas",
             title="[COLOR azure]" + genre['name'] + "[/COLOR]",
             contentType='movie',
             url="%s/api/movies?genres.id=%s" %(host,genre['id']),
             extra=item.extra))
    return itemlist

def search_movie_by_year(item):
    logger.info("kod.polpo.tv search_movie_by_year")
    now = datetime.datetime.now()
    year = int(now.year)
    result = []
    for i in range(100):
        year_to_search = year - i
        result.append(Item(channel=item.channel,
                           url="%s/api/movies?releaseDate=%s" %(host,year_to_search),
                           plot="1",
                           type="movie",
                           title="[COLOR azure]%s[/COLOR]" % year_to_search,
                           action="peliculas"))
    return result 
    
def findvideos(item):
    logger.info("kod.polpotv peliculas")
    itemlist = []
    data = httptools.downloadpage(item.url, headers=headers).data
    json_object = jsontools.load(data)
    for video in json_object['hydra:member'][0]['playlist']['videos']:
        data = httptools.downloadpage(video['src'], headers={'Origin': host},follow_redirects=None).data
        patron = 'href="([^"]+)"'
        video_link = scrapertools.find_single_match(data, patron)
        itemlist.append(
            Item(
                channel=item.channel,
                action="play",
                thumbnail=item.thumbnail,
                title=item.title +' [COLOR orange][' +str(video['size'])+ 'p][/COLOR]',
                url=video_link,
                folder=False))

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(
                Item(channel=item.channel, title="[COLOR yellow]%s[/COLOR]" % config.get_localized_string(30161), url=item.url,
                     action="add_pelicula_to_library", extra="findvideos", contentTitle=item.contentTitle))

    return itemlist

def get_itemlist_movie(movie,item):
    logger.info("kod.polpotv get_itemlist_movie")
    itemlist=[]
    try:
        if movie['originalLanguage']['id']=='it':
            scrapedtitle=movie['originalTitle']
        else:
            scrapedtitle=movie['translations'][1]['name']
        if scrapedtitle=='':
            scrapedtitle=movie['originalTitle']
    except:
        scrapedtitle=movie['originalTitle']
    try:
        scrapedplot=movie['translations'][1]['overview']
    except:
        scrapedplot = ""
    try:
        scrapedthumbnail="http://"+movie['posterPath']
    except:
        scrapedthumbnail=""
    try:
        scrapedfanart="http://"+movie['backdropPath']
    except:
        scrapedfanart=""
    itemlist.append(
        Item(channel=item.channel,
             action="findvideos",
             title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
             fulltitle=scrapedtitle,
             show=scrapedtitle,
             plot=scrapedplot,
             fanart=scrapedfanart,
             thumbnail=scrapedthumbnail,
             contentType='movie',
             contentTitle=scrapedtitle,
             url="%s%s/releases" %(host,movie['@id'] ),
             extra=item.extra))
    return itemlist
