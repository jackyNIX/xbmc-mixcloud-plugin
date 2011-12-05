# -*- coding: utf-8 -*-

'''
@author: jackyNIX

Copyright (C) 2011 jackyNIX
 
This file is part of XBMC MixCloud Plugin.

XBMC MixCloud Plugin is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

XBMC MixCloud Plugin is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with XBMC MixCloud Plugin.  If not, see <http://www.gnu.org/licenses/>.

'''
import sys
import xbmc, xbmcgui, xbmcplugin
import urllib, urllib2
import simplejson as json
import time

PLUGIN_URL = 'plugin://music/MixCloud/'
API_URL = 'http://api.mixcloud.com/'
CATEGORIES_URL = 'http://api.mixcloud.com/categories/'
HOT_URL = 'http://api.mixcloud.com/popular/hot/'
NEW_URL = 'http://api.mixcloud.com/new/'
POPULAR_URL = 'http://api.mixcloud.com/popular/'
SEARCH_URL = 'http://api.mixcloud.com/search/'

MODE_HOME = 0
MODE_HOT = 10
MODE_NEW = 11
MODE_POPULAR = 12
MODE_CATEGORIES = 20
MODE_SEARCH = 30
MODE_PLAY = 40

QUERY_ARTIST = u'artist'
QUERY_AUDIOFORMATS = u'audio_formats'
QUERY_CLOUDCAST = u'cloudcast'
QUERY_CREATED = u'created_time'
QUERY_DATA = u'data'
QUERY_ID = u'id'
QUERY_FORMAT = u'format'
QUERY_KEY = u'key'
QUERY_LENGTH = u'audio_length'
QUERY_LARGE = u'large'
QUERY_MP3 = u'mp3'
QUERY_NAME = u'name'
QUERY_PICTURES = u'pictures'
QUERY_TAG = u'tag'
QUERY_TAGS = u'tags'
QUERY_TRACK = u'track'
QUERY_USER = u'user'

PARAM_MODE = u'mode'
PARAM_OFFSET = u'offset'
PARAM_KEY = u'key'
PARAM_QUERY = u'query'

plugin_handle = int(sys.argv[1])
limit = 20



def add_audio_item(infolabels, parameters={}, img='', thumbnail=''):
    listitem = xbmcgui.ListItem(infolabels['title'], infolabels['artist'], iconImage=thumbnail, thumbnailImage=img)
    listitem.setInfo('Music', infolabels)
    listitem.setProperty('IsPlayable', 'true')
    listitem.setProperty('Comment', infolabels['comment'])
    url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    xbmcplugin.addDirectoryItem(plugin_handle, url, listitem, isFolder=False, totalItems=limit+1)



def add_folder_item(name, infolabels={}, parameters={}, img=''):
    if not infolabels:
        infolabels = {"Title": name }
    listitem = xbmcgui.ListItem(name, iconImage=img, thumbnailImage=img)
    listitem.setInfo('Music', infolabels)
    url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    return xbmcplugin.addDirectoryItem(handle=plugin_handle, url=url, listitem=listitem, isFolder=True)



def show_home_menu():
    add_folder_item(name="Hot", parameters={PARAM_MODE: MODE_HOT, PARAM_OFFSET: 0})
    add_folder_item(name="New", parameters={PARAM_MODE: MODE_NEW, PARAM_OFFSET: 0})
    add_folder_item(name="Popular", parameters={PARAM_MODE: MODE_POPULAR, PARAM_OFFSET: 0})
    add_folder_item(name="Categories", parameters={PARAM_MODE: MODE_CATEGORIES, PARAM_OFFSET: 0})
    add_folder_item(name="Search", parameters={PARAM_MODE: MODE_SEARCH})
    xbmcplugin.endOfDirectory(handle=plugin_handle, succeeded=True)



def show_hot_menu(offset):
    found=get_cloudcasts(HOT_URL+'?',offset)
    if found==limit:
        add_folder_item(name="More...", parameters={PARAM_MODE: MODE_HOT, PARAM_OFFSET: offset+limit})
    xbmcplugin.endOfDirectory(handle=plugin_handle, succeeded=True)



def show_new_menu(offset):
    found=get_cloudcasts(NEW_URL+'?',offset)
    if found==limit:
        add_folder_item(name="More...", parameters={PARAM_MODE: MODE_NEW, PARAM_OFFSET: offset+limit})
    xbmcplugin.endOfDirectory(handle=plugin_handle, succeeded=True)



