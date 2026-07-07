# Jutarnji brief — AI pipeline za dnevni newsletter

Sve što je bitno iz Hrvatske i svijeta, u 5 minuta. Ovaj repo je stroj koji
svako jutro u ~5:00 pripremi draft izdanja; ti ga urediš i pošalješ prije 8:00.

## Kako radi

1. **Fetch** — povlači vijesti (zadnjih ~20 h) s RSS feedova iz `config/sources.yaml`,
   čisti ih i deduplicira.
2. **Draft** — Claude grupira priče, bira najvažnije po rubrikama i piše draft
   prema `config/style_guide.md`, uz B-listu preskočenih priča i 3 prijedloga
   subject linea.
3. **Deliver** — draft stiže mailom (+ opcionalno Telegram ping) i sprema se u `drafts/`.
4. **Ti** — 30–45 min uređivanja, paste u Beehiiv/Substack, send.

## Izbor "mozga" (3 opcije)

**Bitno:** Claude/ChatGPT pretplate NE uključuju API — API se plaća posebno,
po potrošnji (dnevni draft ≈ 0,10–0,20 € sa Sonnetom; jeftiniji modeli i manje).

| Mod | Env postavke | Trošak |
|---|---|---|
| Anthropic API | `DRAFT_PROVIDER=anthropic`, `ANTHROPIC_API_KEY` | ~4 €/mj |
| OpenAI / Gemini / Groq / DeepSeek | `DRAFT_PROVIDER=openai`, `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `DRAFT_MODEL` | Gemini flash: besplatni tier; ostali centi |
| **Manual (bez API-ja)** | ništa — pokreni `python run_daily.py --manual` | 0 € |

Manual mode: skripta složi kompletan prompt (vodič + očišćene vijesti) u
`drafts/DATUM-prompt.md`; ti ga zalijepiš u svoj claude.ai ili ChatGPT,
odgovor je tvoj draft. Koristi pretplate koje već plaćaš — košta te ~2 min
copy-pastea ujutro. Odličan način da kreneš danas, API dodaš kasnije.

Primjeri `OPENAI_BASE_URL` (svi su OpenAI-kompatibilni):
- Gemini: `https://generativelanguage.googleapis.com/v1beta/openai` (model npr. `gemini-2.0-flash`)
- Groq: `https://api.groq.com/openai/v1`
- DeepSeek: `https://api.deepseek.com/v1`

## Postavljanje (lokalno, ~10 min)

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...   # ili odaberi drugog providera (gore)

# 1. Provjeri feedove (neki RSS URL-ovi se mijenjaju — zamijeni neispravne!)
python run_daily.py --check-feeds

# 2. Probni draft bez slanja maila
python run_daily.py --dry-run
cat drafts/$(date +%F).md
```

## Automatika (GitHub Actions)

1. Pushaj repo na GitHub (može private).
2. U repo **Settings → Secrets and variables → Actions** dodaj:

| Secret | Što je |
|---|---|
| `ANTHROPIC_API_KEY` | ako koristiš Anthropic |
| `OPENAI_API_KEY` | ako koristiš OpenAI/Gemini/Groq/DeepSeek (uz repo *Variables*: `DRAFT_PROVIDER=openai`, `OPENAI_BASE_URL`, `DRAFT_MODEL`) |
| `SMTP_HOST` | npr. `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | tvoj Gmail |
| `SMTP_PASS` | Gmail **App Password** (ne obična lozinka — uključi 2FA pa Google Account → App passwords) |
| `EDITOR_EMAIL` | kamo stiže draft (može isti Gmail) |
| `TELEGRAM_BOT_TOKEN` | opcionalno (@BotFather) |
| `TELEGRAM_CHAT_ID` | opcionalno |

3. Testiraj ručno: **Actions → Jutarnji brief → Run workflow**.
4. Cron je postavljen na 05:00 zagrebačko ljetno vrijeme, pon–pet.
   Zimi promijeni `"0 3 * * 1-5"` u `"0 4 * * 1-5"` u `.github/workflows/daily.yml`.

## Dnevna rutina

- 5:00 — pipeline se sam pokrene, draft ti je u inboxu
- ujutro — uredi draft (kreni od subject linea!), swapaj priče s B-liste po potrebi,
  paste u Beehiiv, send do 8:00
- navečer/tjedno — svaku ispravku koju stalno ponavljaš pretvori u pravilo u
  `config/style_guide.md`; draftovi će konvergirati prema tvom glasu

## Degraded mode

Bolestan si / putuješ: `python run_daily.py --quick` (ili pokreni workflow ručno)
daje kraće izdanje. Navika izlaženja je najvrjednija imovina newslettera — nikad ne preskači.

## Važna pravila (pravna higijena)

- Sažetci su UVIJEK napisani vlastitim riječima + link na izvor. Nikad copy-paste iz članaka.
- Neprovjerene tvrdnje uvijek uz atribuciju ("prema pisanju X").
- Ovo je agregacija s atribucijom — normalan model. Prepisivanje nije.

## Web stranica (besplatno, GitHub Pages)

Stranica se generira iz `posts/` foldera — bez servera i bez troškova.

Dnevni tok: uredi draft → spremi ga kao `posts/GGGG-MM-DD.md` →
`python publish.py` → `git add . && git commit -m "izdanje" && git push`.
Generator sam izbacuje urednička poglavlja (SUBJECT PRIJEDLOZI, B-LISTA).

Jednokratno postavljanje:
1. Napravi GitHub račun i **javni** repo (Pages je besplatan samo za javne repoe),
   pushaj cijeli ovaj folder.
2. U repo **Settings → Pages**: Source = "Deploy from a branch",
   Branch = `main`, folder = `/docs` → Save.
3. Za ~1 min stranica je živa na `https://TVOJKORISNIK.github.io/IMEREPOA/`.
4. U `config/site.yaml` upiši naslov, tagline i tu adresu (`base_url`) pa
   ponovno pokreni `publish.py` — zbog RSS linkova.

Vlastita domena (~10 €/god) spaja se kasnije u istim Pages postavkama.

## Sljedeći koraci (nakon prvog tjedna)

- Beehiiv račun (besplatno do 2.500 pretplatnika) + landing stranica za prijave
- Referral program od prvog dana
- Nakon ~2.000 čitatelja: sponzorski slot u BIZNIS rubrici
