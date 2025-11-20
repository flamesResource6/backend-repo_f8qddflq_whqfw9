import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from database import db, create_document, get_documents
from bson import ObjectId

app = FastAPI(title="Bible API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Utility ----------

def to_json(doc: Dict[str, Any]):
    if not doc:
        return doc
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    # convert datetime
    for k, v in list(doc.items()):
        if hasattr(v, "isoformat"):
            doc[k] = v.isoformat()
    return doc

# ---------- Models for simple endpoints ----------

class SearchQuery(BaseModel):
    q: str
    translation: Optional[str] = None
    language: Optional[str] = None
    limit: int = 20

class VoiceSearchQuery(BaseModel):
    transcript: str
    translation: Optional[str] = None

class ReferenceRequest(BaseModel):
    reference: str
    translation: str = "ESV"

class CreateHighlight(BaseModel):
    user_id: str
    reference: str
    translation: str
    color: str = "yellow"
    note: Optional[str] = None

class CreateBookmark(BaseModel):
    user_id: str
    reference: str
    translation: str
    label: Optional[str] = None

class CreateNote(BaseModel):
    user_id: str
    reference: str
    translation: str
    content: str

class CreatePlaylist(BaseModel):
    user_id: str
    title: str
    mood: Optional[str] = None
    theme: Optional[str] = None
    references: List[str] = []

# ---------- Core Routes (MVP scaffolding) ----------

@app.get("/")
def read_root():
    return {"service": "Bible Backend", "status": "ok"}

@app.get("/test")
def test_database():
    status = {
        "backend": "running",
        "database": "not_connected",
        "collections": [],
    }
    try:
        if db is not None:
            status["database"] = "connected"
            status["collections"] = db.list_collection_names()
    except Exception as e:
        status["database_error"] = str(e)
    return status

# Simulated Bible text store note:
# In a production app, we'd store canonical verse texts and audio timing maps.
# For this MVP scaffold, provide a tiny in-app sample and structure endpoints to be expanded.

SAMPLE_TEXTS = {
    "ESV": {
        "John 3:16": "For God so loved the world, that he gave his only Son, that whoever believes in him should not perish but have eternal life.",
        "Psalm 23:1": "The Lord is my shepherd; I shall not want.",
    },
    "NIV": {
        "John 3:16": "For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life.",
        "Psalm 23:1": "The Lord is my shepherd, I lack nothing.",
    },
}

AUDIO_SYNC = {
    # verse -> list of word timings (seconds)
    "John 3:16": [0.0, 0.5, 0.8, 1.1, 1.6, 2.1, 2.5, 2.9, 3.4, 3.8, 4.3, 4.8, 5.2, 5.7, 6.3],
}

@app.get("/api/translations")
def get_translations():
    return ["ESV", "NIV"]

@app.get("/api/languages")
def get_languages():
    return ["en"]

@app.get("/api/verse")
def get_verse(reference: str, translation: str = "ESV"):
    text = SAMPLE_TEXTS.get(translation, {}).get(reference)
    if not text:
        raise HTTPException(status_code=404, detail="Verse not found in sample dataset")
    return {"reference": reference, "translation": translation, "text": text}

@app.get("/api/parallel")
def get_parallel(reference: str, translations: str = "ESV,NIV"):
    results = []
    for t in translations.split(","):
        t = t.strip()
        verse = SAMPLE_TEXTS.get(t, {}).get(reference)
        if verse:
            results.append({"translation": t, "text": verse})
    if not results:
        raise HTTPException(status_code=404, detail="Reference not found")
    return {"reference": reference, "items": results}

@app.post("/api/search")
def search_verses(payload: SearchQuery):
    q = payload.q.lower()
    results = []
    translations = [payload.translation] if payload.translation else list(SAMPLE_TEXTS.keys())
    for t in translations:
        for ref, txt in SAMPLE_TEXTS.get(t, {}).items():
            if q in txt.lower():
                results.append({"reference": ref, "translation": t, "snippet": txt[:160]})
    return results[: payload.limit]

@app.post("/api/voice-search")
def voice_search(payload: VoiceSearchQuery):
    return search_verses(SearchQuery(q=payload.transcript, translation=payload.translation))

@app.get("/api/audio")
def audio_for_reference(reference: str, translation: str = "ESV"):
    # Return a placeholder audio URL and timing map
    return {
        "reference": reference,
        "translation": translation,
        "audio_url": f"https://cdn.example.com/audio/{translation}/{reference.replace(' ', '_')}.mp3",
        "timings": AUDIO_SYNC.get(reference, []),
    }

# ---------- User data (Mongo-backed) ----------

@app.post("/api/highlights")
def create_highlight(payload: CreateHighlight):
    from schemas import Highlight
    doc_id = create_document("highlight", Highlight(**payload.model_dump()))
    return {"id": doc_id}

@app.get("/api/highlights")
def list_highlights(user_id: str):
    docs = get_documents("highlight", {"user_id": user_id})
    return [to_json(d) for d in docs]

@app.post("/api/bookmarks")
def create_bookmark(payload: CreateBookmark):
    from schemas import Bookmark
    doc_id = create_document("bookmark", Bookmark(**payload.model_dump()))
    return {"id": doc_id}

@app.get("/api/bookmarks")
def list_bookmarks(user_id: str):
    docs = get_documents("bookmark", {"user_id": user_id})
    return [to_json(d) for d in docs]

@app.post("/api/notes")
def create_note(payload: CreateNote):
    from schemas import Note
    doc_id = create_document("note", Note(**payload.model_dump()))
    return {"id": doc_id}

@app.get("/api/notes")
def list_notes(user_id: str, reference: Optional[str] = None):
    query = {"user_id": user_id}
    if reference:
        query["reference"] = reference
    docs = get_documents("note", query)
    return [to_json(d) for d in docs]

@app.post("/api/playlists")
def create_playlist(payload: CreatePlaylist):
    from schemas import VersePlaylist
    doc_id = create_document("verseplaylist", VersePlaylist(**payload.model_dump()))
    return {"id": doc_id}

@app.get("/api/playlists")
def list_playlists(user_id: str):
    docs = get_documents("verseplaylist", {"user_id": user_id})
    return [to_json(d) for d in docs]

# ---------- Smart recommendations (placeholder logic) ----------

@app.get("/api/recommendations")
def get_recommendations(user_id: str, based_on: str = "Psalms"):
    # Simple demo: return common comforting verses
    items = [
        {"reference": "Psalm 23:1", "reason": "Because you read Psalms"},
        {"reference": "John 3:16", "reason": "Popular across themes"},
    ]
    return items

# ---------- Study tools (stubs for UI) ----------

@app.get("/api/crossrefs")
def cross_references(reference: str):
    data = {
        "John 3:16": ["Romans 5:8", "1 John 4:9"],
        "Psalm 23:1": ["John 10:11", "Ezekiel 34:11"],
    }
    return {"reference": reference, "cross_references": data.get(reference, [])}

@app.get("/api/commentary")
def commentary(reference: str):
    return {"reference": reference, "commentary": "Sample commentary for study. Expand with real sources."}

@app.get("/api/maps")
def maps(reference: str):
    return {"reference": reference, "places": ["Jerusalem", "Nazareth"]}

@app.get("/api/timelines")
def timelines(reference: str):
    return {"reference": reference, "events": ["Birth of Jesus", "Ministry in Galilee"]}

# ---------- AI features (optional stubs) ----------

class AIRequest(BaseModel):
    reference: Optional[str] = None
    chapter: Optional[str] = None
    prompt: Optional[str] = None

@app.post("/api/ai/explain")
def ai_explain(payload: AIRequest):
    # Placeholder deterministic text to avoid external dependency
    target = payload.reference or payload.chapter or "the verse"
    return {"explanation": f"Here's a concise explanation of {target} providing historical and theological context."}

@app.post("/api/ai/summary")
def ai_summary(payload: AIRequest):
    target = payload.chapter or payload.reference or "the passage"
    return {"summary": f"This summary captures the main themes and structure of {target}."}

@app.post("/api/ai/devotional")
def ai_devotional(payload: AIRequest):
    target = payload.reference or payload.chapter or "today's reading"
    return {"devotional": f"A short devotional for {target}, ending with an applicable prayer."}

@app.post("/api/ai/prayer")
def ai_prayer(payload: AIRequest):
    return {"prayer": "Personalized prayer prompt: Take a deep breath, be still, and bring your concerns before God."}

