# extraction_notion_blocks.py
import os
from datetime import datetime
from notion_client import Client
from docx import Document
from dotenv import load_dotenv
from openai import OpenAI

# Charger variables d'environnement
load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./rapports")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Sous-dossiers
COURS_DIR = os.path.join(OUTPUT_DIR, "cours")
QR_DIR = os.path.join(OUTPUT_DIR, "qr")
os.makedirs(COURS_DIR, exist_ok=True)
os.makedirs(QR_DIR, exist_ok=True)

# Clients API
notion = Client(auth=NOTION_TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)


# --- Récupérer tous les blocs d'une page Notion ---
def get_all_blocks(page_id):
    blocks = []
    cursor = None

    while True:
        response = notion.blocks.children.list(
            block_id=page_id,
            start_cursor=cursor
        )
        blocks.extend(response["results"])
        cursor = response.get("next_cursor")
        if not cursor:
            break

    return blocks


# --- Récupérer le titre de la page ---
def get_page_title():
    page_info = notion.pages.retrieve(NOTION_PAGE_ID)
    title_property = page_info["properties"]["title"]["title"]
    return title_property[0]["plain_text"].replace(" ", "_") if title_property else "Sans_Titre"


# --- Extraire texte depuis un bloc Notion ---
def extract_text_from_block(block):
    block_type = block["type"]
    text_elements = block.get(block_type, {}).get("rich_text", [])
    return "".join([t["text"]["content"] for t in text_elements if t["type"] == "text"])


# --- Exporter Notion vers Word ---
def export_notion_to_word():
    page_title = get_page_title()
    current_date = datetime.now().strftime("%Y-%m-%d_%H-%M")
    output_file = os.path.join(COURS_DIR, f"CR_{page_title}_Amadou_Mactar_{current_date}.docx")

    blocks = get_all_blocks(NOTION_PAGE_ID)

    document = Document()
    for block in blocks:
        text = extract_text_from_block(block)
        if not text:
            continue
        if block["type"] == "heading_1":
            document.add_heading(text, level=1)
        elif block["type"] == "heading_2":
            document.add_heading(text, level=2)
        elif block["type"] == "heading_3":
            document.add_heading(text, level=3)
        elif block["type"] == "to_do":
            document.add_paragraph(f"☐ {text}")
        elif block["type"] == "bulleted_list_item":
            document.add_paragraph(f"• {text}")
        elif block["type"] == "numbered_list_item":
            document.add_paragraph(f"1. {text}")
        else:
            document.add_paragraph(text)

    document.save(output_file)
    print(f"✅ Cours exporté : {output_file}")
    return output_file


# --- Lire texte d'un Word ---
def extract_text_from_docx(file_path):
    doc = Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])


# --- Générer Q/R avec ChatGPT ---
def generate_questions_answers(text):
    prompt = f"""
À partir du texte suivant, génère 10 questions à choix multiples avec leurs réponses correctes.
Format :
Q: ...
A: ...

Texte :
{text}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Tu es un générateur de quiz professionnel."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


# --- Sauvegarder Q/R dans Word ---
def save_to_docx(content, output_file):
    doc = Document()
    for line in content.split("\n"):
        doc.add_paragraph(line)
    doc.save(output_file)
