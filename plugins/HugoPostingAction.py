from datetime import datetime
import os
import re
from BasePostingAction import BasePostingAction

class HugoPostingAction(BasePostingAction):
    pluginName = "Hugo Site"
    configSection = "hugo"
    config = None

    def execute(self, config, nl):
        self.config = config
        
        # Get the Hugo content directory from config
        content_dir = self.read_config_value('contentDir')
        if not content_dir:
            raise ValueError("Hugo content directory not configured")

        # Generate the post filename using the date and film title
        date = nl.get_next_sunday()
        # Strip all punctuation and symbols except hyphens, convert to lowercase, and replace spaces with hyphens
        clean_title = re.sub(r'[^\w\s-]', '', nl.film.lower())
        clean_title = re.sub(r'[-\s]+', '-', clean_title)
        filename = f"{date.strftime('%Y-%m-%d')}-{clean_title}.md"
        filepath = os.path.join(content_dir, filename)

        # Generate the front matter
        front_matter = f"""---
title: '{nl.generate_subject()}'
date: "{datetime.now().strftime('%Y-%m-%dT%H:%M:%S-00:00')}"
draft: false
tags: ["newsletter"]
---
"""

        # Write the file
        with open(filepath, 'w') as f:
            f.write(front_matter + nl.generate_markdown())

        return f"Posted to Hugo blog at {filepath}" 