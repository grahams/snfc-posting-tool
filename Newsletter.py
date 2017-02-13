# Import the sys module and add MX to the path.
import sys

from mx.DateTime import *
import re
import markup
import string
import textwrap

class Newsletter:
    city = ""
    clubURL = ""
    film = ""
    filmURL = ""
    host = ""
    hostURL = ""
    location = ""
    locationURL = ""
    showTime = ""
    synopsis = ""
    wearing = ""
    daySuffix = "th"

    # determine whatever the next sunday is
    nextSunday = now() + RelativeDateTime(weekday=(Sunday,0))

    def __init__(self, city, clubURL, film, filmURL,
                 host, hostURL, 
                 location, locationURL, 
                 wearing,
                 showTime, synopsis):
        self.city = city
        self.clubURL = clubURL
        self.film = film.strip()
        self.filmURL = filmURL.strip()
        self.host = host.strip()
        self.hostURL = hostURL.strip()
        self.location = location.strip()
        self.locationURL = locationURL.strip()
        self.wearing = wearing.strip()
        self.showTime = showTime.strip()
        self.synopsis = synopsis.strip()

        if( (self.nextSunday.day == 1) | (self.nextSunday.day == 21) | 
            (self.nextSunday.day == 31) ):
            self.daySuffix = "st"

        if( (self.nextSunday.day == 2) | (self.nextSunday.day == 22) ):
            self.daySuffix = "nd"

        if( (self.nextSunday.day == 3) | (self.nextSunday.day == 23) ):
            self.daySuffix = "rd"

    def generateSubject(self):
        subject = '"' + self.film + '" - '
        subject += self.nextSunday.strftime("%b %e") + self.daySuffix

        return subject

    def generateHTML(self):
        page = markup.page(mode="loose_html", separator="")

        page.p.open()
        page.add("Join the ")
        page.a(self.city + " Sunday Night Film Club", href=self.clubURL)
        page.add(" this ")

        page.b.open()
        page.add( self.nextSunday.strftime("%A, %b %e") + self.daySuffix )
        page.b.close()

        page.add(" at ")
        
        page.b.open()
        page.add(self.showTime)
        page.b.close()

        page.add(" for ")

        page.a( self.film, href=self.filmURL )

        page.add(" at the ")

        page.a( self.location, href=self.locationURL )

        page.add(". Look for ")

        page.a( self.host, href=self.hostURL )

        page.add(" wearing ")

        page.add( self.wearing )

        page.add(" in the theatre lobby about 15 minutes "
                 "before the film.  As always, after the film we will "
                 "descend on a local establishment for "
                 "dinner/drinks/discussion.")
        page.p.close()

        # yeah, I break strict HTML, what you gonna make of it?
        page.add('<lj-cut text="Film Synopsis" />')

        # hacky attempt at breaking synopsis up into paragraphs...
        r = re.compile("^\r$", re.MULTILINE)
        uni = unicode(self.synopsis, 'latin-1')

        syn = r.split(uni.encode('utf-8', 'replace'))

        page.p(syn)

        return page

    def generateTwitter(self):
        resultText =  '"' + self.film + '" @ ' + self.location + '. '
        resultText += self.nextSunday.strftime("%A, %b %e") + self.daySuffix 
        resultText += " at " + self.showTime

        return resultText

    def generatePlainText(self):
        resultText = "Join the " + self.city + " Sunday Night Film Club "

        resultText += "(" + self.clubURL + ") this "

        resultText += self.nextSunday.strftime("%A, %b %e") + self.daySuffix 
        resultText += " at " + self.showTime + " for " + self.film 

        resultText += ' at the ' + self.location + ". "

        resultText += 'Look for ' + self.host + " "
        resultText += "wearing "
        resultText += self.wearing
        resultText += " in the theatre lobby about 15 "
        resultText += "minutes before the film. As always, after the film "
        resultText += "we will descend on a local establishment for "
        resultText += "dinner/drinks/discussion.\n\n"

        resultText = textwrap.fill(resultText, 70)
        resultText += "\n\n"
        
        # hacky attempt at breaking synopsis up into paragraphs...
        r = re.compile("^\r$", re.MULTILINE)
        syn = r.split(self.synopsis)

        for x in syn:
            s = x
            s = re.sub("\r", "", s)
            s = re.sub("\n", "", s)
            s = textwrap.dedent(s).strip()
            resultText += textwrap.fill(s, 70)
            resultText += "\n\n"

        return resultText

    def generateCraigslist(self):
        page = markup.page(mode="xml")
        page.init( doctype="" )

        page.p.open()
        page.add("Join the ")
        page.a(self.city + " Sunday Night Film Club", href=self.clubURL)
        page.add(" this ")

        page.b.open()
        page.add( self.nextSunday.strftime("%A, %b %e") + self.daySuffix )
        page.b.close()

        page.add(" at ")
        
        page.b.open()
        page.add(self.showTime)
        page.b.close()

        page.add(" for ")

        page.b.open()
        page.add( self.film )
        page.b.close()

        page.add(" at the ")

        page.b.open()
        page.add( self.location )
        page.b.close()

        page.add(". Look for ")

        page.b.open()
        page.add( self.host )
        page.b.close()

        page.add(" wearing ")

        page.add( self.wearing )

        page.add("in the theatre lobby about 15 minutes "
                 "before the film.  As always, after the film we will "
                 "descend on a local establishment for "
                 "dinner/drinks/discussion.")
        page.p.close()

        page.p.open()
        page.add("For links, film synopsis, and further details, visit ")
        page.a("the " + self.city + " Sunday Night Film Club homepage", 
               href=self.clubURL)
        page.add(".")
        page.p.close()

        return page

