# -*- coding: utf-8 -*-

# Copyright (C) 2016, 2017 - BenBaptist and minecraft-wrapper (AKA 'Wrapper.py')
#  developer(s).
# https://github.com/benbaptist/minecraft-wrapper
# This program is distributed under the terms of the GNU General Public License,
#  version 3 or later.

# from __future__ import unicode_literals

import os
import sys
import time
import logging
from api.helpers import mkdir_p, putjsonfile, getjsonfile
from core.config import Config
import threading

version = sys.version_info
PY3 = version[0] > 2

if PY3:
    str2 = str
    # noinspection PyUnresolvedReferences
    import pickle as Pickle
else:
    # noinspection PyUnresolvedReferences
    str2 = unicode
    # noinspection PyUnresolvedReferences
    import cPickle as Pickle


class Storage:

    def __init__(self, name, root="wrapper-data/json", encoding="default", pickle=True):
        self.Data = {}
        self.name = name
        self.root = root
        self.pickle = pickle
        self.configManager = Config()
        self.configManager.loadconfig()
        self.log = logging.getLogger('Storage.py')

        if encoding == "default":
            self.encoding = self.configManager.config["General"]["encoding"]
        else:
            self.encoding = encoding

        if self.pickle:
            self.file_ext = "pkl"
        else:
            self.file_ext = "json"

        self.load()
        self.timer = time.time()
        self.abort = False

        t = threading.Thread(target=self.periodicsave, args=())
        t.daemon = True
        t.start()

    def periodicsave(self):
        # doing it this way (versus just sleeping for 60 seconds), allows faster shutdown response
        while not self.abort:
            if time.time() - self.timer > 60:
                self.save()
                self.timer = time.time()
            time.sleep(1)

    def load(self):
        mkdir_p(self.root)
        if not os.path.exists("%s/%s.%s" % (self.root, self.name, self.file_ext)):
            # load old json storages if there is no pickled file (and if storage is using pickle)
            if self.pickle:
                self.Data = self.json_load()
            self.save()  # save to the selected file mode (json or pkl)
        if self.pickle:
            self.pickle_load()
        else:
            self.json_load()

    def save(self):
        if not os.path.exists(self.root):
            mkdir_p(self.root)
        if self.pickle:
            self.pickle_save()
        else:
            self.json_save()

    def pickle_save(self):
        if "human" in self.encoding.lower():
            _protocol = 0
        else:
            _protocol = Pickle.HIGHEST_PROTOCOL

        with open("%s/%s.%s" % (self.root, self.name, self.file_ext), "wb") as f:
            Pickle.dump(self.Data, f, protocol=_protocol)

    def json_save(self):
        putcode = putjsonfile(self.Data, self.name, self.root)
        if not putcode:
            self.log.exception("Error encoutered while saving json data:\n"
                               "'%s/%s.%s'\nData Dump:\ns",
                               self.root, self.name, self.file_ext, self.Data)

    def pickle_load(self):
        with open("%s/%s.%s" % (self.root, self.name, self.file_ext), "rb") as f:
            return Pickle.load(f)

    def json_load(self):
        try_load = getjsonfile(self.name, self.root, encodedas=self.encoding)
        if try_load in (None, False):
            self.log.exception("bad/non-existent file or data '%s/%s.%s'", self.root, self.name, self.file_ext)
            return {}
        else:
            return try_load

    def close(self):
        self.abort = True
        self.save()
