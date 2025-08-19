# extraction_notion_blocks_multi_pages.py
import os
from datetime import datetime,timezone
from notion_client import Client
from docx import Document
from dotenv import load_dotenv
from openai import OpenAI

# Charger variables d'environnement
load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
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
def get_last_export_time(page_id: str):
    """Lit le dernier export effectué pour une page (si existe)."""
    file = f"last_export_{page_id}.txt"
    if os.path.exists(file):
        with open(file, "r") as f:
            # toujours charger en UTC aware
            return datetime.fromisoformat(f.read().strip()).astimezone(timezone.utc)
    return None


def save_last_export_time(page_id: str):
    """Sauvegarde la date/heure du dernier export pour une page (UTC)."""
    file = f"last_export_{page_id}.txt"
    with open(file, "w") as f:
        f.write(datetime.now(timezone.utc).isoformat())

# --- Lister les pages accessibles ---
def get_page_title_from_info(page_info: dict):
    """
    Récupère le titre d'une page Notion depuis sa structure JSON.
    """
    title_property = page_info.get("properties", {}).get("title", {}).get("title", [])
    title_text = "".join([t.get("plain_text", "") for t in title_property])
    return title_text.replace(" ", "_") if title_text else "Sans_Titre"


def lister_pages_interessantes(titres_cibles=None):
    """
    Liste les pages accessibles.
    Retourne un dict {titre: id}.
    Si titres_cibles est fourni, filtre uniquement ces titres.
    """
    results = notion.search(filter={"property": "object", "value": "page"})
    mapping = {}

    for item in results["results"]:
        if item.get("object") == "page":
            title = get_page_title_from_info(item)
            if not titres_cibles or title in titres_cibles:
                mapping[title] = item["id"]

    return mapping


# --- Récupérer tous les blocs d'une page ---
def get_all_blocks(page_id: str):
    """Récupère récursivement tous les blocs d’une page Notion."""
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
def get_modified_blocks(page_id: str, since_time=None):
    blocks = get_all_blocks(page_id)
    if since_time:
        blocks = [
            b for b in blocks
            if datetime.fromisoformat(
                b["last_edited_time"].replace("Z", "+00:00")
            ).astimezone(timezone.utc) > since_time
        ]
    return blocks


# --- Récupérer le titre d'une page par son ID ---
def get_page_title(page_id: str):
    page_info = notion.pages.retrieve(page_id)
    title_property = page_info["properties"]["title"]["title"]
    return title_property[0]["plain_text"].replace(" ", "_") if title_property else "Sans_Titre"


# --- Extraire texte depuis un bloc ---
def extract_text_from_block(block: dict):
    """Extrait le texte d’un bloc Notion (selon son type)."""
    block_type = block["type"]
    text_elements = block.get(block_type, {}).get("rich_text", [])
    return "".join([t["text"]["content"] for t in text_elements if t["type"] == "text"])


# --- Concaténer texte des blocs ---
def get_text_from_blocks(blocks: list):
    """Concatène le texte de plusieurs blocs."""
    texts = []
    for block in blocks:
        text = extract_text_from_block(block)
        if text:
            texts.append(text)
    return "\n".join(texts)


# --- Générer Q/R avec ChatGPT ---
# def generate_questions_answers(text: str):
#     """Appelle OpenAI pour générer des QCM à partir du texte donné."""
#     prompt = f"""
# À partir du texte suivant, génère 10 questions à choix multiples avec leurs réponses correctes.
# Format :
# Q: ...
# A: ...

# Texte :
# {text}
# """
#     response = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[
#             {"role": "system", "content": "Tu es un générateur de quiz professionnel."},
#             {"role": "user", "content": prompt}
#         ]
#     )
#     return response.choices[0].message.content


# --- Sauvegarder Q/R ou texte dans Word ---
def save_to_docx(content: str, output_file: str):
    """Enregistre un texte brut dans un fichier Word (.docx)."""
    doc = Document()
    for line in content.split("\n"):
        doc.add_paragraph(line)
    doc.save(output_file)