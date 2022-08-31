import smtplib
import ssl
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart



class AutomatedEmail:
    """Class for Email"""

    def __init__(self, sent_from, sent_to):
        """ 
        sent_from: Name of the person who is sending email
        sent_to: Email of the person to whom email will be sent
        """
        self.message = MIMEMultipart("alternative")
        self.message["From"] = self.sent_from = sent_from
        self.sent_to = sent_to
        if isinstance(self.sent_to, (list, tuple)):
            self.message["To"] = ", ".join(self.sent_to)
        elif isinstance(self.sent_to, str):
            self.message["To"] = self.sent_to
        else:
            raise ValueError

        self.user_email = None
        self.password = None

        self.ssl_host = 'smtp.gmail.com'
        self.ssl_port = 465
        self.is_ssl_set = False

    def add_subject(self, subject):
        """Add the subject to the email"""
        self.message["Subject"] = subject

    def set_login_details(self, user_email, password):
        """ Email will be send by using the following details """
        self.user_email = user_email
        self.password = password

    def set_smtp_ssl(self, ssl_host, ssl_port):
        self.ssl_host = ssl_host
        self.ssl_port = ssl_port
        self.is_ssl_set = True

    def add_alternative_text(self, text):
        """Add alternative text, just in case HTML doesn't gets rendered."""
        part1 = MIMEText(text, "plain")
        self.message.attach(part1)

    def add_html(self, html):
        """ Add HTML to the email"""
        part2 = MIMEText(html, "html")
        self.message.attach(part2)

    def send(self):
        """ Finally login and send the mail"""
        # Create a secure SSL context
        context = ssl.create_default_context()

        if not self.is_ssl_set:
            print(f"SSL is not set. Using Gmail's Host:'{self.ssl_host}' and Port:{self.ssl_port}")
        with smtplib.SMTP_SSL(self.ssl_host, self.ssl_port, context=context) as server:
            print(self.user_email, self.password)
            server.login(self.user_email, self.password)
            server.sendmail(self.user_email, [self.sent_to], self.message.as_string())


class HTMLPage:

    def __init__(self, html_path):
        self.html_path = html_path
        self.text = None

    def read_page(self):
        with open(self.html_path, 'r') as html:
            html_text = html.read()
        self.text = html_text

    def format_page(self, **kwargs):
        if self.text:
            self.text = self.text.format(**kwargs)
        else:
            raise Exception("Call read_page() first")

    def get_text(self):
        return self.text


def send_activation_email(user, user_email, activation_link):
    # Harcoded login details

    sent_from = "my@email.com"
    sent_from_password = "mypassword"
    sent_to = user_email

    email = AutomatedEmail(sent_from, sent_to)
    email.set_smtp_ssl(ssl_host="mail.coderize.in", ssl_port=465)
    email.add_subject("CodeRize Products Activation_link")
    email.set_login_details(user_email=sent_from, password=sent_from_password)

    link = activation_link
    text = f"""
    Hi , This is the alternative text if HTML Doesn't gets rendered.
    Here is your activation link
    {link}
    """

    html_path = os.path.join(settings.BASE_DIR, 'templates', 'activation_email_template.html')
    html = HTMLPage(html_path)
    html.read_page()
    html.format_page(UserName=user, ActivationLink=link)

    email.add_alternative_text(text)
    email.add_html(html.get_text())

    email.send()


def send_forgot_password_link(send_to_email, link_with_passcode):
    # Harcoded login details

    sent_from = "my@email.com"
    sent_from_password = "mypassword"

    email = AutomatedEmail(sent_from, send_to_email)
    email.set_smtp_ssl(ssl_host="mail.coderize.in", ssl_port=465)
    email.add_subject(" CodeRize GeoSet Viewer activation_link")
    email.set_login_details(user_email=sent_from, password=sent_from_password)

    text = f"""
    Hi , This is the alternative text if HTML Doesn't gets rendered.
    Here is your activation link
    {link_with_passcode}
    """
    html_path = os.path.join(r"E:\Projects\FSProjects\RandomFactsDashboard\RandomFactsDashboard-BE\auth\email_template.html")
    html = HTMLPage(html_path)
    html.read_page()
    html.format_page(UserName=send_to_email, ActivationLink=link_with_passcode)

    email.add_alternative_text(text)
    email.add_html(html.get_text())

    email.send()
