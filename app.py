from flask import Flask, request, render_template, redirect, url_for
from Newsletter import Newsletter

import glob
import os
import traceback
import sys
import json

app = Flask(__name__)

config = None
scriptPath = os.path.dirname(os.path.abspath(__file__))

pluginList = {}

# read the configuration 
def readConfig(filename):
    # read the configuration from the JSON file
    stream = open(filename, "r")
    config = json.load(stream)
    stream.close()

    return config

# read the configuration xml
config = readConfig(os.path.join(scriptPath, "config.json"))

def load_plugins():
    global scriptPath

    pluginPath = os.path.join(scriptPath, "plugins")

    sys.path.append(scriptPath)
    sys.path.append(pluginPath)

    pluginNames = glob.glob(os.path.join(pluginPath, "*.py"))
    
    for x in pluginNames: 
        pathName = x.replace(".py","")
        className = os.path.basename(pathName)

        # import the module
        mod = __import__(className)

        # find the symbol for the class
        cls  = getattr(mod, className)

        # add the plugin to the list
        pluginList[ cls().pluginName ] = cls()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        form = request.form

        hostIndex = 0;
        locationIndex = 0
        
        for x in config['hosts']:
            if x['name'] == form["hostSelect"]:
                break
            hostIndex += 1

        for x in config['locations']:
            if x['name'] == form["locationSelect"]:
                break
            locationIndex += 1


        nl = Newsletter(config['clubCity'],
                        config['clubURL'],
                        form["film"],
                        form["filmURL"],
                        form["hostSelect"],
                        config["hosts"][hostIndex]['image'],
                        form["locationSelect"],
                        config["locations"][locationIndex]['link'],
                        form["wearing"],
                        form["showTime"],
                        form["plotSynopsis"])

        load_plugins()

        list = form.getlist("plugins")

        responses = []

        for x in list:
            plugin = pluginList[x]
    
            try:
                responses.append(plugin.execute(config, nl))
            except:
                responses.append(f"Error in {plugin.pluginName}<br>")
                responses.append("<pre>")
                responses.append(traceback.format_exc(file=sys.stdout))
                responses.append("</pre>")

        return render_template('responses.html', responses=responses)

    else:
        load_plugins()

        plugNames = []

        for item in pluginList:
            plugNames.append(item)

        return render_template('form.html', pluginList=plugNames, hostsDict=config['hosts'], locationDict=config['locations'])

if __name__ == '__main__':
    app.run(debug=True)