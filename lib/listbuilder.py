# -*- coding: utf-8 -*-

'''
@author: jackyNIX

Copyright (C) 2011-2020 jackyNIX

This file is part of KODI MixCloud Plugin.

KODI MixCloud Plugin is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

KODI MixCloud Plugin is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with KODI MixCloud Plugin.  If not, see <http://www.gnu.org/licenses/>.
'''



import sys
import xbmc
import xbmcgui
import xbmcplugin
from datetime import datetime
from .mixcloud import MixcloudInterface
from .utils import log, encodeArguments, getIcon, getArguments
from .history import History
from .resolver import ResolverBuilder
from .base import BaseBuilder, BaseListBuilder, QueryListBuilder, BaseList
from .lang import Lang



# main menu
class MainBuilder(BaseListBuilder):

    def buildItems(self):
        log('MainBuilder.buildItems()')
        if MixcloudInterface().profileLoggedIn():
            self.addFolderItem({'title' : Lang.FOLLOWINGS}, {'mode' : 'playlists', 'key' : '/me/following/'}, getIcon('nav/kodi_highlight.png'))
            self.addFolderItem({'title' : Lang.FOLLOWERS}, {'mode' : 'playlists', 'key' : '/me/followers/'}, getIcon('nav/kodi_highlight.png'))
            self.addFolderItem({'title' : Lang.FAVORITES}, {'mode' : 'cloudcasts', 'key' : '/me/favorites/'}, getIcon('nav/kodi_favorites.png'))
            self.addFolderItem({'title' : Lang.UPLOADS}, {'mode' : 'cloudcasts', 'key' : '/me/cloudcasts/'}, getIcon('nav/kodi_uploads.png'))
            self.addFolderItem({'title' : Lang.PLAYLISTS}, {'mode' : 'playlists', 'key' : '/me/playlists/'}, getIcon('nav/kodi_playlists.png'))
            self.addFolderItem({'title' : Lang.LISTEN_LATER}, {'mode' : 'cloudcasts', 'key' : '/me/listen-later/'}, getIcon('nav/kodi_listenlater.png'))
        else:
            self.addFolderItem({'title' : Lang.PROFILE}, {'mode' : 'profile', 'key' : 'login'}, getIcon('nav/kodi_profile.png'))
        self.addFolderItem({'title' : Lang.CATEGORIES}, {'mode' : 'playlists', 'key' : '/categories/'}, getIcon('nav/kodi_categories.png'))
        self.addFolderItem({'title' : Lang.HISTORY}, {'mode' : 'playhistory', 'offset' : 0, 'offsetex' : 0}, getIcon('nav/kodi_history.png'))
        self.addFolderItem({'title' : Lang.SEARCH}, {'mode' : 'search'}, getIcon('nav/kodi_search.png'))
        return 0



# cloudcasts menu
class CloudcastsBuilder(BaseListBuilder):

    def buildItems(self):
        log('CloudcastsBuilder.buildItems()')
        xbmcplugin.setContent(self.plugin_handle, 'songs')
        cloudcasts = MixcloudInterface().getList(self.key, {'offset' : self.offset})
        for cloudcast in cloudcasts.items:
            contextMenuItems = self.buildContextMenuItems(cloudcast)
            self.addAudioItem(cloudcast.infolabels, {'mode' : 'resolve', 'key' : cloudcast.key, 'user' : cloudcast.user}, cloudcast.image, contextMenuItems, len(cloudcasts.items))
        return cloudcasts.nextOffset



# playlists menu
class PlaylistsBuilder(BaseListBuilder):

    def buildItems(self):
        log('PlaylistsBuilder.buildItems()')
        playlists = MixcloudInterface().getList(self.key, {'offset' : self.offset})
        for playlist in playlists.items:
            if playlist.image:
                image = playlist.image
            elif self.key == '/categories/':
                image = getIcon('nav/kodi_categories.png')
            elif self.key == '/me/playlists/':
                image = getIcon('nav/kodi_playlists.png')
            else:
                image = ''
            contextMenuItems = self.buildContextMenuItems(playlist)
            self.addFolderItem(playlist.infolabels, {'mode' : 'cloudcasts', 'key' : playlist.key + 'cloudcasts/'}, image, contextMenuItems)
        return playlists.nextOffset
    


