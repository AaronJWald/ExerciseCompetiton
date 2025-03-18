import matplotlib.pyplot as plt
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email import encoders
from os.path import basename

def send_email(subject, body, to_email, filename = None):
    # Your email and password (use an app password if using Gmail)
    email_address = 'your_email@email.com'
    email_password = 'your smtp pass here'

    # Set up the MIME
    message = MIMEMultipart()
    message['From'] = email_address
    message['To'] = to_email
    message['Subject'] = subject

    # Attach the body of the email
    message.attach(MIMEText(body, 'plain'))

    if filename != None:    
        with open(filename, "rb") as attachment:
    # MIMEImage object for the PNG image
            part = MIMEImage(attachment.read(), name="graph.png")
            part.add_header("Content-Disposition", "attachment", filename="Performance.png")
            message.attach(part)

    # Connect to the SMTP server (in this case, Gmail's SMTP server)
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        # Start the TLS encryption
        server.starttls()

        # Login to the email account
        server.login(email_address, email_password)

        # Send the email
        server.sendmail(email_address, to_email, message.as_string())

# Example usage
if __name__ == "__main__":
    subject = 'Automated message'
    body = 'It worked!'
    to_email = 'your_email@email.com'  # Replace with your friend's email address

    send_email(subject, body, to_email)
