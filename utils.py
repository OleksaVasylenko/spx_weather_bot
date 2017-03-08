class UserSettings:
    def __init__(self, user_info, location=None, lang='en', notify=None):
        self.info = user_info
        self.location = location
        self.lang = lang
        self.notify = []

    def set_location(self, location):
        self.location = location

    def set_notify(self, time):
        self.notify.append(time)

    def set_lang(self, lang):
        self.lang = lang
