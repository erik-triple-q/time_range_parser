````md
# 📘 Git Cheat Sheet – Meest Gebruikte Commands

Een overzicht van de **meest gebruikte Git-commando’s**, handig voor dagelijks gebruik.
Geschikt voor beginners én gevorderden.

---

## 📁 Repository & Setup

### Een nieuwe repository starten

```bash
git init
```
````

### Een repository clonen

```bash
git clone <repo-url>
```

### Remote repositories bekijken

```bash
git remote -v
```

---

## 📄 Status & Informatie

### Huidige status bekijken

```bash
git status
```

### Commit-geschiedenis bekijken

```bash
git log
```

### Verkorte log met grafiek

```bash
git log --oneline --graph --decorate
```

### Wijzigingen bekijken (diff)

```bash
git diff
```

---

## ➕ Bestanden Toevoegen (Staging)

### Eén bestand toevoegen

```bash
git add bestand.txt
```

### Alle wijzigingen toevoegen

```bash
git add .
```

### Interactief toevoegen

```bash
git add -p
```

---

## ✅ Committen

### Commit maken

```bash
git commit -m "Beschrijving van de wijziging"
```

### Commit aanpassen (laatste)

```bash
git commit --amend
```

---

## 🌿 Branches

### Alle branches bekijken

```bash
git branch
```

### Nieuwe branch maken

```bash
git branch nieuwe-branch
```

### Wisselen van branch

```bash
git checkout nieuwe-branch
```

### Branch maken + wisselen

```bash
git checkout -b nieuwe-branch
```

### Branch verwijderen

```bash
git branch -d branch-naam
```

---

## 🔀 Mergen & Rebasen

### Branch mergen

```bash
git merge branch-naam
```

### Rebase uitvoeren

```bash
git rebase main
```

### Rebase afbreken

```bash
git rebase --abort
```

---

## 🌍 Remote & Samenwerken

### Wijzigingen ophalen

```bash
git fetch
```

### Wijzigingen ophalen + mergen

```bash
git pull
```

### Wijzigingen pushen

```bash
git push
```

### Nieuwe branch pushen

```bash
git push -u origin branch-naam
```

---

## 🧹 Ongedaan Maken & Opruimen

### Bestand terugzetten (unstaged)

```bash
git restore bestand.txt
```

### Staging ongedaan maken

```bash
git restore --staged bestand.txt
```

### Laatste commit ongedaan maken (behoud wijzigingen)

```bash
git reset --soft HEAD~1
```

### Alles resetten (⚠️ destructief)

```bash
git reset --hard
```

---

## 📦 Stash (tijdelijk opslaan)

### Wijzigingen stashen

```bash
git stash
```

### Stash toepassen

```bash
git stash apply
```

### Stash lijst bekijken

```bash
git stash list
```

### Stash verwijderen

```bash
git stash drop
```

---

## 🏷️ Tags

### Tag aanmaken

```bash
git tag v1.0.0
```

### Tags bekijken

```bash
git tag
```

### Tag pushen

```bash
git push origin v1.0.0
```

---

## 🧠 Handige Tips

- Gebruik duidelijke commit messages
- Commit vaak en klein
- Pull altijd voordat je pusht
- Gebruik branches voor features en fixes

---

## 📚 Extra

- Officiële docs: https://git-scm.com/docs
- Visual Git tool: GitKraken / Sourcetree

---

✅ **Happy coding & versioning!**

```

Wil je ook:
- een **NL/EN versie**
- een **PDF of printbare layout**
- of een **team-specifieke Git workflow** (Git Flow / Trunk-based)?

Laat het weten!
```
