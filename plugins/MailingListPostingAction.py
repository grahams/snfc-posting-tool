import smtplib

from email.message import EmailMessage
from email.utils import make_msgid

from Newsletter import Newsletter
from BasePostingAction import BasePostingAction

class MailingListPostingAction(BasePostingAction):
    pluginName = "SNFC Mailing List"
    configSection = 'mailingList'
    
    def execute(self, config, nl):
        self.config = config 

        sender = self.read_config_value('sender')
        recipient = self.read_config_value('recipient')
        url = self.read_config_value('url')
        smtpUsername = self.read_config_value('smtpUsername')
        smtpPassword = self.read_config_value('smtpPassword')

        msg = EmailMessage()
        msg['Subject'] = nl.generate_subject()
        msg['From'] = sender
        msg['To'] = recipient
        msg.set_content(nl.generate_plain_text())

        msg.add_alternative(str(nl.generate_HTML()), subtype='html')
    
        s = smtplib.SMTP_SSL('mail.messagingengine.com', 465)
        s.login(smtpUsername, smtpPassword) # type: ignore
        s.send_message(msg)

        return(f"Posted to the <a href='{url}'>Mailing List</a><br />")
