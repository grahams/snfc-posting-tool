from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from dateutil.relativedelta import relativedelta
import re
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
        self.daySuffix = self.get_date_suffix(self.get_next_sunday().day)

    def get_next_sunday(self):
        # determine whatever the next sunday is
        nextSunday = datetime.now() + relativedelta(weekday=6)
        return nextSunday

    def get_date_suffix(self, d):
        return {1:'st',2:'nd',3:'rd'}.get(d%20, 'th')

    def generate_subject(self):
        subject = f'"{self.film}" - {self.get_next_sunday().strftime("%b %d")}{self.daySuffix}'

        return subject

    def generate_HTML(self):
        env = Environment(loader=FileSystemLoader('templates/'))
        template = env.get_template('htmlnewsletter.html')

        # Split synopsis into paragraphs
        r = re.compile("^\r$", re.MULTILINE)
        syn = r.split(self.synopsis)
        synopsis_paragraphs = [textwrap.fill(textwrap.dedent(s).strip(), 70) for s in syn]

        rendered_template = template.render(
            city=self.city,
            clubURL=self.clubURL,
            nextSunday=self.get_next_sunday().strftime("%A, %b %e"),
            daySuffix=self.daySuffix,
            showTime=self.showTime,
            film=self.film,
            filmURL=self.filmURL,
            location=self.location,
            locationURL=self.locationURL,
            host=self.host,
            hostURL=self.hostURL,
            wearing=self.wearing,
            synopsis=synopsis_paragraphs
        )

        return rendered_template

    def generate_twitter(self):
        resultText = f'"{self.film}" @ {self.location}. {self.get_next_sunday().strftime("%A, %b %e")}{self.daySuffix} at {self.showTime}. Look for your host, {self.host}.'

        return resultText

    def generate_plain_text(self):
        env = Environment(loader=FileSystemLoader('templates/'))
        template = env.get_template('textnewsletter.txt')

        # Split synopsis into paragraphs
        r = re.compile("^\r$", re.MULTILINE)
        syn = r.split(self.synopsis)
        synopsis_paragraphs = [textwrap.fill(textwrap.dedent(s).strip(), 70) for s in syn]

        rendered_template = template.render(
            city=self.city,
            clubURL=self.clubURL,
            nextSunday=self.get_next_sunday().strftime("%A, %b %e"),
            daySuffix=self.daySuffix,
            showTime=self.showTime,
            film=self.film,
            location=self.location,
            host=self.host,
            wearing=self.wearing,
            synopsis=synopsis_paragraphs
        )

        return rendered_template

    def generate_markdown(self):
        env = Environment(loader=FileSystemLoader('templates/'))
        template = env.get_template('markdownnewsletter.md')

        # Split synopsis into paragraphs
        r = re.compile("^\r$", re.MULTILINE)
        syn = r.split(self.synopsis)
        synopsis_paragraphs = [textwrap.fill(textwrap.dedent(s).strip(), 70) for s in syn]

        rendered_template = template.render(
            city=self.city,
            clubURL=self.clubURL,
            nextSunday=self.get_next_sunday().strftime("%A, %b %e"),
            daySuffix=self.daySuffix,
            showTime=self.showTime,
            film=self.film,
            filmURL=self.filmURL,
            location=self.location,
            locationURL=self.locationURL,
            host=self.host,
            hostURL=self.hostURL,
            wearing=self.wearing,
            synopsis=synopsis_paragraphs
        )

        return rendered_template