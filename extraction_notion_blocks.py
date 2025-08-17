# extraction_notion_blocks_multi_pages.py
import os
from datetime import datetime
from notion_client import Client
from docx import Document
from dotenv import load_dotenv
from openai import OpenAI
#from dateutil import parser

# Charger variables d'environnement
load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_PAGE_IDS = os.getenv("NOTION_PAGE_IDS", "").split(",")  # liste séparée par virgules
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


# --- Gestion du timestamp d’export (par page) ---
def get_last_export_time(page_id):
    file = f"last_export_{page_id}.txt"
    if os.path.exists(file):
        with open(file, "r") as f:
            return datetime.fromisoformat(f.read().strip())
    return None


def save_last_export_time(page_id):
    file = f"last_export_{page_id}.txt"
    with open(file, "w") as f:
        f.write(datetime.now().isoformat())


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


# --- Filtrer seulement les blocs modifiés ---
from datetime import datetime

def get_modified_blocks(page_id, since_time=None):
    blocks = get_all_blocks(page_id)
    if since_time:
        # Convertir le timestamp ISO 8601 en datetime
        blocks = [
            b for b in blocks
            if datetime.fromisoformat(b["last_edited_time"].replace("Z", "+00:00")) > since_time
        ]
    return blocks


# --- Récupérer le titre de la page ---
def get_page_title(page_id):
    page_info = notion.pages.retrieve(page_id)
    title_property = page_info["properties"]["title"]["title"]
    return title_property[0]["plain_text"].replace(" ", "_") if title_property else "Sans_Titre"


# --- Extraire texte depuis un bloc Notion ---
def extract_text_from_block(block):
    block_type = block["type"]
    text_elements = block.get(block_type, {}).get("rich_text", [])
    return "".join([t["text"]["content"] for t in text_elements if t["type"] == "text"])


# --- Concaténer texte des blocs ---
def get_text_from_blocks(blocks):
    texts = []
    for block in blocks:
        text = extract_text_from_block(block)
        if text:
            texts.append(text)
    return "\n".join(texts)


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