def show_popular_menu(offset):
    found=get_cloudcasts(POPULAR_URL+'?',offset)
    if found==limit:
        add_folder_item(name="More...", parameters={PARAM_MODE: MODE_POPULAR, PARAM_OFFSET: offset+limit})
    xbmcplugin.endOfDirectory(handle=plugin_handle, succeeded=True)



def show_categories_menu(key,offset):
    if key=='':
        get_categories(CATEGORIES_URL)
    else:
        found=get_cloudcasts(API_URL+key[1:len(key)-1]+'/cloudcasts/?',offset)
        if found==limit:
            add_folder_item(name="More...", parameters={PARAM_MODE: MODE_CATEGORIES, PARAM_KEY: key, PARAM_OFFSET: offset+limit})
    xbmcplugin.endOfDirectory(handle=plugin_handle, succeeded=True)



def show_search_menu(key,query,offset):
    if key=='':
        add_folder_item(name="Cloudcast", parameters={PARAM_MODE: MODE_SEARCH, PARAM_KEY: QUERY_CLOUDCAST, PARAM_OFFSET: 0})
        '''add_folder_item(name="User", parameters={PARAM_MODE: MODE_SEARCH, PARAM_KEY: QUERY_USER, PARAM_OFFSET: 0})'''
        '''add_folder_item(name="Tag", parameters={PARAM_MODE: MODE_SEARCH, PARAM_KEY: QUERY_TAG, PARAM_OFFSET: 0})'''
        '''add_folder_item(name="Artist", parameters={PARAM_MODE: MODE_SEARCH, PARAM_KEY: QUERY_ARTIST, PARAM_OFFSET: 0})'''
        '''add_folder_item(name="Track", parameters={PARAM_MODE: MODE_SEARCH, PARAM_KEY: QUERY_TRACK, PARAM_OFFSET: 0})'''
        xbmcplugin.endOfDirectory(handle=plugin_handle, succeeded=True)
    else:
        if query=='':
            query=get_query()
        if query!='':
            found=0
            if key==QUERY_CLOUDCAST:
                found=get_cloudcasts(SEARCH_URL+'?'+urllib.urlencode({u'q': query, u'type': key})+'&',offset)
            if found==limit:
                add_folder_item(name="More...", parameters={PARAM_MODE: MODE_SEARCH, PARAM_KEY: key, PARAM_QUERY: query, PARAM_OFFSET: offset+limit})
            xbmcplugin.endOfDirectory(handle=plugin_handle, succeeded=True)



def play_cloudcast(key):
    url=get_stream(key)
    if url:
        xbmcplugin.setResolvedUrl(handle=plugin_handle, succeeded=True, listitem=xbmcgui.ListItem(path=url))
    else:
        xbmcplugin.setResolvedUrl(handle=plugin_handle, succeeded=False, listitem=xbmcgui.ListItem())



def get_cloudcasts(url,offset):
    found=0
    url=url+'limit='+str(limit)+'&offset='+str(offset)
    print(url)
    h=urllib2.urlopen(url)
    content=h.read()
    json_content = json.loads(content)
    if QUERY_DATA in json_content and json_content[QUERY_DATA] :
        json_data = json_content[QUERY_DATA]
        json_tracknumber = offset
        for json_cloudcast in json_data :
            json_tracknumber = json_tracknumber + 1
            if QUERY_NAME in json_cloudcast and json_cloudcast[QUERY_NAME] :
                json_name = json_cloudcast[QUERY_NAME]
                json_key = ''
                json_year = 0
                json_date = ''
                json_length = 0
                json_username = ''
                json_image = ''
                json_comment = ''
                if QUERY_KEY in json_cloudcast and json_cloudcast[QUERY_KEY] :
                    json_key = json_cloudcast[QUERY_KEY]
                if QUERY_CREATED in json_cloudcast and json_cloudcast[QUERY_CREATED] :
                    json_created = json_cloudcast[QUERY_CREATED]
                    json_structtime = time.strptime(json_created[0:10],'%Y-%m-%d')
                    json_year = int(time.strftime('%Y',json_structtime))
                    json_date = time.strftime('%d/%m/Y',json_structtime)
                if QUERY_LENGTH in json_cloudcast and json_cloudcast[QUERY_LENGTH] :
                    json_length = json_cloudcast[QUERY_LENGTH]
                if QUERY_USER in json_cloudcast and json_cloudcast[QUERY_USER] :
                    json_user = json_cloudcast[QUERY_USER]
                    if QUERY_NAME in json_user and json_user[QUERY_NAME] :
                        json_username = json_user[QUERY_NAME]
                if QUERY_PICTURES in json_cloudcast and json_cloudcast[QUERY_PICTURES] :
                    json_pictures = json_cloudcast[QUERY_PICTURES]
                    if QUERY_LARGE in json_pictures and json_pictures[QUERY_LARGE] :
                        json_image = json_pictures[QUERY_LARGE]
                if QUERY_TAGS in json_cloudcast and json_cloudcast[QUERY_TAGS] :
                    json_tags = json_cloudcast[QUERY_TAGS]
                    for json_tag in json_tags:
                        if QUERY_NAME in json_tag and json_tag[QUERY_NAME] :
                            if json_comment != '':
                                json_comment=json_comment+'\n'
                            json_comment = json_comment+json_tag[QUERY_NAME]
                add_audio_item({'count': json_tracknumber, 'tracknumber': json_tracknumber, 'title': json_name, 'artist': json_username, 'duration': json_length, 'year': json_year, 'date': json_date, 'comment': json_comment},
                               parameters={PARAM_MODE: MODE_PLAY, PARAM_KEY: json_key},
                               img=json_image, thumbnail=json_image)
                found=found+1
    return found
    


