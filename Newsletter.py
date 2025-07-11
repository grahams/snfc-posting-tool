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
        self.showTime = self.normalize_time(showTime)
        self.synopsis = synopsis.strip()
        self.daySuffix = self.get_date_suffix(self.get_next_sunday().day)

    def get_next_sunday(self):
        # determine whatever the next sunday is
        nextSunday = datetime.now() + relativedelta(weekday=6)
        return nextSunday

    def get_date_suffix(self, d):
        return {1:'st',2:'nd',3:'rd'}.get(d%20, 'th')

    def normalize_time(self, time_str):
        """
        Normalize various time input formats to a standard format (e.g. "7:00 PM").
        Handles formats like:
        - 4p, 400p, 4pm, 4:00p, 4:00pm
        - 400 (assumed PM)
        - 4:00 PM, 4:00PM
        - 605pm (6:05 PM)
        """
        # Remove any extra whitespace
        time_str = time_str.strip().lower()
        print(f"Processing time string: '{time_str}'")
        
        # Handle times without separators (e.g. 400, 220)
        if re.match(r'^(\d{1,4})$', time_str):
            print("Matched numeric-only pattern")
            # If it's 3 or 4 digits, assume it's a time without separator
            if len(time_str) >= 3:
                # Last two digits are minutes
                hour = int(time_str[:-2])
                minute = time_str[-2:]
                # Since this is an evening club, assume PM
                return f"{hour}:{minute}pm"
            else:
                # assume just an hour
                hour = time_str
                # Since this is an evening club, assume PM
                return f"{hour}:00pm"
        
        # Handle times with minutes but no colon (e.g., "605pm", "605p")
        no_colon_match = re.match(r'^(\d{1,2})(\d{2})([ap]m?)?$', time_str)
        if no_colon_match:
            print(f"Matched no-colon pattern: {no_colon_match.groups()}")
            hour = int(no_colon_match.group(1))
            minute = no_colon_match.group(2)
            ampm = no_colon_match.group(3) or 'pm'
            ampm = 'pm' if ampm.startswith('p') else 'am'
            hour = hour % 12 or 12
            return f"{hour}:{minute}{ampm}"
        
        # Handle simple format (e.g., "8p", "8pm")
        simple_match = re.match(r'^(\d{1,2})([ap]m?)?$', time_str)
        if simple_match:
            print(f"Matched simple pattern: {simple_match.groups()}")
            hour = int(simple_match.group(1))
            ampm = simple_match.group(2) or 'pm'
            ampm = 'pm' if ampm.startswith('p') else 'am'
            hour = hour % 12 or 12
            return f"{hour}:00{ampm}"
            
        # Handle complex format (e.g., "8:00pm", "8:00 pm")
        complex_match = re.match(r'^(\d{1,2}):(\d{2})\s*([ap]m?)?$', time_str)
        if complex_match:
            print(f"Matched complex pattern: {complex_match.groups()}")
            hour = int(complex_match.group(1))
            minute = complex_match.group(2)
            ampm = complex_match.group(3) or 'pm'
            ampm = 'pm' if ampm.startswith('p') else 'am'
            hour = hour % 12 or 12
            return f"{hour}:{minute}{ampm}"
        
        raise ValueError(f"Invalid time format: {time_str}")

    def generate_subject(self):
        subject = f'"{self.film}" - {self.get_next_sunday().strftime("%b %d")}{self.daySuffix}'

        return subject

    def generate_HTML(self):
        env = Environment(loader=FileSystemLoader('templates/'))
        template = env.get_template('htmlnewsletter.html')

        # Split synopsis into paragraphs
        r = re.compile("^\r$", re.MULTILINE)
        syn = r.split(self.synopsis)
        synopsis_paragraphs = [textwrap.dedent(s).strip() for s in syn]

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
        synopsis_paragraphs = [textwrap.dedent(s).strip() for s in syn]

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
        synopsis_paragraphs = [textwrap.dedent(s).strip() for s in syn]

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