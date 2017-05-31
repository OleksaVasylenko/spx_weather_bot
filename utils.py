<<<<<<< HEAD
#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class UserSettings:
    def __init__(self, user_info, location=None, lang='en'):
        self.info = user_info
        self.location = location
        self.lang = lang
        self.notification = {}
=======
class UserSettings:
    def __init__(self, user_info, location=None, lang='en', notify=None):
        self.info = user_info
        self.location = location
        self.lang = lang
        self.notify = []
>>>>>>> 280e58f1e2796ffd182a24c89a0117eae85f5e08

    def set_location(self, location):
        self.location = location

<<<<<<< HEAD
    def set_notification(self, time):
        self.notification.update(time)
=======
    def set_notify(self, time):
        self.notify.append(time)
>>>>>>> 280e58f1e2796ffd182a24c89a0117eae85f5e08

    def set_lang(self, lang):
        self.lang = lang