def get_stream(cloudcast_key):
    casturl='http://www.mixcloud.com/api/1/cloudcast' + cloudcast_key[0:len(cloudcast_key)-1] + '.json?embed_type=cloudcast'
    print casturl
    h=urllib2.urlopen(casturl)
    contentcast=h.read()
    json_contentcast = json.loads(contentcast)
    if QUERY_AUDIOFORMATS in json_contentcast and json_contentcast[QUERY_AUDIOFORMATS] :
        json_audioformats = json_contentcast[QUERY_AUDIOFORMATS]
        if QUERY_MP3 in json_audioformats and json_audioformats[QUERY_MP3] :
            json_mp3 = json_audioformats[QUERY_MP3]
            for json_mp3url in json_mp3 :
                json_url=json_mp3url
                print json_url
                try:
                    conn=urllib2.urlopen(json_url)
                    print '200 OK'
                    conn.close
                except Exception, e:
                    print str(e)
                    json_url=''
                if json_url != '' :
                    return json_url
    return ''



def get_categories(url):
    h=urllib2.urlopen(url)
    content=h.read()
    json_content = json.loads(content)
    if QUERY_DATA in json_content and json_content[QUERY_DATA] :
        json_data = json_content[QUERY_DATA]
        for json_category in json_data :
            if QUERY_NAME in json_category and json_category[QUERY_NAME] :
                json_name = json_category[QUERY_NAME]
                json_key = ''
                json_format = ''
                json_thumbnail = ''
                if QUERY_KEY in json_category and json_category[QUERY_KEY] :
                    json_key = json_category[QUERY_KEY]
                if QUERY_FORMAT in json_category and json_category[QUERY_FORMAT] :
                    json_format = json_category[QUERY_FORMAT]
                if QUERY_PICTURES in json_category and json_category[QUERY_PICTURES] :
                    json_pictures = json_category[QUERY_PICTURES]
                    if QUERY_LARGE in json_pictures and json_pictures[QUERY_LARGE] :
                        json_thumbnail = json_pictures[QUERY_LARGE]
                add_folder_item(name=json_name, parameters={PARAM_MODE: MODE_CATEGORIES, PARAM_KEY: json_key}, img=json_thumbnail)



def get_query(query=''):
    keyboard = xbmc.Keyboard(query)
    query=''
    keyboard.doModal()
    if keyboard.isConfirmed():
        query = keyboard.getText()
    return query;
    


def parameters_string_to_dict(parameters):
    ''' Convert parameters encoded in a URL to a dict. '''
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict



params = parameters_string_to_dict(urllib.unquote(sys.argv[2]))
mode = int(params.get(PARAM_MODE, "0"))
offset = int(params.get(PARAM_OFFSET, "0"))
key = params.get(PARAM_KEY, "")
query = params.get(PARAM_QUERY, "")

print "##########################################################"
print("Mode: %s" % mode)
print("Offset: %s" % offset)
print("Key: %s" % key)
print("Query: %s" % query)
print "##########################################################"

if not sys.argv[ 2 ] or mode == MODE_HOME:
    ok = show_home_menu()
elif mode == MODE_HOT:
    ok = show_hot_menu(offset)
elif mode == MODE_NEW:
    ok = show_new_menu(offset)
elif mode == MODE_POPULAR:
    ok = show_popular_menu(offset)
elif mode == MODE_CATEGORIES:
    ok = show_categories_menu(key,offset)
elif mode == MODE_SEARCH:
    ok = show_search_menu(key,query,offset)
elif mode == MODE_PLAY:
    ok = play_cloudcast(key)
