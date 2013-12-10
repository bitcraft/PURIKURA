import smtplib
import threading
import pickle

sender = 'leif@kilbuckcreek.com'
auth_file = '/home/mjolnir/git/PURIKURA/secrets'

class SenderThread(threading.Thread):

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.address = address
        self.filename = filename

    def run(self):
        import email
        from email.mime.text import MIMEText

        msg = email.MIMEMultipart.MIMEMultipart('mixed')
        msg['subject'] = 'Your photo from Kilbuck Creek Photo Booth'
        msg['from'] = sender
        msg['to'] = self.address

        body = email.mime.Text.MIMEText('Here\'s your photo!\n\nThank you!\n\n')
        msg.attach(body)

        file_msg = email.mime.base.MIMEBase('image', 'jpeg')
        file_msg.set_payload(open(self.filename).read())
        email.encoders.encode_base64(file_msg)
        file_msg.add_header(
            'Content-Disposition',
            'attachment;filname=photo.jpg')
        msg.attach(file_msg)

        with open(auth_file) as fh:
            auth = pickle.load(fh)
            auth = auth['smtp']

        smtpout = smtplib.SMTP(auth['host'])
        smtpout.login(auth['username'], auth['password'])

        auth = None

        smtpout.sendmail(sender, [self.address], msg.as_string())
        smtpout.quit()

