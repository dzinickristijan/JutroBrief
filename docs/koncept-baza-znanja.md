# Koncept: Baza Znanja

> **Status:** Koncept potvrđen — spreman za razvoj  
> **Datum:** 7. srpnja 2026.  
> **Aplikacija:** Baza Znanja  
> **Cilj:** Brži pristup provjerenim odgovorima na pitanja klijenata i rješenjima grešaka

---

## 1. Problem koji rješavamo

Referenti i knjigovođe svakodnevno odgovaraju na ista ili slična pitanja:
- greške u aplikacijama (ERP, eRačun, DMS, HR…)
- porezna i zakonska pitanja
- postupci (kako unijeti X, kako ispraviti Y)

Znanje je danas rasuto po e-mailovima, chatu, glavi pojedinih kolega i bilješkama.

**Posljedica:** Sporo pronalaženje odgovora, dupliciranje rada, ovisnost o pojedinim ljudima.

---

## 2. Rješenje

Centralizirana web aplikacija **Baza Znanja** gdje se:
1. **Unose** pitanja, odgovori i rješenja grešaka
2. **Odobravaju** prije objave (više urednika)
3. **Pretražuju** ključnim riječima i AI semantičkom pretragom (preko API-ja)
4. **Čitaju** interni tim i klijenti (klijenti samo čitanje)

---

## 3. Korisnici i uloge

| Uloga | Tko | Što može |
|-------|-----|----------|
| **Admin** | Vi (održavanje) | Korisnici, kategorije, postavke, odobravanje registracija |
| **Urednik** | Senior referenti (više njih) | Unos, uređivanje, odobravanje članaka |
| **Autor** | Referent / knjigovođa (~20) | Unos novih članaka (čeka odobrenje) |
| **Čitatelj (interni)** | Cijeli tim | Pretraga i čitanje |
| **Klijent** | Vanjski korisnik (10–150) | Samo pretraga i čitanje objavljenih članaka |

### Potvrđene odluke

| Pitanje | Odgovor |
|---------|---------|
| Broj referenata | ~20 |
| Broj klijenata | 10–150 (ovisno) |
| Pristup klijentima | Pozivnica **ili** registracija s odobrenjem admina |
| Vidljivost kategorija za klijente | Još nije definirano — ostaviti fleksibilno u adminu |
| Jezik | Samo hrvatski |
| Postojeći sadržaj za uvoz | Ne (za sada) |
| E-mail obavijesti | Ne (trenutno) |
| Održavanje | Vi osobno |
| Odobravanje | Više urednika |

### Registracija klijenata — dva načina

```
Način A: Pozivnica
  Admin šalje link → klijent se registrira → odmah aktivan

Način B: Samostalna registracija
  Klijent se registrira → status "čeka odobrenje" → admin odobri → aktivan
```

---

## 4. Aplikacije i kontekst (ne ERP po imenu)

**Zašto nije bitno kako se zove ERP:** aplikacija se ne veže uz jedan program. Umjesto toga, svaki članak ima polje **Aplikacija** — slobodan odabir ili tag:

- Računovodstvene aplikacije
- Knjigovodstvene aplikacije
- eRačun
- HR aplikacije
- DMS
- Excel predlošci
- Opće (bez vezane aplikacije)

To omogućuje filtriranje pretrage: *"Prikaži samo greške iz eRačuna"* — bez obzira kako se interni ERP točno zove.

---

## 5. Tipovi sadržaja (članaka)

### 5.1 Pitanje–odgovor (FAQ)
Pitanje, odgovor, vezana aplikacija, kategorija.

### 5.2 Rješenje greške
Poruka greške, uzrok, koraci rješenja, aplikacija.

### 5.3 Procedura / uputa
Naslov, koraci, napomene, rokovi.

### 5.4 Pravni / porezni podsjetnik
Tema, sažetak, detalji, izvor, datum valjanosti.

---

## 6. Ključne funkcionalnosti

### MVP

