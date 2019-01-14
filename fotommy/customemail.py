import smtplib
from email.mime.text import MIMEText
class Email(object):
    """docstring for Email"""
    def __init__(self, body='(empty)', subject='(empty)', recipients=None, test=False):
        super(Email, self).__init__()
        self.test = test
        self.subject = subject
        self.body = body
        if recipients is None:
            self.recipients = ['thomasklijnsma@gmail.com']
        else:
            self.recipients = recipients

    def parse_msg(self, recipient):
        msg = MIMEText(self.body, 'html')
        msg['Subject'] = '[ws] ' + self.subject
        msg['From']    = 'tklijnsm.helper@gmail.com'
        msg['To']      = recipient
        return msg

    def send(self):
        for recipient in self.recipients:
            msg = self.parse_msg(recipient)
            if not self.test:
                server = smtplib.SMTP('smtp.gmail.com:587')
                server.ehlo()
                server.starttls()
                server.login(
                    'tklijnsm.helper@gmail.com',
                    'iwanttohelp'
                    )
                server.sendmail( msg['From'], msg['To'], msg.as_string() )
                server.quit()
            else:
                logging.info('TEST MODE: Sending the following email:')
                logging.info(msg)
