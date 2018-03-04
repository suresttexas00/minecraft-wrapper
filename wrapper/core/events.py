# -*- coding: utf-8 -*-

# Copyright (C) 2016, 2017 - BenBaptist and Wrapper.py developer(s).
# https://github.com/benbaptist/minecraft-wrapper
# This program is distributed under the terms of the GNU
# General Public License, version 3 or later.

import threading


class Events(object):

    def __init__(self, wrapper):
        self.wrapper = wrapper
        self.log = wrapper.log
        self.listeners = []
        self.events = {}

    def __getitem__(self, index):
        if not type(index) == str:
            raise Exception("A string must be passed - got %s" % type(index))
        return self.events[index]

    def __setitem__(self, index, value):
        if not type(index) == str:
            raise Exception("A string must be passed - got %s" % type(index))
        self.events[index] = value
        return self.events[index]

    def __delitem__(self, index):
        if not type(index) == str:
            raise Exception("A string must be passed - got %s" % type(index))
        del self.events[index]

    def __iter__(self):
        for i in self.events:
            yield i

    def callevent(self, event, payload, abortable=True):
        """
        This needs some standardization
        :param event: String name event

        :param payload:  Should have these items.
            :playername: Optional string playername
            :player: Player Object - Optional, unless playername is provided

        :param abortable: Callevent must wait for plugins to complete.

        :return:

        """

        if event == "player.runCommand":
            abortable = False

        # Event processor thread

        if abortable:
            return self._callevent(event, payload)
        else:
            t = threading.Thread(target=self._callevent,
                                 name="EventProcessor", args=(event, payload))
            t.daemon = True
            t.start()
            return

    def _callevent(self, event, payload):
        if event == "player.runCommand":
            self.wrapper.commands.playercommand(payload)
            return

        # create reference player object for payload, if needed.
        if payload and ("playername" in payload) and ("player" not in payload):
            payload["player"] = self.wrapper.api.minecraft.getPlayer(
                payload["playername"])

        # listeners is normally empty.
        # Supposed to be part of the blockForEvent code.
        for sock in self.listeners:
            sock.append({"event": event, "payload": payload})

        payload_status = True
        # old_payload = payload  # retaining the original payload might be helpful for the future features.  # noqa

        # in all plugins with this event listed..
        for plugin_id in self.events:

            # for each plugin...
            if event in self.events[plugin_id]:

                # run the plugin code and get the plugin's return value
                result = None
                try:
                    # 'self.events[plugin_id][event]' is the
                    # <bound method Main.plugin_event_function>
                    # pass 'payload' as the argument for the plugin-defined
                    # event code function
                    result = self.events[plugin_id][event](payload)
                except Exception as e:
                    self.log.exception(
                        "Plugin '%s' \n"
                        "experienced an exception calling '%s': \n%s",
                        plugin_id, event, e
                    )

                # Evaluate this plugin's result
                # Every plugin will be given equal time to run it's event code.
                # However, if one plugin returns a False, no payload changes
                #  will be possible.
                #
                if result in (None, True):  # Don't change the payload status
                    pass
                elif result is False:  # mark this event permanently as False
                    payload_status = False
                else:
                    # A payload is being returned
                    # If any plugin rejects the event, no payload changes
                    #  will be authorized.
                    if payload_status is not False:
                        # the next plugin looking at this event sees the
                        #  new payload.
                        if type(result) == dict:
                            payload, payload_status = result
                        else:
                            # non dictionary payloads are deprecated and will
                            # be overridden by dict payloads
                            # Dict payloads are those that return the
                            # payload in the same format as it was passed.
                            payload_status = result
        return payload_status
