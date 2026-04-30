from fastapi import APIRouter, HTTPException

router = APIRouter()

TRANSLATIONS = {
    "en": {
        "summary_label": "Summary",
        "view_summary": "View Summary",
        "view_full": "View Full",
        "generating_summary": "Generating summary...",
    },
    "mr": {
        "summary_label": "संक्षिप्त माहिती",
        "view_summary": "सारांश पहा",
        "view_full": "पूर्ण तपशील पहा",
        "generating_summary": "सारांश तयार होत आहे...",
    },
    "hi": {
        "summary_label": "संक्षिप्त जानकारी",
        "view_summary": "सारांश देखें",
        "view_full": "पूरा विवरण देखें",
        "generating_summary": "सारांश तैयार हो रहा है...",
    },
}


@router.get("/{lang}")
def get_translations(lang: str):
    lang = (lang or "en").lower()
    if lang not in TRANSLATIONS:
        raise HTTPException(status_code=404, detail=f"Translations not found for language '{lang}'")
    return {"success": True, "data": TRANSLATIONS[lang], "lang": lang}

