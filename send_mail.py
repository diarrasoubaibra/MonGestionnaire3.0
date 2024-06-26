import smtplib
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText 
from email.mime.application import MIMEApplication  

def envoicode(code, email):
    message = MIMEMultipart()
    message["From"] = 'ibrahimdiarrassouba840@gmail.com'
    message["To"] = email
    message["Subject"] = 'Code de vérification'
    
    message.attach(MIMEText(f"Bonjour, \n Votre code de vérification est {code}", "plain"))
    
    # Envoyer l'e-mail
    serveur_smtp = smtplib.SMTP("smtp.gmail.com", 587)
    serveur_smtp.starttls()
    serveur_smtp.login('ibrahimdiarrassouba840@gmail.com', 'ixmk cbww tlks vfea')
    serveur_smtp.sendmail('ibrahimdiarrassouba840@gmail.com', email, message.as_string())
    serveur_smtp.quit()