# simple play history menu (without profile listens)
class SimplePlayHistoryBuilder(BaseListBuilder):

    def buildItems(self):
        log('SimplePlayHistoryBuilder.buildItems()')
        xbmcplugin.setContent(self.plugin_handle, 'songs')
        playHistory = History('play_history')
        if playHistory:
            cloudcasts = MixcloudInterface().getCloudcasts(playHistory.data, {'offset' : self.offset})
            for cloudcast in cloudcasts.items:
                contextMenuItems = self.buildContextMenuItems(cloudcast)
                self.addAudioItem(cloudcast.infolabels, {'mode' : 'resolve', 'key' : cloudcast.key, 'user' : cloudcast.user}, cloudcast.image, contextMenuItems, len(cloudcasts.items))
            return cloudcasts.nextOffset
        else:
            return 0



# play history menu (with profile listens)
class PlayHistoryBuilder(BaseListBuilder):

    def buildItems(self):
        log('PlayHistoryBuilder.buildItems()')
        xbmcplugin.setContent(self.plugin_handle, 'songs')

        cloudcasts = []
        playHistory = History('play_history')
        if playHistory:
            cloudcasts.append(MixcloudInterface().getCloudcasts(playHistory.data, {'offset' : self.offset[0]}))
        else:
            cloudcasts.append(BaseList())
        if MixcloudInterface().profileLoggedIn():
            cloudcasts.append(MixcloudInterface().getList('/me/listens/', {'offset' : self.offset[1]}))
        else:
            cloudcasts.append(BaseList())

        mergedCloudcasts = BaseList()
        mergedCloudcasts.merge(cloudcasts)
        mergedCloudcasts.initTrackNumbers(self.offset[0] + self.offset[1])
        if (cloudcasts[0].nextOffset + cloudcasts[1].nextOffset) > 0:
            mergedCloudcasts.nextOffset[0] = self.offset[0] + mergedCloudcasts.nextOffset[0]
            mergedCloudcasts.nextOffset[1] = self.offset[1] + mergedCloudcasts.nextOffset[1]
        else:
            mergedCloudcasts.nextOffset = [0, 0]

        for cloudcast in mergedCloudcasts.items:
            contextMenuItems = self.buildContextMenuItems(cloudcast)
            self.addAudioItem(cloudcast.infolabels, {'mode' : 'resolve', 'key' : cloudcast.key, 'user' : cloudcast.user}, cloudcast.image, contextMenuItems, len(mergedCloudcasts.items))

        return mergedCloudcasts.nextOffset



# search menu
class SearchBuilder(BaseListBuilder):

    def buildItems(self):
        self.addFolderItem({'title' : Lang.SEARCH_FOR_CLOUDCASTS}, {'mode' : 'searchcloudcast'}, getIcon('nav/kodi_search.png'))
        self.addFolderItem({'title' : Lang.SEARCH_FOR_USERS}, {'mode' : 'searchuser'}, getIcon('nav/kodi_search.png'))
        searchHistory = History('search_history')
        if searchHistory:
            index = 0
            for keyitem in searchHistory.data:
                index += 1
                if index > self.offset:
                    if index <= self.offset + 10:
                        if keyitem['key'] == 'cloudcast':
                            self.addFolderItem({'title' : keyitem['value']}, {'mode' : 'searchcloudcast', 'key' : keyitem['value']}, getIcon('nav/kodi_playlists.png'))
                        elif keyitem['key'] == 'user':
                            self.addFolderItem({'title' : keyitem['value']}, {'mode' : 'searchuser', 'key' : keyitem['value']}, getIcon('nav/kodi_profile.png'))
                    else:
                        break
            if index < len(searchHistory.data):
                return index
        return 0