| Funkcija | Opis |
|----------|------|
| CRUD članaka | Kreiranje, uređivanje, brisanje |
| Workflow odobravanja | Nacrt → Na pregledu → Objavljeno / Odbijeno |
| Više urednika | Bilo koji urednik može odobriti |
| Kategorije i tagovi | Hijerarhija + slobodni tagovi |
| Povijest verzija | Tko je što mijenjao i kada |
| Full-text pretraga | SQL Server Full-Text Search |
| AI semantička pretraga | OpenAI API (embeddings) — bez lokalnog AI |
| Auth + uloge | Login, dozvole po ulozi |
| Klijentski pristup | Pozivnica ili registracija s odobrenjem |
| Filtar po aplikaciji | eRačun, DMS, HR, predlošci… |

### Faza 2

Prilozi (screenshot), povezani članci, statistika, "Je li ovo pomoglo?", ograničenje kategorija po ulozi, export PDF.

---

## 7. Workflow odobravanja

```
┌─────────┐    Pošalji     ┌──────────────┐   Odobri    ┌───────────┐
│  NACRT  │ ──────────────►│ NA PREGLEDU  │ ──────────► │ OBJAVLJENO│
│ (autor) │                │  (urednik)   │             │ (svi)     │
└─────────┘                └──────────────┘             └───────────┘
      ▲                            │
      │         Vrati na doradu    │
      └────────────────────────────┘
```

- Autor vidi svoje nacrte + sve objavljene
- Urednik vidi red čekanja ("Na pregledu")
- Klijenti vide samo objavljene članke
- Promjena objavljenog članka → nova verzija u povijesti

---

## 8. Pretraga — hibridni pristup

### 8.1 Ključna pretraga (SQL Server Full-Text)
- `CONTAINS` / `FREETEXT` na naslovu, pitanju, odgovoru
- Filtri: kategorija, tag, aplikacija, tip članka, datum
- Brzo, radi offline, bez vanjskog API-ja

### 8.2 AI semantička pretraga (API)
- Pri objavi članka: tekst se šalje na **OpenAI Embeddings API** → vektor se sprema u SQL Server
- Pri pretrazi: upit korisnika → embedding → cosine similarity s pohranjenim vektorima
- Korisnik upiše: *"ne mogu zatvoriti mjesec jer fale stavke"*
- Sustav pronađe: *"Greška pri zatvaranju — nedostaju knjiženja"*

> **Napomena o podacima:** Samo tekst članka ide na API za embedding. Nema osobnih podataka klijenata. API ključ se drži u `.env` na serveru.

### 8.3 Arhitektura pretrage

```
Upit korisnika
     │
     ├──► SQL Server Full-Text (CONTAINS)
     │         └── rezultati A
     │
     └──► OpenAI Embeddings API
               └── cosine similarity u aplikaciji
               └── rezultati B
     │
     ▼
Merge + ranking → prikaz korisniku
```

**Fallback:** Ako API nije dostupan, pretraga radi samo full-text — aplikacija i dalje funkcionira.

---

## 9. Tehnička arhitektura

### Stack

| Sloj | Tehnologija | Zašto |
|------|-------------|-------|
| Frontend | **Next.js 15** (React, TypeScript) | Moderan, brz, dobar za interne alate |
| Backend | **Next.js API routes** | Jedan projekt, jednostavno održavanje |
| Baza | **SQL Server** (postojeći server) | Već imate infrastrukturu |
| ORM | **Prisma** ili **Drizzle** | Type-safe pristup SQL Serveru |
| Auth | **NextAuth.js** (Credentials + JWT) | Login, uloge, sesije |
| AI embeddings | **OpenAI API** (`text-embedding-3-small`) | Bez lokalnog GPU, jednostavna integracija |
| File storage | Lokalni disk na serveru | Screenshoti (Faza 2) |
| Reverse proxy | **IIS** ili **Nginx** | HTTPS na postojećem serveru |
| Deploy | **Node.js** na Windows Serveru ili Docker | Ovisno o vašem okruženju |

### Infrastruktura

