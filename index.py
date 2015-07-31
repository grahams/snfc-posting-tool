#!/usr/bin/python

import sys

sys.path.append(".")

import glob
import markup
import cgi
import cgitb; cgitb.enable(); sys.stderr = sys.stdout
import traceback

from unidecode import unidecode
from xml.dom import minidom

from Newsletter import Newsletter
from BasePostingAction import BasePostingAction
from mod_python import apache,util

clubCity = ""
clubURL = ""

hostsDict = dict()
locationsDict = dict()

config = None
scriptPath = "/usr/share/wordpress/tool/boston"

pluginList = { }

def load_plugins():
    global scriptPath

    pluginPath = ""

    if( scriptPath.endswith('/') ):
        pluginPath = scriptPath + "plugins/"
    else:
        pluginPath = scriptPath + "/plugins/"

    sys.path.append(scriptPath)
    sys.path.append(pluginPath)

    pluginNames = glob.glob(pluginPath + "/*.py")
    
    for x in pluginNames: 
        pathName = x.replace(".py","")
        className = x.replace(".py","").replace(pluginPath,"")

        # import the module
        mod = __import__(className, globals(), locals(), [''])

        # find the symbol for the class
        cls  = getattr(mod,className)

        # add the plugin to the list
        pluginList[ cls().pluginName ] = cls()

# Define function to generate HTML form.
def generate_form():
    load_plugins() 

    page = markup.page()
    
    page.init(title=clubCity + " SNFC Newsletter Tool",
              css=('tool.css'))


    page.div( id="leftColumnDiv" )

    page.div( id="hostsDiv" )
    page.fieldset( id="hostsFieldSet" )

    page.legend("Choose a host:")

    page.form.open(method="post", action="index.py")
    page.select.open(size=5, name="hostSelect")
    page.option(hostsDict)
    page.select.close()

    page.br()
    page.br()

    page.add("Wearing: ")
    page.input(type="text", name="wearing", value="a nametag")

    page.fieldset.close()
    page.div.close()

    page.div( id="locationDiv" )
    page.fieldset( id="locationSet" )

    page.legend("Locations:")
    page.select.open(size=9, name="locationSelect")
    page.option(locationsDict)
    page.select.close()

    page.fieldset.close()
    page.div.close()

    page.div( id="filmInfoDiv" )
    page.fieldset( id="filmInfoSet" )

    page.legend( "Film Information:" )

    page.add("Film: ")
    page.input(type="text", name="film")
    page.br()

    page.add("Film URL: ")
    page.input(type="text", name="filmURL")
    page.br()

    page.add("Showtime: ")
    page.input(type="text", name="showTime")
    page.br()

    page.add("Plot Synopsis:")
    page.br()
    page.textarea.open(name="plotSynopsis", rows=10, cols=40)
    page.textarea.close()

    page.fieldset.close()
    page.div.close()

    page.div.close()

    page.div( id="rightColumnDiv" )

    page.div( id="targetsDiv" )
    page.fieldset( id="targetsSet" )

    page.legend("Where should I post to?")

    for x, y in pluginList.iteritems():
        page.input(checked="checked", type="checkbox", name="plugins", value=x)
        page.add(x)
        page.br()

    page.fieldset.close()
    page.div.close()

    page.div( id="buttonsDiv" )
    page.fieldset( id="buttonsSet" )

    page.input(type="hidden", name="Submit", value="send")
    page.input(type="submit", value="Enter")
    page.input(type="reset")
    page.form.close()

    page.fieldset.close()
    page.div.close()

    page.div.close()
              
    print page

# Define function display data.
def display_data(form):
    nl = Newsletter(clubCity,
                    clubURL,
                    unidecode(form["film"].value),
                    form["filmURL"].value,
                    form["hostSelect"].value,
                    hostsDict[form["hostSelect"].value],
                    form["locationSelect"].value,
                    locationsDict[form["locationSelect"].value],
                    unidecode(form["wearing"].value),
                    form["showTime"].value,
                    unidecode(form["plotSynopsis"].value))

    load_plugins()

    list = form.getlist("plugins")

    for x in list:
        plugin = pluginList[x]

        #plugin.execute(config, nl)
    
        try:
            plugin.execute(config, nl)
        except:
            print "Error in " + plugin.pluginName + "<br>"
            print "<pre>"
            traceback.print_exc(file=sys.stdout)
            print "</pre>"

# read the configuration xml
def readConfig(filename):
    document = minidom.parse(filename)

    global clubCity
    global clubURL

    clubCity = document.getElementsByTagName("clubCity")[0].childNodes[0].data
    clubURL = document.getElementsByTagName("clubURL")[0].childNodes[0].data

    hosts = document.getElementsByTagName('host')

    for host in hosts:
        name = host.getElementsByTagName('name')[0].childNodes[0].data
        image = host.getElementsByTagName('image')[0].childNodes[0].data

        hostsDict[name] = image

    locations = document.getElementsByTagName('location')

    for location in locations:
        name = location.getElementsByTagName('name')[0].childNodes[0].data
        link = location.getElementsByTagName('link')[0].childNodes[0].data

        locationsDict[name] = link

    return document

# Define main function.
def main(req):
    form = util.FieldStorage(req)

    global scriptPath
    global config 

    scriptPath = req.filename

    if(scriptPath.endswith('index.py')):
        scriptPath = scriptPath.replace('index.py','')

    config = readConfig(scriptPath + "/.postingtoolrc")

    if (form.has_key("hostSelect") ):
        if (form["Submit"].value == "send"):
            display_data(form)
    else:
        generate_form()

def handler(req):
    req.content_type = "text/html"

    sys.stdout = req

    main(req)

    return apache.OK
