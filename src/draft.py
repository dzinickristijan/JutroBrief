"""Turn fetched news items into a newsletter draft.

Providers (env var DRAFT_PROVIDER):
  anthropic  — Anthropic API (ANTHROPIC_API_KEY)
  openai     — OpenAI ili bilo koji OpenAI-kompatibilan API:
               Gemini, Groq, DeepSeek... (OPENAI_API_KEY, opcionalno OPENAI_BASE_URL)
  manual     — bez API-ja: generira prompt file koji zalijepiš u claude.ai / ChatGPT

Model se bira kroz DRAFT_MODEL (default ovisi o provideru).
"""

import os
import json
import urllib.request
from datetime import datetime

PROVIDER = os.environ.get("DRAFT_PROVIDER", "anthropic").lower()

DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-4o-mini",
}

MAX_ITEMS = 120  # hard cap on how many items we show the model

SYSTEM_PROMPT = """Ti si urednik hrvatskog jutarnjeg newslettera. Pišeš ISKLJUČIVO na hrvatskom.

Tvoj zadatak:
1. Grupiraj vijesti koje pokrivaju istu priču (različiti portali, ista vijest = jedna stavka).
2. Odaberi najvažnije priče po rubrikama prema stilskom vodiču.
3. Napiši kompletan draft izdanja u Markdownu, točno po strukturi iz vodiča.
4. Nakon drafta dodaj sekciju "## B-LISTA" s 5–10 priča koje NISI uvrstio
   (samo naslov + link), da urednik može lako zamijeniti.
5. Na samom početku predloži 3 subject linea pod "## SUBJECT PRIJEDLOZI".

Stroga pravila:
- Svaki sažetak piši SVOJIM riječima — nikad ne kopiraj rečenice iz izvora.
- Svaka vijest završava linkom: [Izvor](url) — koristi točan link iz podataka.
- Ako za neku rubriku nema dovoljno kvalitetnih vijesti, bolje manje nego punjenje.
- Ne izmišljaj činjenice koje nisu u dostavljenim podacima. Ako je nešto nejasno,
  formuliraj oprezno ("prema pisanju X").
"""


def _load_style_guide(path: str = "config/style_guide.md") -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _items_block(items: list[dict]) -> str:
    lines = []
    for i, it in enumerate(items[:MAX_ITEMS]):
        lines.append(
            json.dumps(
                {
                    "id": i,
                    "izvor": it["source"],
                    "rubrika_hint": it["section_hint"],
                    "naslov": it["title"],
                    "sazetak": it["summary"][:300],
                    "link": it["link"],
                },
                ensure_ascii=False,
            )
        )
    return "\n".join(lines)


def _user_prompt(items: list[dict]) -> str:
    today = datetime.now().strftime("%A, %d.%m.%Y.")
    return (
        f"Današnji datum: {today}\n\n"
        f"=== STILSKI VODIČ ===\n{_load_style_guide()}\n\n"
        f"=== VIJESTI (JSON, jedna po retku) ===\n{_items_block(items)}\n\n"
        "Napiši draft današnjeg izdanja."
    )


# ---------------------------------------------------------------- providers

def _draft_anthropic(prompt: str) -> str:
    import anthropic

    client = anthropic.Anthropic()  # ANTHROPIC_API_KEY iz okoline
    response = client.messages.create(
        model=os.environ.get("DRAFT_MODEL", DEFAULT_MODELS["anthropic"]),
        max_tokens=6000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in response.content if b.type == "text")


def _draft_openai_compatible(prompt: str) -> str:
    """OpenAI ili bilo koji OpenAI-kompatibilan endpoint (Gemini, Groq, DeepSeek...).

    Env:
      OPENAI_API_KEY   — ključ providera
      OPENAI_BASE_URL  — opcionalno; primjeri:
        OpenAI    (default)  https://api.openai.com/v1
        Gemini               https://generativelanguage.googleapis.com/v1beta/openai
        Groq                 https://api.groq.com/openai/v1
        DeepSeek             https://api.deepseek.com/v1
      DRAFT_MODEL      — npr. gpt-4o-mini / gemini-2.0-flash / llama-3.3-70b-versatile
    """
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    key = os.environ["OPENAI_API_KEY"]
    model = os.environ.get("DRAFT_MODEL", DEFAULT_MODELS["openai"])

    body = json.dumps(
        {
            "model": model,
            "max_tokens": 6000,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        }
    ).encode()

    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode())
    return data["choices"][0]["message"]["content"]


def write_manual_prompt(items: list[dict], out_dir: str = "drafts") -> str:
    """Manual mode: spremi kompletan prompt u file za copy-paste u claude.ai / ChatGPT."""
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{datetime.now():%Y-%m-%d}-prompt.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(SYSTEM_PROMPT + "\n\n" + _user_prompt(items))
    return path


def draft_issue(items: list[dict]) -> str:
    prompt = _user_prompt(items)
    if PROVIDER == "anthropic":
        return _draft_anthropic(prompt)
    if PROVIDER == "openai":
        return _draft_openai_compatible(prompt)
    raise ValueError(
        f"Nepoznat DRAFT_PROVIDER='{PROVIDER}'. Opcije: anthropic, openai "
        "(za manual mode pokreni: python run_daily.py --manual)"
    )
