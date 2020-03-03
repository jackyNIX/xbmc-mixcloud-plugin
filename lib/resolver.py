from .utils import log, encodeArguments, getIcon, getArguments, getSetting, setSetting, isValidURL
from .history import History
from .mixcloud import MixcloudInterface
from .base import BaseBuilder
from urllib import request, parse
import xbmc
import xbmcgui
import xbmcplugin
import re
import sys
import json
import base64
from itertools import cycle



STR_USERAGENT=      'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0'



class BaseResolver:

    def __init__(self, key):
        self.key = key

    def resolve(self):
        return ''



class MixcloudResolver(BaseResolver):

    def resolve(self):
        url = None
        ck = 'https://www.mixcloud.com' + self.key
        log('resolving cloudcast stream via mixcloud: ' + ck)

        try:
            headers = {
                    'User-Agent' : STR_USERAGENT,
                    'Referer' : 'https://www.mixcloud.com/'
                    }
            req = request.Request(ck, headers = headers, origin_req_host = 'https://www.mixcloud.com/')
            response = request.urlopen(req).read().decode('utf-8').replace('&quot;','"')
            match = re.search(r'<script id="relay-data" type="text/x-mixcloud">\[(.*)', response, re.MULTILINE)
            if match:
                match = re.search(r'(.*)\]</script>', match.group(1), re.MULTILINE)
                if match:
                    decoded = '[' + match.group(1) + ']'
                    content = json.loads(decoded)
                    isexclusive = False
                    for item in content:
                        if 'cloudcastLookup' in item and item['cloudcastLookup']:
                            cloudcastLookupA = item['cloudcastLookup']
                            if 'data' in cloudcastLookupA and cloudcastLookupA['data']:
                                data = cloudcastLookupA['data']
                                if 'cloudcastLookup' in data and data['cloudcastLookup']:
                                    cloudcastLookupB = data['cloudcastLookup']
                                    if 'isExclusive' in cloudcastLookupB and cloudcastLookupB['isExclusive']:
                                        isexclusive = cloudcastLookupB['isExclusive']
                                    if 'streamInfo' in cloudcastLookupB and cloudcastLookupB['streamInfo']:
                                        streaminfo = cloudcastLookupB['streamInfo']
                                        if 'url' in streaminfo and streaminfo['url']:
                                            url = streaminfo['url']
                                        elif 'hlsUrl' in streaminfo and streaminfo['hlsUrl']:
                                            url = streaminfo['hlsUrl']
                                        elif 'dashUrl' in streaminfo and streaminfo['dashUrl']:
                                            url = streaminfo['dashUrl']
                        if url:
                            break

                    if url:
                        decoded_url = base64.b64decode(url).decode('utf-8')
                        url = ''.join(chr(ord(a) ^ ord(b)) for a, b in zip(decoded_url, cycle('IFYOUWANTTHEARTISTSTOGETPAIDDONOTDOWNLOADFROMMIXCLOUD')))
                        log('url found: '+url)
                        if not isValidURL(url):
                            log('invalid url')
                            url = None
                    elif isexclusive:
                        log('Cloudcast is exclusive')
                    else:
                        log('Unable to find url in json')
                else:
                    log('Unable to resolve (match 2)')
            else:
                log('Unable to resolve (match 1)')
        except Exception as e:
            log('Unable to resolve: ' + str(e))
        return url



