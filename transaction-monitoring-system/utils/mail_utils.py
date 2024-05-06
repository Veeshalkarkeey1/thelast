from configurations import SMTP_HOST, SMTP_PORT, MAIL_FROM, MAIL_PASSWORD
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from utils import logger
import smtplib

# connecting with the mail server
mail = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
mail.ehlo()
mail.starttls()
mail.login(MAIL_FROM, MAIL_PASSWORD)


def send_mail_html(subject, mail_to,  html_message, mail_cc=None, mail_bcc=None):
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = MAIL_FROM
        msg['To'] = mail_to
        msg['Cc'] = mail_cc
        msg["Bcc"] = mail_bcc
        msg.attach(MIMEText(html_message, 'html'))
        mail.send_message(msg)
        return 1
    except Exception as e:
        logger.exception('Error sending mail',  str(e))
        return 0





