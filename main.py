# main.py
import os
from datetime import datetime
from extraction_notion_blocks import (
    export_page,
    get_text_from_blocks,
    generate_questions_answers,
    save_to_docx,
    QR_DIR,
    NOTION_PAGE_IDS,
)
from send_mail import send_email_with_latest_cours_and_qr


def main():
    all_page_qr_sections = []

    # 1. Parcourir toutes les pages Notion configurées
    for page_id in NOTION_PAGE_IDS:
        page_id = page_id.strip()
        if not page_id:
            continue

        # Exporter uniquement les modifs dans un CR par page
        _, blocks, page_title = export_page(page_id)

        # S’il y a des modifs → préparer la section Q/R correspondante
        if blocks:
            text_for_qr = get_text_from_blocks(blocks)
            qr_content = generate_questions_answers(text_for_qr)
            section = f"=== Page {page_title} ===\n{qr_content}\n"
            all_page_qr_sections.append(section)

    # 2. Générer Q/R global si au moins une page a été modifiée
    if all_page_qr_sections:
        current_date = datetime.now().strftime("%Y-%m-%d_%H-%M")
        qr_file = os.path.join(QR_DIR, f"QR_GLOBAL_Amadou_Mactar_{current_date}.docx")
        save_to_docx("\n\n".join(all_page_qr_sections), qr_file)
        print(f"✅ Q/R global créé : {qr_file}")

        # 3. Envoyer par mail CR + Q/R global
        send_email_with_latest_cours_and_qr()
    else:
        print("⚠️ Aucune modification détectée dans toutes les pages.")


if __name__ == "__main__":
    main()
