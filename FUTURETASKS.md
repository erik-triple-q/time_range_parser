# Business Plan & MVP Strategie: Date Parser MCP

## 1. Executive Summary

**Date Parser MCP** is een gespecialiseerde middleware-service die natuurlijke taal (NL/EN) deterministisch omzet naar gestructureerde ISO-8601 tijdreeksen. Het lost een fundamenteel probleem op in AI-pipelines: het gebrek aan nauwkeurig en consistent tijdsbesef bij LLM's. Dit plan beschrijft de strategie om de huidige codebase om te zetten naar een marktklaar Minimum Viable Product (MVP), met een primaire focus op **Text-to-SQL** en **Business Intelligence** toepassingen.

## 2. Probleemstelling & Marktanalyse

### Het Probleem

- **LLM Hallucinaties:** Modellen zoals Claude en GPT maken rekenfouten met datums (bijv. "wat was de datum 3 weken geleden?").
- **Gebrek aan Determinisme:** "Vorige maand" betekent vandaag iets anders dan morgen. Voor regressietests en SQL-queries is een vaste referentietijd cruciaal.
- **Huidig Aanbod:**
  - _Basic Time Servers:_ Bieden vaak alleen `now()` en missen taalkundig inzicht.
  - _Agenda Tools (Google Calendar):_ Te zwaar en gekoppeld aan externe accounts; niet bruikbaar als pure rekenmachine.
  - _Code Sandboxes:_ Trager, complexer in setup en veiligheidsrisico's.

### De Oplossing

Een **standalone, stateless MCP-server** die fungeert als de autoriteit voor tijd-interpretatie.

## 3. Waardepropositie (USP)

1.  **Deterministisch:** Garandeert consistente output voor SQL-generatie door vaste referentietijden (`now` injectie).
2.  **Zakelijke Intelligentie:** Native begrip van kwartalen (`Q3`), semesters (`H1`), en weeknummers (`week 42`).
3.  **Bilingual & Lokaal:** Volledige ondersteuning voor Nederlandse spreektaal ("overmorgen", "half 3") en feestdagen, uniek in het huidige aanbod.

## 4. Doelgroep

1.  **AI Engineers (Text-to-SQL):** Ontwikkelaars die agents bouwen die databases bevragen. Zij hebben exacte `BETWEEN 'start' AND 'end'` waarden nodig.
2.  **Enterprise Chatbot Developers:** Voor klantenservice in de Benelux (bijv. "status van mijn bestelling van eergisteren").
3.  **Data Analisten:** Voor het automatiseren van rapportages op basis van vage tijdsaanduidingen.

## 5. MVP Scope (Minimum Viable Product)

De MVP is gedefinieerd als een stabiele v1.0 release die direct inzetbaar is in productie-pipelines.

### Kernfunctionaliteit (Must-Haves)

- [x] **Natuurlijke Taal Parsing:** Ondersteuning voor relatieve dagen, specifieke datums en tijdstippen (NL/EN).
- [x] **Business Logica:** Kwartalen, semesters, weeknummers.
- [x] **Range Resolutie:** Start- en eindtijden (inclusive/exclusive logica) voor SQL `BETWEEN` statements.
- [x] **Tijdzones:** Conversie en IANA support.
- [x] **Feestdagen:** Vaste en bewegende feestdagen (Pasen, Kerst).

### Infrastructuur & Kwaliteit

- [x] **Docker Support:** Kant-en-klare image voor eenvoudige deployment.
- [x] **MCP Protocol:** Volledige implementatie van Tools en Resources.
- [x] **Documentatie:** Duidelijke "Getting Started" voor Text-to-SQL integratie (zie README & example script).
- [ ] **CI/CD:** Automatische tests bij elke commit (lokaal via `release.sh`).

## 6. Roadmap

### Fase 1: Validatie & Hardening (Huidig)

- Focus: Zorgen dat de parser 99.9% accuraat is op edge cases (jaarwisselingen, schrikkeljaren).
- Actie: Uitbreiden test-suite met specifieke SQL-generatie scenario's.

### Fase 2: Launch & Distributie

- Publiceren op Docker Hub.
- Publiceren op PyPI (`pip install mcp-time_range_parser`).
- Listing aanvragen op MCP-server directories (Smithery, Glama).

### Fase 3: Future Growth (Post-MVP)

- **Fiscal Years:** Ondersteuning voor gebroken boekjaren (bijv. start in april).
- **Custom Events:** Gebruikersconfiguratie voor bedrijfsspecifieke events ("Black Friday Sale").
- **Meertaligheid:** Uitbreiden naar Duits en Frans.

## 7. Implementatieplan (Directe Acties)

1.  **Refine Docs:** [x] Update `README.md` met de specifieke Text-to-SQL use-case.
2.  **Integration Test:** [x] Maak een voorbeeld script (`text_to_sql_example.py`) dat een "mock" SQL query genereert.
3.  **Release v1.0:** [x] Zie `release.sh` voor build & tag instructies.