```
┌──────────────────────────────────────────────────────┐
│                 Vaš server (postojeći)                │
│                                                       │
│  ┌──────────┐   ┌─────────────┐   ┌──────────────┐ │
│  │ IIS/Nginx│──►│  Baza       │──►│ SQL Server   │ │
│  │ (HTTPS)  │   │  Znanja     │   │ (postojeći)  │ │
│  │          │   │  (Next.js)  │   │ + Full-Text  │ │
│  └──────────┘   └──────┬──────┘   └──────────────┘ │
│                        │                              │
│                        │ embeddings (samo pri objavi  │
│                        │ i pretrazi)                   │
└────────────────────────┼──────────────────────────────┘
                         ▼
                  ┌─────────────┐
                  │ OpenAI API  │  (internet)
                  │ embeddings  │
                  └─────────────┘

Pristup: https://baza-znanja.vasa-firma.local
```

### Zašto SQL Server (a ne PostgreSQL)

- Već imate SQL Server — nema nove infrastrukture
- Full-Text Search ugrađen
- Embeddings se pohranjuju kao `NVARCHAR(MAX)` (JSON niz floatova) — similarity se računa u Node.js
- Backup i održavanje već znate
- Prisma/Drizzle dobro podržavaju SQL Server

---

## 10. Model podataka (SQL Server)

```sql
-- Korisnici
CREATE TABLE Users (
    Id            UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    Email         NVARCHAR(255) NOT NULL UNIQUE,
    Name          NVARCHAR(200) NOT NULL,
    PasswordHash  NVARCHAR(500) NOT NULL,
    Role          NVARCHAR(20) NOT NULL,  -- admin | editor | author | reader | client
    ClientId      UNIQUEIDENTIFIER NULL,  -- za klijente: vezano na tvrtku
    IsActive      BIT NOT NULL DEFAULT 0,
    CreatedAt     DATETIME2 NOT NULL DEFAULT GETUTCDATE()
);

-- Klijenti (tvrtke koje opslužujete)
CREATE TABLE Clients (
    Id      UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    Name    NVARCHAR(300) NOT NULL,
    Oib     NVARCHAR(11) NULL,
    Active  BIT NOT NULL DEFAULT 1
);

-- Pozivnice
CREATE TABLE Invitations (
    Id        UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    Email     NVARCHAR(255) NOT NULL,
    Token     NVARCHAR(100) NOT NULL UNIQUE,
    Role      NVARCHAR(20) NOT NULL DEFAULT 'client',
    ClientId  UNIQUEIDENTIFIER NULL,
    ExpiresAt DATETIME2 NOT NULL,
    UsedAt    DATETIME2 NULL
);

-- Kategorije (hijerarhija)
CREATE TABLE Categories (
    Id        UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    Name      NVARCHAR(200) NOT NULL,
    ParentId  UNIQUEIDENTIFIER NULL REFERENCES Categories(Id),
    SortOrder INT NOT NULL DEFAULT 0
);

-- Aplikacije (eRačun, DMS, HR, predlošci…)
CREATE TABLE Applications (
    Id   UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    Name NVARCHAR(200) NOT NULL UNIQUE
);

-- Članci
CREATE TABLE Articles (
    Id           UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    Type         NVARCHAR(20) NOT NULL,  -- faq | error | procedure | legal
    Title        NVARCHAR(500) NOT NULL,
    Question     NVARCHAR(MAX) NULL,
    Answer       NVARCHAR(MAX) NULL,
    ErrorMessage NVARCHAR(MAX) NULL,
    Cause        NVARCHAR(MAX) NULL,
    Solution     NVARCHAR(MAX) NULL,
    Steps        NVARCHAR(MAX) NULL,
    Status       NVARCHAR(20) NOT NULL DEFAULT 'draft',
    CategoryId   UNIQUEIDENTIFIER NULL REFERENCES Categories(Id),
    ApplicationId UNIQUEIDENTIFIER NULL REFERENCES Applications(Id),
    AuthorId     UNIQUEIDENTIFIER NOT NULL REFERENCES Users(Id),
    ReviewerId   UNIQUEIDENTIFIER NULL REFERENCES Users(Id),
    ReviewNote   NVARCHAR(MAX) NULL,
    PublishedAt  DATETIME2 NULL,
    CreatedAt    DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    UpdatedAt    DATETIME2 NOT NULL DEFAULT GETUTCDATE()
);

-- Full-Text indeks na Articles (Title, Question, Answer, Solution, Steps)

-- Tagovi
CREATE TABLE Tags (
    Id   UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    Name NVARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE ArticleTags (
    ArticleId UNIQUEIDENTIFIER NOT NULL REFERENCES Articles(Id),
    TagId     UNIQUEIDENTIFIER NOT NULL REFERENCES Tags(Id),
    PRIMARY KEY (ArticleId, TagId)
);

-- Verzije
CREATE TABLE ArticleVersions (
    Id            UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    ArticleId     UNIQUEIDENTIFIER NOT NULL REFERENCES Articles(Id),
    VersionNumber INT NOT NULL,
    SnapshotJson  NVARCHAR(MAX) NOT NULL,
    ChangedById   UNIQUEIDENTIFIER NOT NULL REFERENCES Users(Id),
    ChangeNote    NVARCHAR(500) NULL,
    ChangedAt     DATETIME2 NOT NULL DEFAULT GETUTCDATE()
);

-- AI embeddings (JSON niz floatova)
CREATE TABLE ArticleEmbeddings (
    ArticleId  UNIQUEIDENTIFIER PRIMARY KEY REFERENCES Articles(Id),
    Embedding  NVARCHAR(MAX) NOT NULL,
    UpdatedAt  DATETIME2 NOT NULL DEFAULT GETUTCDATE()
);

-- Audit log
CREATE TABLE AuditLog (
    Id        UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    UserId    UNIQUEIDENTIFIER NULL REFERENCES Users(Id),
    Action    NVARCHAR(50) NOT NULL,
    Entity    NVARCHAR(50) NOT NULL,
    EntityId  UNIQUEIDENTIFIER NULL,
    Details   NVARCHAR(MAX) NULL,
    Timestamp DATETIME2 NOT NULL DEFAULT GETUTCDATE()
);
```

