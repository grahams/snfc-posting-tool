import smtplib

from email.message import EmailMessage
from email.policy import default as default_policy
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
        smtpHostname = self.read_config_value('smtpHostname')
        smtpPort = self.read_config_value('smtpPort')
        smtpUseSSL = self.read_config_value('smtpUseSSL')
        smtpUseStartTLS = self.read_config_value('smtpUseStartTLS')

        # Use a policy with an extremely large max line length to avoid wrapping
        mail_policy = default_policy.clone(max_line_length=100000)
        msg = EmailMessage(policy=mail_policy)
        msg['Subject'] = nl.generate_subject()
        msg['From'] = sender
        msg['To'] = recipient
        # Avoid quoted-printable soft wraps for easier local inspection
        msg.set_content(nl.generate_plain_text(), subtype='plain', charset='utf-8', cte='8bit')

        msg.add_alternative(str(nl.generate_HTML()), subtype='html', charset='utf-8', cte='8bit')
        
        # Normalize config
        host = smtpHostname or 'localhost'
        port = int(smtpPort) if smtpPort else (465 if smtpUseSSL else 25)
        use_ssl = bool(smtpUseSSL) if smtpUseSSL is not None else True
        use_starttls = bool(smtpUseStartTLS) if smtpUseStartTLS is not None else False

        if use_ssl:
            server = smtplib.SMTP_SSL(host, port)
        else:
            server = smtplib.SMTP(host, port)

        try:
            if not use_ssl and use_starttls:
                server.starttls()
            # Login only if credentials provided
            if smtpUsername and smtpPassword:
                server.login(smtpUsername, smtpPassword)
            server.send_message(msg)
        finally:
            try:
                server.quit()
            except Exception:
                pass

        return(f"Posted to the <a href='{url}'>Mailing List</a><br />")
