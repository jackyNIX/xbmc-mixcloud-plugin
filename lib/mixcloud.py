from urllib import parse, request
from .utils import log, copyValue, getSetting, setSetting, getQuery
from .base import BaseBuilder, BaseList, BaseListItem
from .lang import Lang
import json
import sys
import time
import xbmc
import xbmcgui 



STR_MIXCLOUD_API    = 'https://api.mixcloud.com'
STR_THUMB_SIZES     = {0 : 'small', 1 : 'thumbnail', 2 : 'medium', 3 : 'large', 4 : 'extra_large'}
STR_CLIENTID=       'Vef7HWkSjCzEFvdhet'
STR_CLIENTSECRET=   'VK7hwemnZWBexDbnVZqXLapVbPK3FFYT'
STR_USERAGENT=      'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0'
URL_REDIRECTURI=    'http://forum.kodi.tv/showthread.php?tid=116386'
URL_MIXCLOUD=       'https://www.mixcloud.com/'
URL_TOKEN=          'https://www.mixcloud.com/oauth/access_token'



class MixcloudInterface:

    def __init__(self):
        self.accessToken = getSetting('access_token')
        self.thumbSize = STR_THUMB_SIZES[int(getSetting('thumb_size'))]



    def getList(self, key = '', parameters = None):
        log('getList(key = ' + key + ', parameters = ' + str(parameters) + ')')
        mixcloudList = BaseList()
        try:
            url = STR_MIXCLOUD_API + key
            offset = 0
            listLimit = (1 + int(getSetting('page_limit'))) * 10
            if self.accessToken:
                if parameters:
                    parameters['access_token'] = self.accessToken
                else:
                    parameters = {'access_token' : self.accessToken}
            if parameters:
                parameters['limit'] = listLimit
                if 'offset' in parameters and parameters['offset']:
                    offset = parameters['offset']
            else:
                parameters = {'limit' : listLimit}
            if parameters and len(parameters) > 0:
                url = url + '?' + parse.urlencode(parameters)
            log('getList(' + url + ')')
            response = json.loads(request.urlopen(url).read())
            if 'data' in response and response['data'] :
                data = response['data']
                for item in data:
                    if (getSetting('ext_info') == 'true') and (listLimit == 10) and ('key' in item) and (item['key']):
                        mixcloudList.items.append(self.getCloudcast(item['key'], {}))
                    else:
                        mixcloudList.items.append(self.toListItem(item))
            if 'paging' in response and response['paging']:
                paging = response['paging']
                if 'next' in paging and paging['next']:
                    mixcloudList.nextOffset = offset + listLimit
            mixcloudList.initTrackNumbers(offset)
        except Exception as e:
            log('getList failed error: ' + str(e))
        return mixcloudList



    def getCloudcasts(self, keylist, parameters = {}):
        mixcloudList = BaseList()
        try:
            offset = 0
            listLimit = (1 + int(getSetting('page_limit'))) * 10
            index = 0
            if parameters and 'offset' in parameters and parameters['offset']:
                offset = parameters['offset']
            for keyitem in keylist:
                if index >= offset:
                    if index < offset + listLimit:
                        mixcloudListItem = self.getCloudcast(keyitem['key'], {})
                        if mixcloudListItem:
                            mixcloudListItem.setTimestamp(keyitem, 'timestamp')
                            mixcloudList.items.append(mixcloudListItem)
                        else:
                            index -= 1
                    else:
                        break
                index += 1
            if index < len(keylist):
                mixcloudList.nextOffset = index
            mixcloudList.initTrackNumbers(offset)
        except:
            log('Get cloudcasts failed error: %s' % (sys.exc_info()[1]))
        return mixcloudList



    def getCloudcast(self, key, parameters = {}):
        try:
            url = STR_MIXCLOUD_API + key
            if self.accessToken:
                if parameters:
                    parameters['access_token'] = self.accessToken
                else:
                    parameters = {'access_token' : self.accessToken}
            if parameters and (len(parameters) > 0):
                url = url + '?' + parse.urlencode(parameters)
            log('getCloudcast(' + url + ')')
            response = json.loads(request.urlopen(url).read())
            return self.toListItem(response)
        except:
            log('Get cloudcast failed error: %s' % (sys.exc_info()[1]))
            return None



    def toListItem(self, data):
        mixcloudListItem = BaseListItem()
        if mixcloudListItem.setKey(data, 'key'):
            copyValue(data, 'name', mixcloudListItem.infolabels, 'title')
            if 'created_time' in data and data['created_time']:
                created = data['created_time']
                structtime = time.strptime(created[0 : 10], '%Y-%m-%d')
                mixcloudListItem.infolabels['year'] = int(time.strftime('%Y', structtime))
                mixcloudListItem.infolabels['date'] = time.strftime('%d.%m.%Y', structtime)
            copyValue(data, 'audio_length', mixcloudListItem.infolabels, 'duration')
            if 'user' in data and data['user']:
                user = data['user']
                mixcloudListItem.setUser(user, 'key')
                if not ('is_current_user' in user and user['is_current_user']):
                    mixcloudListItem.setFollowing(user, 'following')
                copyValue(user, 'name', mixcloudListItem.infolabels, 'artist')
            else:
                if not ('is_current_user' in data and data['is_current_user']):
                    mixcloudListItem.setFollowing(data, 'following')
            if 'pictures' in data and data['pictures']:
                pictures = data['pictures']
                mixcloudListItem.setImage(pictures, self.thumbSize)
            copyValue(data, 'description', mixcloudListItem.infolabels, 'comment')
            if 'tags' in data and data['tags']:
                tags = data['tags']
                genres = ''
                for tag in tags:
                    if 'name' in tag and tag['name']:
                        genres = genres + tag['name'] + ' '
                if genres:
                    mixcloudListItem.infolabels['genre'] = genres.strip()
            mixcloudListItem.setTimestamp(data, 'listen_time')
            mixcloudListItem.setFavorited(data, 'favorited')
            mixcloudListItem.setListenLater(data, 'is_listen_later')
        log('toListItem(): ' + str(mixcloudListItem))
        return mixcloudListItem



    def profileLogout(self):
        if xbmcgui.Dialog().yesno('Mixcloud', Lang.ASK_PROFILE_LOGOUT):
            self.accessToken = ''
            # setSetting('oath_code', '')   
            setSetting('access_token', '')



    def profileLoggedIn(self):
        return self.accessToken != ''



    def profileLogin(self):
        # ask for code if no token provided yet
        if not self.accessToken:
            log('No access token found')
            ask = True
            oathCode = getSetting('oath_code')
            while ask:
                ask = xbmcgui.Dialog().yesno('Mixcloud', Lang.TOKEN_ERROR, Lang.ENTER_OATH_CODE)
                if ask:
                    oathCode = getQuery(oathCode)
                    setSetting('oath_code', oathCode)
                    setSetting('access_token', '')
                    if oathCode != '':
                        try:
                            values = {
                                'client_id' : STR_CLIENTID,
                                'redirect_uri' : URL_REDIRECTURI,
                                'client_secret' : STR_CLIENTSECRET,
                                'code' : oathCode
                            }
                            headers = {
                                'User-Agent' : STR_USERAGENT,
                                'Referer' : URL_MIXCLOUD
                            }
                            postdata = parse.urlencode(values).encode('utf-8')
                            req = request.Request(URL_TOKEN, postdata, headers, URL_MIXCLOUD)
                            response = json.loads(request.urlopen(req).read().decode('utf-8'))
                            if 'access_token' in response and response['access_token'] :
                                log('Access_token received')
                                self.accessToken = response['access_token']
                                setSetting('access_token', self.accessToken)
                            else:
                                log('No access_token received')
                                log(str(response))
                        except:
                            log('oath_code failed error=%s' % (sys.exc_info()[1]))

                    ask=((oathCode!='') and (self.accessToken==''))

        return self.accessToken != ''

    def profileAction(self, action, key):
        log('profile action: ' + action + ' key: ' + key)
        url = STR_MIXCLOUD_API + key + '?' + parse.urlencode({'access_token' : self.accessToken})
        log('url: ' + url)
        req = request.Request(url, data = 'none'.encode('utf-8'))
        req.get_method = lambda: action
        response = request.urlopen(req).read().decode('utf-8')
        data = json.loads(response)
        info=''
        if 'result' in data and data['result']:
            result = data['result']
            if 'message' in result and result['message']:
                info = result['message']
                if not(('success' in result) and (result['success'] == True)):
                    info = info + '\n\nFAILED!'
        if info == '':
            log(str(data))
            info = 'Unknown error occured.\n\n' + str(data)
        xbmcgui.Dialog().ok('Mixcloud', info)