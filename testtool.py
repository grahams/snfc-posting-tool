#!/usr/bin/python

import sys
import glob
import markup
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

from Newsletter import Newsletter
from BasePostingAction import BasePostingAction

film = "Ignore this Posting: The Alan Smithee Story"
filmURL = "http://en.wikipedia.org/wiki/Alan_Smithee"
host = "Sean"
hostURL = "http://www.flickr.com/photos/seangraham/125530602/"
location = "Example Cinema"
locationURL = "http://landmarktheatres.com/Market/Boston/Boston_Frameset.htm"
wearing = "a nametag"
showTime = "7:00pm"

synopsis = "This is a test post, ignore it."

nl = Newsletter("Boston", "http://boston.sundaynightfilmclub.com/", film, 
                filmURL, host, hostURL, location, locationURL,
                wearing, showTime, synopsis)

plugins = glob.glob("plugins/Goo*.py")
sys.path.append("plugins/")

for x in plugins: 
    className = x.replace(".py","").replace("plugins/","")

    foo = __import__(className, globals(), locals(), [''])
    bar = getattr(foo,className)

    obj = bar()

    print obj
    obj.execute(None,nl)