---

## 11. Korisničko sučelje

| Ekran | Opis |
|-------|------|
| **Početna** | Veliko polje za pretragu, filteri (kategorija, aplikacija, tip), nedavno dodano |
| **Rezultati** | Lista s relevance score, badgeovi, highlight |
| **Članak** | Puni prikaz, tagovi, povezani članci, povijest verzija (urednici) |
| **Novi članak** | Wizard po tipu, rich text, odabir aplikacije i kategorije |
| **Red čekanja** | Urednik: lista na pregledu, odobri / vrati / odbij |
| **Admin** | Korisnici, pozivnice, registracije na čekanju, kategorije, aplikacije |

Dizajn: čist, profesionalan, hrvatski jezik, responzivno (mobitel u pregledniku).

---

## 12. Plan razvoja u Cursoru

### Faza 0 — Priprema (1 dan)
- [x] Koncept i odluke potvrđene
- [ ] Novi projekt: `baza-znanja`
- [ ] Next.js 15 + TypeScript + Tailwind
- [ ] Prisma + SQL Server connection
- [ ] `.cursor/rules/` za projektni kontekst
- [ ] `.env.example` s varijablama

### Faza 1 — Backend + baza (3–4 dana)
- [ ] SQL migracije (tablice iz §10)
- [ ] Full-Text indeks na Articles
- [ ] Auth (NextAuth, uloge)
- [ ] CRUD API za članke
- [ ] Workflow statusa
- [ ] Seed: admin korisnik, osnovne kategorije i aplikacije

### Faza 2 — Frontend MVP (3–4 dana)
- [ ] Login
- [ ] Pretraga + rezultati (full-text)
- [ ] Prikaz članka
- [ ] Forma za unos/uređivanje
- [ ] Red čekanja za urednike

