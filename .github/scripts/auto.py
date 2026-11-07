#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto.py - VERSION 1.1 (2026-11-07)  [1.1 : injection de hub-commun.js dans chaque outil publie]
Publication automatique des outils deposes dans a-publier/ (lance par GitHub Actions).

Principe : TOUT est controle d'abord. Si un seul controle echoue, le script s'arrete avec
un code d'erreur : le robot ne fait ni commit ni push, donc RIEN n'est publie.
"""
import argparse
import datetime
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import publier  # noqa: E402

RACINE = os.getcwd()
DOSSIER = os.path.join(RACINE, "a-publier")
INDEX = os.path.join(RACINE, "index.html")
HOTES_OK = ("www.gstatic.com", "fonts.googleapis.com", "fonts.gstatic.com", "cdnjs.cloudflare.com")
TAILLE_MAX = 2 * 1024 * 1024
MSG_COMMIT = os.path.join(tempfile.gettempdir(), "commit_message.txt")


def version_de(txt):
    m = re.search(r"\b(?:v|version)\s*(\d+)\.(\d+)", txt, re.I)
    return (int(m.group(1)), int(m.group(2))) if m else None


def lire_meta(txt):
    m = re.search(r"<meta\s+name=[\"']hub[\"']\s+content='(.*?)'\s*/?>", txt, re.S)
    if not m:
        return None
    return json.loads(m.group(1))


def scripts_inline(txt):
    return re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", txt, re.S | re.I)


def verif_js(code, etiquette):
    """Retourne un message d'erreur ou None. node --check sur le code."""
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(code)
        nom = f.name
    try:
        r = subprocess.run(["node", "--check", nom], capture_output=True, text=True)
        if r.returncode != 0:
            ligne = [l for l in r.stderr.splitlines() if l.strip()][:4]
            return etiquette + " : erreur de syntaxe JavaScript -> " + " | ".join(ligne)
    except FileNotFoundError:
        return "Node.js introuvable : controle JavaScript impossible."
    finally:
        os.unlink(nom)
    return None


def controles(chemin, nom_pub):
    """Liste des erreurs bloquantes pour un fichier a publier."""
    err = []
    base = os.path.basename(chemin)
    if os.path.getsize(chemin) > TAILLE_MAX:
        err.append("fichier trop gros (> 2 Mo)")
    try:
        txt = publier.lire(chemin)
    except UnicodeDecodeError:
        return ["le fichier n'est pas en UTF-8"]

    for p in publier.controle_confidentialite(chemin):
        err.append("donnee personnelle : " + p)
    if re.search(r"Mode\s+Prof", txt):
        err.append("vocabulaire interdit : « Mode Prof » (utiliser « Mode Parent »)")
    if re.search(r"-----BEGIN [A-Z ]*PRIVATE KEY|ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}", txt):
        err.append("cle privee ou jeton detecte")

    v = version_de(txt)
    if not v:
        err.append("aucun numero de version visible (ex. v1.2) dans le fichier")
    cible = os.path.join(RACINE, nom_pub)
    if v and os.path.isfile(cible):
        ancien = publier.lire(cible)
        va = version_de(ancien)
        if va and v < va:
            err.append("version " + "%d.%d" % v + " plus ancienne que la version en ligne " + "%d.%d" % va)
        elif va and v == va and ancien != txt:
            err.append("meme version " + "%d.%d" % v + " mais contenu different : monte le numero de version")

    hotes = re.findall(r"<script[^>]+src=[\"'](https?://[^\"']+)", txt, re.I) + \
            re.findall(r"<link[^>]+href=[\"'](https?://[^\"']+)", txt, re.I)
    for u in hotes:
        h = re.match(r"https?://([^/]+)", u).group(1).lower()
        if h not in HOTES_OK:
            err.append("ressource externe non autorisee : " + u[:80])

    for i, code in enumerate(scripts_inline(txt), 1):
        if code.strip():
            e = verif_js(code, "script " + str(i))
            if e:
                err.append(e)
    return err


def carte_presente(index_txt, nom):
    _, lignes = publier.lire_liste(index_txt, "TOOLS")
    return any(re.search(r'href\s*:\s*"' + re.escape(nom) + '"', l) for l in lignes)


def namespace(meta):
    return argparse.Namespace(
        titre=meta.get("titre", ""), texte=meta.get("texte", ""), emoji=meta.get("emoji", "🎮"),
        couleur=meta.get("couleur", "vert"), section=meta.get("section", "entrainement"),
        section_titre=meta.get("section_titre", ""), pastille=meta.get("pastille", ""),
        avant=meta.get("avant", ""), etiquette=meta.get("etiquette", "Outil"),
        bouton=meta.get("bouton", "▶ Jouer"), essai=False)


