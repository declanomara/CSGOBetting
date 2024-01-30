# Importing the Required Modules
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Defining the send_email Function
def send_email(sender_email, receiver_email, subject, message, smtp_server, smtp_port, smtp_username, smtp_password):
    # Create a multipart message
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    # Add body to the email
    msg.attach(MIMEText(message, "plain"))

    try:
        # Create a secure SSL/TLS connection to the SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.ehlo()
        server.starttls()
        server.ehlo()

        # Login to the SMTP server
        server.login(smtp_username, smtp_password)

        # Send the email
        server.sendmail(sender_email, receiver_email, msg.as_string())

        # Close the SMTP connection
        server.quit()

        print("Email sent successfully!")
    except Exception as e:
        print("Failed to send email. Error:", str(e))

# Creating all the parameters
sender_email = "CSGO Betting Alerts"
receiver_email = "declan@omara.us"
subject = "+EV Opportunity Found!"
message = "This is a test message."

smtp_server = "smtp.gmail.com"
smtp_port = 587
smtp_username = "d.omara000@gmail.com"
smtp_password = "efzl vwys rrqh fwfy"

# Call the function
send_email(sender_email, receiver_email, subject, message, smtp_server, smtp_port, smtp_username, smtp_password)