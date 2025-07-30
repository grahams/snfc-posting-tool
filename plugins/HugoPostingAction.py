from datetime import datetime
import os
import re
from git import Repo
from git.remote import Remote
from BasePostingAction import BasePostingAction

class HugoPostingAction(BasePostingAction):
    pluginName = "Hugo Site"
    configSection = "hugo"
    config = None

    def execute(self, config, nl):
        self.config = config
        
        # Get the git repo directory from config
        git_repo_dir = self.read_config_value('gitRepoDir')
        content_dir = self.read_config_value('contentDir')
        ssh_key_path = self.read_config_value('sshKeyPath')
        if not content_dir:
            raise ValueError("Hugo content directory not configured")
        if not git_repo_dir:
            raise ValueError("Git repository directory not configured")

        # Generate the post filename using the date and film title
        date = nl.get_next_sunday()
        # Strip all punctuation and symbols except hyphens, convert to lowercase, and replace spaces with hyphens
        clean_title = re.sub(r'[^\w\s-]', '', nl.film.lower())
        clean_title = re.sub(r'[-\s]+', '-', clean_title)
        filename = f"{date.strftime('%Y-%m-%d')}-{clean_title}.md"
        
        # Create the full path in the git repo
        git_filepath = os.path.join(git_repo_dir, content_dir, filename)

        # Generate the front matter
        front_matter = f"""---
title: '{nl.generate_subject()}'
date: "{datetime.now().strftime('%Y-%m-%dT%H:%M:%S-00:00')}"
draft: false
tags: ["newsletter"]
---
"""

        # Write the file to the git repo
        with open(git_filepath, 'w') as f:
            f.write(front_matter + nl.generate_markdown())

        # Git operations: add, commit, and push using GitPython
        try:
            # Initialize the git repository
            repo = Repo(git_repo_dir)
            
            # Configure SSH key if specified
            if ssh_key_path:
                # Set the SSH command with the specified key
                ssh_cmd = f'ssh -i {ssh_key_path}'
                repo.git.update_environment(GIT_SSH_COMMAND=ssh_cmd)
            
            # Add the file to git
            repo.index.add([os.path.join(content_dir, filename)])
            
            # Commit the file
            commit_message = f"Add newsletter post: {nl.generate_subject()}"
            repo.index.commit(commit_message)
            
            # Push to remote
            origin = repo.remote(name='origin')
            origin.push()
            
            build_status = " and pushed to git repository successfully"
        except Exception as e:
            build_status = f" but git operations failed: {str(e)}"

        return f"Posted to Hugo blog at {git_filepath}{build_status}" 