def ecrire_resume(lignes):
    chemin = os.environ.get("GITHUB_STEP_SUMMARY")
    texte = "\n".join(lignes) + "\n"
    print(texte)
    if chemin:
        with open(chemin, "a", encoding="utf-8") as f:
            f.write(texte)


def main():
    fichiers = sorted(glob.glob(os.path.join(DOSSIER, "*.html")))
    if not fichiers:
        ecrire_resume(["Aucun fichier .html dans a-publier/ : rien a faire."])
        return 0
    if not os.path.isfile(INDEX):
        ecrire_resume(["## ECHEC", "index.html introuvable a la racine du depot."])
        return 1

    date = datetime.date.today().isoformat()
    index_txt = publier.lire(INDEX)
    plans, echecs = [], []

    # ---------- phase 1 : controles (rien n'est modifie)
    for f in fichiers:
        base = os.path.basename(f)
        nom_pub = re.sub(r"[-_]v\d+(?:[._]\d+)*(?=\.html$)", "", base)
        err = controles(f, nom_pub)
        meta = None
        deja = carte_presente(index_txt, nom_pub)
        if not deja:
            try:
                meta = lire_meta(publier.lire(f))
            except (ValueError, json.JSONDecodeError) as e:
                err.append("balise meta hub illisible (JSON invalide) : " + str(e)[:60])
            else:
                if not meta:
                    err.append("nouvel outil : balise <meta name=\"hub\" ...> absente (voir a-publier/LISEZMOI.md)")
                else:
                    for cle in ("titre", "texte", "emoji", "couleur", "section"):
                        if not meta.get(cle):
                            err.append("meta hub : champ « " + cle + " » manquant")
                    if meta.get("couleur") and meta["couleur"] not in publier.COULEURS:
                        err.append("meta hub : couleur « " + meta["couleur"] + " » inconnue")
        if err:
            echecs.append((base, err))
        else:
            plans.append((f, base, nom_pub, meta, deja))

    if echecs:
        out = ["## ECHEC - rien n'a ete publie", ""]
        for base, err in echecs:
            out.append("**" + base + "**")
            out += ["- " + e for e in err]
            out.append("")
        out.append("Le fichier reste dans a-publier/. Corrige-le puis depose-le de nouveau.")
        ecrire_resume(out)
        return 1

    # ---------- phase 2 : application (dans l'espace de travail du robot)
    titres, nouveaux = [], []
    for f, base, nom_pub, meta, deja in plans:
        cible = os.path.join(RACINE, nom_pub)
        shutil.copyfile(f, cible)
        os.remove(f)
        nouveau_txt, change = publier.injecter_hub_commun(publier.lire(cible))
        if change:
            publier.ecrire(cible, nouveau_txt)
        if not deja:
            publier.mettre_a_jour_index(INDEX, namespace(meta), nom_pub, date)
            nouveaux.append(nom_pub)
            titres.append(meta["titre"])
        else:
            titres.append(nom_pub + " (mise a jour)")

    # ---------- phase 3 : controle final du hub
    err = []
    idx = publier.lire(INDEX)
    for nom in nouveaux:
        if not os.path.isfile(os.path.join(RACINE, nom)):
            err.append("lien casse dans le hub : " + nom)
    for i, code in enumerate(scripts_inline(idx), 1):
        e = verif_js(code, "index.html script " + str(i))
        if e:
            err.append(e)
    _, tools = publier.lire_liste(idx, "TOOLS")
    avert = []
    if not os.path.isfile(os.path.join(RACINE, "hub-commun.js")):
        avert.append("hub-commun.js est absent de la racine : bouton Mes jeux et Mode Parent partage inactifs")
    for l in tools:
        m = re.search(r'href\s*:\s*"([^"]+)"', l)
        if m and not os.path.isfile(os.path.join(RACINE, m.group(1))):
            avert.append("carte dont le fichier est absent : " + m.group(1))
    if err:
        ecrire_resume(["## ECHEC (controle final du hub) - rien n'a ete publie", ""] + ["- " + e for e in err])
        return 1

    mv = re.search(r"— v(\d+\.\d+)", idx)
    ver = mv.group(1) if mv else "?"
    msg = "Publication automatique : " + ", ".join(titres) + " (hub v" + ver + ")"
    with open(MSG_COMMIT, "w", encoding="utf-8") as fh:
        fh.write(msg + "\n")
    out = ["## Publication reussie", "", msg, ""]
    out += ["- " + os.path.basename(p[1]) + " -> " + p[2] for p in plans]
    if avert:
        out += ["", "Avertissements (non bloquants) :"] + ["- " + a for a in avert]
    ecrire_resume(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
