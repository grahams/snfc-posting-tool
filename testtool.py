#!/usr/bin/python

import sys
import glob
import smtplib

from xml.dom import minidom

from Newsletter import Newsletter
from BasePostingAction import BasePostingAction

config = None
scriptPath = "/usr/share/wordpress/tool/boston"
hostsDict = dict()
locationsDict = dict()

film = "Ignore this Posting: The Alan Smithee Story"
filmURL = "http://en.wikipedia.org/wiki/Alan_Smithee"
host = "Sean"
hostURL = "http://www.flickr.com/photos/seangraham/125530602/"
location = "Example Cinema"
locationURL = "http://landmarktheatres.com/Market/Boston/Boston_Frameset.htm"
wearing = "a nametag"
showTime = "7:00pm"

synopsis = "This is a test post, ignore it."

# read the configuration xml
def read_config(filename):
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


nl = Newsletter("Boston", "http://boston.sundaynightfilmclub.com/", film, 
                filmURL, host, hostURL, location, locationURL,
                wearing, showTime, synopsis)

plugins = glob.glob("plugins/Crai*.py")
sys.path.append("plugins/")

for x in plugins: 
    className = x.replace(".py","").replace("plugins/","")

    config = read_config(scriptPath + "/.postingtoolrc")

    foo = __import__(className, globals(), locals(), [''])
    bar = getattr(foo,className)

    obj = bar()

    print(obj)
    obj.execute(config,nl)

