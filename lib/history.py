import os
import sys
import json
from datetime import datetime
import xbmc
import xbmcaddon
from .utils import log 



# statics
__addon__ = xbmcaddon.Addon('plugin.audio.mixcloud')



class History:

    def __init__(self, name):
        self.name = name
        self.data = []
        self.readFile()

    def readFile(self):
        starttime = datetime.now()
        self.data = []
        filepath = xbmc.translatePath(__addon__.getAddonInfo('profile')) + self.name + '.json'
        log('reading json file: ' + filepath)
        try:
            # read file
            if os.path.exists(filepath):
                text_file = open(filepath, 'r')
                self.data = json.loads(text_file.read())
                text_file.close()
                self.trim()
            elif __addon__.getSetting(self.name+'_list'):
                # convert old 2.4.x settings
                list_data = __addon__.getSetting(self.name + '_list').split(', ')
                for list_entry in list_data:
                    json_entry = {}
                    list_fields = list_entry.split('=')
                    for list_field in list_fields:
                        if len(json_entry) == 0:
                            json_entry['key'] = list_field
                        elif len(json_entry) == 1:
                            json_entry['value'] = list_field
                    self.data.append(json_entry)
                    self.trim()
                log('convert old 2.4.x settings: ' + self.name + ' -> ' + json.dumps(self.data))
                self.writeFile()
                __addon__.setSetting(self.name + '_list', None)

        except Exception as e:
            log('unable to read json file: ' + filepath)
            log(str(e))
        elapsedtime = datetime.now() - starttime
        log('read ' + str(len(self.data)) + ' items in ' + str(elapsedtime.seconds) + '.' + str(elapsedtime.microseconds) + ' seconds')
        return self.data
        
    def writeFile(self):
        filepath = xbmc.translatePath(__addon__.getAddonInfo('profile')) + self.name + '.json'
        try:
            text_file = open(filepath, 'w+')
            text_file.write(json.dumps(self.data, indent = 4 * ' '))
            text_file.close()
        except Exception as e:
            log('unable to write json file: ' + filepath)
            log(str(e))

    # add data and write file
    def add(self, json_entry = {}):
        try:
            json_entry['timestamp'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            self.data.insert(0, json_entry)
            self.trim()
            self.writeFile()
        except Exception as e:
            log('unable to add to json: ' + str(e))

    # limit list
    def trim(self):
        json_max = 1
        if __addon__.getSetting(self.name + '_max'):
            json_max = (1 + int(__addon__.getSetting(self.name + '_max'))) * 100
        while len(self.data) > json_max:
            self.data.pop()

    # clear list
    def clear(self):
        log('clear json sfile')
        self.data = []