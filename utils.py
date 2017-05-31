#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class UserSettings:
    def __init__(self, user_info, location=None, lang='en'):
        self.info = user_info
        self.location = location
        self.lang = lang
        self.notification = {}

    def set_location(self, location):
        self.location = location

    def set_notification(self, time):
        self.notification.update(time)

    def set_lang(self, lang):
        self.lang = lang
