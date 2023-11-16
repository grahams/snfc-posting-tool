from Newsletter import Newsletter

class BasePostingAction:
    pluginName = "Base Class"
    configSection = "basePostingAction"
    config = None

    def execute(self, config, nl):
        print("This should do something profound\n\n")

        print(nl.generateHTML())

    def read_config_value(self, key):
        if self.config:
            return self.config[self.configSection][key]
        else:
            return None

