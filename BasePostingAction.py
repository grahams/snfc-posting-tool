from Newsletter import Newsletter

class BasePostingAction:
    pluginName = "Base Class"
    configSection = "basePostingAction"
    config = None

    def execute(self, config, nl):
        print "This should do something profound\n\n"

        print nl.generateHTML()

    def readConfigValue(self, key):
        section = self.config.getElementsByTagName(self.configSection)[0]

        value = section.getElementsByTagName(key)[0].childNodes[0].data

        return value
