import smtplib
from email.message import EmailMessage
import os
import glob

def send_email_with_latest_cours_and_qr():
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = int(os.getenv("SMTP_PORT"))
    EMAIL = os.getenv("EMAIL_USERNAME")
    PASSWORD = os.getenv("EMAIL_PASSWORD")

    output_dir = os.getenv("OUTPUT_DIR", "./rapports")
    cours_dir = os.path.join(output_dir, "cours")
    qr_dir = os.path.join(output_dir, "qr")

    # Dernier fichier dans cours
    cours_files = glob.glob(os.path.join(cours_dir, "*.docx"))
    if not cours_files:
        print("❌ Aucun fichier cours trouvé.")
        return
    latest_cours = max(cours_files, key=os.path.getmtime)

    # Dernier fichier dans qr
    qr_files = glob.glob(os.path.join(qr_dir, "*.docx"))
    if not qr_files:
        print("❌ Aucun fichier Q/R trouvé.")
        return
    latest_qr = max(qr_files, key=os.path.getmtime)

    # Création du message
    msg = EmailMessage()
    msg["Subject"] = "Livrables du jour"
    msg["From"] = EMAIL
    msg["To"] = "mactar031@gmail.com"
    msg.set_content("Bonjour,\nJe vous envoie ci-joint le livrable du jour (cours + Q/R).")

    # Ajouter le cours
    with open(latest_cours, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=os.path.basename(f.name)
        )

    # Ajouter le QR
    with open(latest_qr, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=os.path.basename(f.name)
        )

    # Envoi
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.login(EMAIL, PASSWORD)
            smtp.send_message(msg)
        print(f"✅ Email envoyé avec succès ! Fichiers : {os.path.basename(latest_cours)}, {os.path.basename(latest_qr)}")
    except smtplib.SMTPAuthenticationError:
        print("❌ Erreur d’authentification. Vérifie l’adresse ou le mot de passe.")
    except Exception as e:
        print(f"❌ Une erreur est survenue : {e}")
