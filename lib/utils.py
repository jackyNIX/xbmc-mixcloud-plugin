import os
import sys
import json
from datetime import datetime
from urllib import parse
import xbmc
import xbmcaddon
import xbmcplugin
import re



# static variables
__addon__ = xbmcaddon.Addon('plugin.audio.mixcloud')
debugenabled = (__addon__.getSetting('debug')=='true')



# logging functions
def log(message):
    if debugenabled:
        xbmc.log(msg = 'MIXCLOUD ' + message, level = xbmc.LOGNOTICE)



# icons
def getIcon(iconname):
    return xbmc.translatePath(os.path.join(__addon__.getAddonInfo('path'), 'resources', 'icons', iconname))



def getQuery(query = ''):
    keyboard = xbmc.Keyboard(query)
    keyboard.doModal()
    if keyboard.isConfirmed():
        query = keyboard.getText()
    else:
        query = ''
    return query 



def isValidURL(url):
    regex = re.compile(
            r'^(?:http|ftp)s?://' # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
            r'localhost|' #localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
            r'(?::\d+)?' # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None
    


# arguments
def encodeArguments(parameters):
    return sys.argv[0] + '?' + parse.urlencode(parameters)

def getArguments():
    paramDict = {}
    parameters = parse.unquote(sys.argv[2])
    if parameters:
        paramPairs = parameters[1:].split('&')
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if len(paramSplits) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict



def copyValue(sourcedata, sourcekey, targetdata, targetkey):
    if sourcekey in sourcedata and sourcedata[sourcekey]:
        targetdata[targetkey] = sourcedata[sourcekey]
        return True
    else:
        return False



# settings
def getSetting(name):
    return __addon__.getSetting(name)

def setSetting(name, value):
    __addon__.setSetting(name, value)