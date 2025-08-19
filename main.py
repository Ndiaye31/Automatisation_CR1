# main.py
import os
from datetime import datetime
from extraction_notion_blocks import (
    lister_pages_interessantes,
    get_last_export_time,
    save_last_export_time,
    get_modified_blocks,
    get_page_title,
    get_text_from_blocks,
    #generate_questions_answers,
    save_to_docx,
    COURS_DIR,
    QR_DIR,
)
from send_mail import send_email_with_latest_cours_and_qr


def main():
    # 1. Récupérer les pages cibles (automatique)
    PAGES_INTERESSANTES = ["Git", "Dataiku", "Talend_Studio", "Python", "Docker", "SHELL"]
    pages = lister_pages_interessantes(PAGES_INTERESSANTES)

    # 2. Exporter les modifs par page
    global_text_for_qr = ""
    cours_files = []

    for title, page_id in pages.items():
        since_time = get_last_export_time(page_id)
        modified_blocks = get_modified_blocks(page_id, since_time)

        if not modified_blocks:
            print(f"⏩ Pas de modif dans {title}")
            continue

        # Concaténer texte modifié
        page_text = get_text_from_blocks(modified_blocks)

        # Sauvegarder fichier Word de compte rendu par page
        current_date = datetime.now().strftime("%Y-%m-%d_%H-%M")
        output_file = os.path.join(COURS_DIR, f"CR_{title}_{current_date}.docx")
        save_to_docx(page_text, output_file)
        cours_files.append(output_file)

        # Ajouter au texte global pour le Q/R
        global_text_for_qr += f"\n\n=== {title} ===\n{page_text}"

        # Marquer l’export
        save_last_export_time(page_id)

        print(f"✅ Exporté : {output_file}")

    # 3. Générer Q/R global
    # if global_text_for_qr.strip():
    #     qa_content = generate_questions_answers(global_text_for_qr)
    #     current_date = datetime.now().strftime("%Y-%m-%d_%H-%M")
    #     qr_file = os.path.join(QR_DIR, f"QR_Global_{current_date}.docx")
    #     save_to_docx(qa_content, qr_file)
    #     print(f"✅ Fichier Q/R global créé : {qr_file}")

    #     # 4. Envoyer par mail
    #     send_email_with_latest_cours_and_qr()
    # else:
    #     print("⚠️ Aucune modification trouvée, rien à générer.")
    # 5. Envoyer par mail
    send_email_with_latest_cours_and_qr()

if __name__ == "__main__":
    main()