class MixcloudDownloaderResolver(BaseResolver):

    def resolve(self):
        url = None
        ck = 'https://www.mixcloud.com' + self.key
        log('resolving cloudcast stream via mixcloud-downloader: ' + ck)

        try:
            headers = {
                'User-Agent' : STR_USERAGENT,
                'Referer' : 'https://www.mixcloud-downloader.com/'
            }

            values = {
                'url' : ck,
            }
            postdata = parse.urlencode(values).encode('utf-8')
            req = request.Request('https://www.mixcloud-downloader.com/download/', postdata, headers, 'https://www.mixcloud-downloader.com/')
            response = request.urlopen(req)
            data = response.read().decode('utf-8')

            # first attempt
            match = re.search(r'a class="btn btn-secondary btn-sm"(.*)', data, re.DOTALL)
            if match:
                match=re.search(r'href="(.*)"', match.group(1))
                if match:
                    url = match.group(1)
                    log('url found (1): ' + url)
                    if not isValidURL(url):
                        log('invalid url')
                        url = None
                else:
                    log('Wrong response code (1)=%s len=%s' % (response.getcode(), len(data)))

            # second attempt
            if not url:
                match = re.search(r'URL from Mixcloud: <br /> <a href="(.*)"', data)
                if match:
                    url = match.group(1)
                    log('url found (2): ' + url)
                    if not isValidURL(url):
                        log('invalid url')
                        url = None
                else:
                    log('Wrong response code (2)=%s len=%s' % (response.getcode(), len(data)))
        except Exception as e:
            log('Unable to resolve: ' + str(e))
        return url



class OfflibertyResolver(BaseResolver):

    def resolve(self):
        url = None
        ck = 'https://www.mixcloud.com' + self.key

        for retry in range(1, 2):
            log('resolving cloudcast stream via offliberty (' + str(retry) + '): ' + ck)

            try:
                values = {
                    'track' : ck,
                    'refext' : 'https://www.google.com/'
                }
                headers = {
                    'User-Agent' : STR_USERAGENT,
                    'Referer' : 'http://offliberty.com/'
                }
                postdata = parse.urlencode(values).encode('utf-8')
                req = request.Request('http://offliberty.com/off04.php', postdata, headers, 'http://offliberty.com/')
                response = request.urlopen(req)
                data = response.read().decode('utf-8')
                match = re.search(r'href="(.*)" class="download"', data)
                if match:
                    url = match.group(1)
                    log('url found: ' + url)
                    if not isValidURL(url):
                        log('invalid url')
                        url = None
                else:
                    log('Wrong response try=%s code=%s len=%s, trying again...' % (retry, response.getcode(), len(data)))
            except:
                log('Unexpected error try=%s error=%s, trying again...' % (retry, sys.exc_info()[0]))
        return url



class ResolverBuilder(BaseBuilder):

    def execute(self):
        log('ResolverBuilder.execute()')
        url = self.getStream()
        if url:
            mixcloudListItem = MixcloudInterface().getCloudcast(self.key, {})
            if mixcloudListItem:
                listitem = xbmcgui.ListItem(label = mixcloudListItem.infolabels['title'], label2 = mixcloudListItem.infolabels['artist'], path = url)
                listitem.setInfo('music', mixcloudListItem.infolabels)
                xbmcplugin.setResolvedUrl(handle = self.plugin_handle, succeeded = True, listitem = listitem)
                History('play_history').add({'key' : self.key})
                log('Playing: ' + url)
                return
        log('Stop player')
        xbmcplugin.setResolvedUrl(handle = self.plugin_handle, succeeded = False, listitem = xbmcgui.ListItem())

    def getStream(self):
        log('ResolverBuilder.getStream()')

        strm_url = None

        # resolvers
        activeResolvers = []
        if getSetting('resolver_mixcloud') == 'true':
            activeResolvers.append(MixcloudResolver)
        if getSetting('resolver_mixclouddownloader') == 'true':
            activeResolvers.append(MixcloudDownloaderResolver)
        if getSetting('resolver_offliberty') == 'true':
            activeResolvers.append(OfflibertyResolver)
        log('active resolvers: ' + str(activeResolvers))

        for resolver in activeResolvers:
            strm_url = resolver(self.key).resolve()

            # stream found!
            if strm_url:
                break

            # user aborted
            if xbmc.Monitor().abortRequested():
                break
                
        return strm_url