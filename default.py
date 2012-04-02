# -*- coding: utf-8 -*-
import HTMLParser
import re
import urllib
import urllib2
import urlparse
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import sys

SAVE_FILE = True
MODE_SNURRAN = 'snurran'
MODE_SELECTED = 'selected'
MODE_VIDEO = 'video'

def parameters_string_to_dict(str):
    params = {}
    if str:
        pairs = str[1:].split("&")
        for pair in pairs:
            split = pair.split('=')
            if (len(split)) == 2:
                params[split[0]] = split[1]
    return params

def get_url(url, filename=None):
    req = urllib2.Request(url)
    req.add_header('User-Agent', ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
    response = urllib2.urlopen(req)
    url = response.geturl()
    html = response.read()
    response.close()
    if filename and SAVE_FILE:
        file = open(filename, 'w')
        file.write(html)
        file.close()
    return (url, html)

def baseUrl(url):
    (scheme, netloc, path, query, fragment) = urlparse.urlsplit(url)
    return urlparse.urlunsplit((scheme, netloc, '', '', ''))

def videoUrl(url):
    (scheme, netloc, path, query, fragment) = urlparse.urlsplit(url)
    if query.find('format=') > -1:
        query = query.replace('format=all', 'format=video')
    else:
        prefix = ''
        if len(query) > 0:
            prefix = '&'
        query += prefix + 'format=video&firstboxformat=video'
    return urlparse.urlunsplit((scheme, netloc, path, query, fragment))

def addItems(name, image, plot, url, mode, isFolder, handle, totalItems):
    for i in range(len(name)):
        li = xbmcgui.ListItem(name[i])
        if image:
            li.setThumbnailImage(image[i])
        infoLabels = {'Title': name[i]}
        if plot:
            infoLabels['Plot'] = plot[i]
        li.setInfo(type='Video', infoLabels=infoLabels)
        if mode == MODE_VIDEO:
            li.setProperty('IsPlayable', 'true')
        params = { 'url': url[i], 'mode': mode }
        url2 = sys.argv[0] + '?' + urllib.urlencode(params)
        xbmcplugin.addDirectoryItem(handle=handle, url=url2,
                                    listitem=li, isFolder=isFolder,
                                    totalItems=totalItems)

def main(handle, url):
    (url, html) = get_url(url, "main.html")
    addItems(['Snurran'], None, None, [url], MODE_SNURRAN, True, handle, 0)
    partial = re.findall('class="box-bar-left tabs"(.+?)class="formatfilter">',
                         html, re.DOTALL)[0]
    name = re.findall('<li id=".+?<a href=.+?>(.+?)</a></li>', partial)
    url = baseUrl(url)
    url2 = [url + x for x in re.findall('<li id=".+?<a href="(.+?)" id=',
                                        partial)]
    totalItems = 1 + len(name)
    # TODO image, plot
    addItems(name, None, None, url2, MODE_SELECTED, True, handle, totalItems)
    # TODO add Sök, ...
    partial = re.findall('<div class="topmenu">(.+?)</li>\s+</ul>\s+</div>',
                         html, re.DOTALL)[0]
    name = re.findall('<li><a href.+?>(.+?)</a>', partial)[1:]
    url2 = [url + x for x in re.findall('<li><a href="(.+?)"', partial)[1:]]
    addItems(name, None, None, url2, MODE_SELECTED, True, handle, totalItems)

def snurran(handle, url):
    (url, html) = get_url(url, "snurran.html")
    partial = re.findall('<div class="featurebrowser">.+?<div id=\'sliderBar\'>(.+?)</div> <a id=\'nextSlide\'>', html, re.DOTALL)[0]
    name = re.findall('<span>(.+?)</span>', partial)
    url2 = re.findall('<a href=\'(.+?)\'>', partial)
    image = re.findall(' style="background-image: url\((.+?)\)"', partial)
    addItems(name, image, None, url2, MODE_SELECTED, True, handle, len(name))

def selected(handle, url):
    (url, html) = get_url(url, 'select.html')
    url = baseUrl(url)
    if len(re.findall('class="selected">Program A-Ö<', html)) > 0:
        return a2o(handle, url, html)
    partial = re.findall('<div class="productlist(.+?)</a>\s+</div>\s+</div>',
                         html, re.DOTALL)
    if len(partial) > 0:
        # TODO total items
        name = re.findall('<span class="tv"></span>(.+?)</span>', partial[0])
        image = re.findall('<span><img src="(.+?)" id=', partial[0])
        description = re.findall('<a href=".+? title="(.+?)">', partial[0])
        url2 = [url + x for x in re.findall('<a href="(.+?)" id=', partial[0])]
        addItems(name, image, description, url2, MODE_VIDEO, False, handle,
                 len(name))
    if len(re.findall('class="selected">Ämnesord<', html)) > 0:
        (name2, url2) = cloud(handle, url, html)
        addItems(name2, None, None, url2, MODE_SELECTED, True, handle,
                 len(name2))

def a2o(handle, url, html):
    # TODO filter TV
    name = re.findall('<div class="serieslink">.+>(.+?)</a>', html)
    description = re.findall('<div class="serieslink">.+?title="(.+?)"', html)
    url2 = [url + x for x in
            re.findall('<div class="serieslink"><a href="(.+?)"', html)]
    addItems(name, None, description, url2, MODE_SELECTED, True, handle,
             len(name))

def cloud(handle, url, html):
    htmlParser = HTMLParser.HTMLParser()
    name = [htmlParser.unescape(x) for x in
            re.findall('<a href=.+? class="clouditem.+?>(.+?)<', html)]
    url2 = [url + x for x in re.findall('<a href="(.+?)".+? class="clouditem',
                                        html)]
    return (name, url2)

def video(handle, url):
    (url, html) = get_url(url, 'video.html')
    streamer = re.findall('var movieFlashVars.+?&streamer=(.+?)&', html)[0]
    pageUrl = re.findall('var movieFlashVars.+?&file=(.+?).mp4&', html)[0]
    url2 = streamer + '/mp4:' + pageUrl + '.mp4'
    image = re.findall('poster="(.+?)"', html)[0]
    description = re.findall('name="description" content="(.+?)"', html)[0]
    name = re.findall('<h1>(.+?)</h1>', html)[0]
    li = xbmcgui.ListItem(name)
    li.setThumbnailImage(image)
    infoLabels = {'Title': name, 'Plot': description }
    li.setInfo(type='Video', infoLabels=infoLabels)
    li.setPath(url2)
    xbmcplugin.setResolvedUrl(handle, True, li)
#    addItems(name, image, description, [url2], None, False, handle, 1)

params = parameters_string_to_dict(sys.argv[2])
mode = params.get('mode', None)
url = videoUrl(urllib.unquote_plus(params.get("url",  "")))
handle = int(sys.argv[1])

xbmc.log('params=' + str(params))
xbmc.log('mode=' + str(mode))
xbmc.log('url=' + str(url))

#TODO paging, barn har två delar: senaste program och senaste serier

if not mode:
    main(handle, 'http://urplay.se/')
elif mode == MODE_SNURRAN:
    snurran(handle, url)
elif mode == MODE_SELECTED:
    selected(handle, url)
else:
    video(handle, url)
if mode != MODE_VIDEO:
    xbmcplugin.endOfDirectory(handle, succeeded=True, cacheToDisc=True)