# search cloudcast menu
class SearchCloudcastBuilder(QueryListBuilder):

    def buildQueryItems(self, query):
        xbmcplugin.setContent(self.plugin_handle, 'songs')
        cloudcasts = MixcloudInterface().getList('/search/', {'q' : query, 'type' : 'cloudcast', 'offset' : self.offset})
        for cloudcast in cloudcasts.items:
            contextMenuItems = self.buildContextMenuItems(cloudcast)
            self.addAudioItem(cloudcast.infolabels, {'mode' : 'resolve', 'key' : cloudcast.key, 'user' : cloudcast.user}, cloudcast.image, contextMenuItems, len(cloudcasts.items))
        if not self.key:
            searchHistory = History('search_history')
            if searchHistory:
                searchHistory.add({'key' : 'cloudcast', 'value' : query})
        return cloudcasts.nextOffset



# search user menu
class SearchUserBuilder(QueryListBuilder):

    def buildQueryItems(self, query):
        users = MixcloudInterface().getList('/search/', {'q' : query, 'type' : 'user', 'offset' : self.offset})
        for user in users.items:
            contextMenuItems = self.buildContextMenuItems(user)
            self.addFolderItem(user.infolabels, {'mode' : 'cloudcasts', 'key' : user.key + 'cloudcasts/'}, user.image, contextMenuItems)
        if not self.key:
            searchHistory = History('search_history')
            if searchHistory:
                searchHistory.add({'key' : 'user', 'value' : query})
        return users.nextOffset



# mixcloud profile builder
class MixcloudProfileBuilder(BaseBuilder):

    def build(self):
        if (self.key == 'login') and (MixcloudInterface().profileLogin()):
            return MainBuilder().build()
        elif self.key == 'logout':
            MixcloudInterface().profileLogout()
            xbmc.executebuiltin('Container.Refresh')
        else:
            return False



# mixcloud post or delete builder
class MixcloudProfileActionBuilder(BaseBuilder):

    def build(self):
        MixcloudInterface().profileAction(self.mode.upper(), self.key)
        xbmc.executebuiltin('Container.Refresh')



# mixcloud post or delete builder
class ClearHistoryBuilder(BaseBuilder):

    def build(self):
        if xbmcgui.Dialog().yesno('Mixcloud', Lang.ASK_CLEAR_HISTORY):
            playHistory = History('play_history')
            playHistory.clear()
            playHistory.writeFile()

            searchHistory = History('search_history')
            searchHistory.clear()
            searchHistory.writeFile()

        xbmc.executebuiltin('Container.Refresh')



# mode/class switches
BUILDERS = {
    '' : MainBuilder,
    'cloudcasts' : CloudcastsBuilder,
    'playlists' : PlaylistsBuilder,
    'simpleplayhistory' : SimplePlayHistoryBuilder,
    'playhistory' : PlayHistoryBuilder,
    'search' : SearchBuilder,
    'searchcloudcast' : SearchCloudcastBuilder,
    'searchuser' : SearchUserBuilder,
    'resolve' : ResolverBuilder,
    'profile' : MixcloudProfileBuilder,
    'post' : MixcloudProfileActionBuilder,
    'delete' : MixcloudProfileActionBuilder,
    'history' : ClearHistoryBuilder
}

# main entry
def run():
    starttime = datetime.now()
    log('##############################################################################################################################')
    plugin_args = getArguments()
    log('args: ' + str(plugin_args))
    BUILDERS.get(plugin_args.get('mode', ''), MainBuilder)().execute()
    elapsedtime = datetime.now() - starttime
    log('executed in ' + str(elapsedtime.seconds) + '.' + str(elapsedtime.microseconds) + ' seconds')