### Faza 3 — AI pretraga + verzije (2 dana)
- [ ] OpenAI embeddings pipeline (pri objavi)
- [ ] Semantička pretraga u API-ju
- [ ] Povijest verzija

### Faza 4 — Klijenti + admin (2 dana)
- [ ] Pozivnice (generiranje linka, registracija)
- [ ] Registracija s odobrenjem
- [ ] Admin panel (korisnici, kategorije, aplikacije)

### Faza 5 — Deploy (1 dan)
- [ ] Build na serveru
- [ ] IIS / Nginx reverse proxy
- [ ] HTTPS certifikat
- [ ] Backup procedure

**Ukupno procjena:** 2–3 tjedna (part-time)

---

## 13. Kako pokrenuti u Cursoru

### Korak 1 — Novi projekt
```
File → New Window → Create new project
Naziv: baza-znanja
Lokacija: npr. C:\Projects\baza-znanja
```

### Korak 2 — Cursor Rule
Kreirati `.cursor/rules/project-context.mdc`:

```markdown
---
description: Kontekst projekta Baza Znanja
alwaysApply: true
---

# Baza Znanja — projektni kontekst

Interna Q&A baza znanja za računovodstvenu firmu (~20 referenata, 10–150 klijenata).

- Naziv aplikacije: Baza Znanja
- Jezik UI: hrvatski
- Korisnici: interni (pisanje) + klijenti (samo čitanje)
- Klijenti: pozivnica ili registracija s odobrenjem
- Hosting: on-premise, postojeći SQL Server
- Stack: Next.js 15, TypeScript, Prisma, SQL Server, NextAuth
- Pretraga: SQL Server Full-Text + OpenAI embeddings API
- Workflow: nacrt → pregled → objava (više urednika)
- Tipovi članaka: faq, error, procedure, legal
- Aplikacije: generičko polje (eRačun, DMS, HR, predlošci…)
- Nema e-mail obavijesti u MVP-u
```

### Korak 3 — Prvi prompt u Cursoru
```
Pročitaj docs/koncept-baza-znanja.md i započni Fazu 0:

1. Inicijaliziraj Next.js 15 projekt (TypeScript, Tailwind, App Router)
2. Dodaj Prisma s SQL Server providerom
3. Kreiraj prisma/schema.prisma prema modelu iz koncepta (§10)
4. Postavi NextAuth s Credentials providerom i ulogama
5. Napravi osnovnu strukturu: src/app, src/lib, src/components
6. Dodaj .env.example s DATABASE_URL, NEXTAUTH_SECRET, OPENAI_API_KEY
```

---

## 14. Sažetak svih odluka

| Odluka | Vrijednost |
|--------|------------|
| Naziv aplikacije | **Baza Znanja** |
| Korisnici | ~20 referenata + 10–150 klijenata |
| Klijenti | Pozivnica ili registracija s odobrenjem |
| Vidljivost kategorija | Fleksibilno — definirati kasnije u adminu |
| Jezik | Hrvatski |
| Baza | **SQL Server** (postojeći server) |
| Hosting | On-premise |
| Pretraga | Full-Text + OpenAI API embeddings |
| AI | API (ne lokalno) |
| Odobravanje | Više urednika |
| Obavijesti | Ne (trenutno) |
| Održavanje | Vi osobno |
| Postojeći sadržaj | Nema (za sada) |
| Aplikacije | eRačun, DMS, HR, predlošci, računovodstvo, knjigovodstvo |
| MVP | CRUD + workflow + kategorije/tagovi + verzije + pretraga |

---

## 15. Otvoreno za kasnije

- Koje kategorije klijenti smiju vidjeti
- Uvoz postojećeg sadržaja (Word, Excel)
- E-mail obavijesti
- Prilozi (screenshot grešaka)
- Integracija s DMS-om

---

*Koncept je potpun. Sljedeći korak: kreirati projekt `baza-znanja` i pokrenuti Fazu 0.*
