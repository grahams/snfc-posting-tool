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

        sender = self.readConfigValue('sender')
        recipient = self.readConfigValue('recipient')
        url = self.readConfigValue('url')
        smtpUsername = self.readConfigValue('smtpUsername')
        smtpPassword = self.readConfigValue('smtpPassword')

        msg = EmailMessage()
        msg['Subject'] = nl.generateSubject()
        msg['From'] = sender
        msg['To'] = recipient
        msg.set_content(nl.generatePlainText())

        msg.add_alternative(str(nl.generateHTML()), subtype='html')
    
        s = smtplib.SMTP_SSL('mail.messagingengine.com', 465)
        s.login(smtpUsername, smtpPassword)
        s.send_message(msg)

        return(f"Posted to the <a href='{url}'>Mailing List</a><br />")
