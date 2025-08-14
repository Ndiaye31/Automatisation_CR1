# main.py
import os
from datetime import datetime
from extraction_notion_blocks import (
    export_notion_to_word,
    extract_text_from_docx,
    generate_questions_answers,
    save_to_docx,
    QR_DIR
)
from send_mail import send_email_with_latest_cours_and_qr


def main():
    # 1. Exporter le cours depuis Notion
    cours_file = export_notion_to_word()

    # 2. Lire le texte du cours
    cours_text = extract_text_from_docx(cours_file)

    # 3. Générer Q/R
    qa_content = generate_questions_answers(cours_text)

    # 4. Sauvegarder Q/R
    base_name = os.path.splitext(os.path.basename(cours_file))[0]
    current_date = datetime.now().strftime("%Y-%m-%d_%H-%M")
    qr_file = os.path.join(QR_DIR, f"QR_{base_name}_{current_date}.docx")

    save_to_docx(qa_content, qr_file)
    print(f"✅ Fichier Q/R créé : {qr_file}")

    # 5. Envoyer par mail
    send_email_with_latest_cours_and_qr()


if __name__ == "__main__":
    main()
