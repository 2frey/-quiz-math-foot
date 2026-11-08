#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
publier.py - VERSION 1.3 (2026-11-08)  [1.3 : champ ajout (badge Nouveau) ; 1.2 : detection exacte de la balise hub-commun ; 1.1 : injecter_hub_commun]
Publie un outil HTML dans le depot du hub « Mes jeux pour apprendre ».

Ce que fait le script :
  1. verifie que le fichier ne contient ni e-mail, ni mot de passe (depot public) ;
  2. copie le fichier a la racine du depot, SANS numero de version dans le nom ;
  3. ajoute la carte dans index.html (liste TOOLS, et la section si besoin) ;
  4. monte la version du hub et ajoute une ligne a l'historique ;
  5. fait la meme chose dans index-complet-local.html si --local est donne ;
  6. optionnel : commit (et push) avec un message en francais.

Exemples (a lancer dans le dossier du depot clone, ou avec --depot) :
  python publier.py evaluation-plantes-cm1-v1.1.html --titre "Évaluation Sciences" ^
      --emoji 🌱 --couleur vert --section lecons --section-titre "🔬 Je vérifie mes leçons" ^
      --pastille sciences --avant devoirs --etiquette Évaluation --bouton "▶ Commencer" ^
      --texte "Graines et plantes : réponds aux questions et découvre ton score !"
  python publier.py evaluation-plantes-cm1-v1.2.html          (mise a jour d'un outil deja dans le hub)
  python publier.py mon-outil.html --essai                     (simulation : ne modifie rien)
"""
import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys

COULEURS = ["vert", "indigo", "orange", "bleu", "violet"]
DOMAINES_OK = ("exemple.fr", "exemple.com", "example.com", "example.org", "example.fr")


TAG_HUB = '<script src="hub-commun.js"></script>'


def a_balise_hub_commun(txt):
    """Vrai si la balise <script src="hub-commun.js"> est deja presente (une simple mention ne compte pas)."""
    return re.search(r"<script[^>]+src=[\"']hub-commun\.js", txt, re.I) is not None


def injecter_hub_commun(txt):
    """Ajoute la balise hub-commun.js avant le dernier </body>. Retourne (texte, modifie)."""
    if a_balise_hub_commun(txt):
        return txt, False
    i = txt.lower().rfind("</body>")
    if i < 0:
        return txt, False
    return txt[:i] + "<!-- hub-commun v1.0 : bouton Mes jeux + Mode Parent partage -->\n" + TAG_HUB + "\n" + txt[i:], True


class Erreur(Exception):
    pass


def lire(chemin):
    with open(chemin, encoding="utf-8") as f:
        return f.read()


def ecrire(chemin, texte):
    with open(chemin, "w", encoding="utf-8", newline="\n") as f:
        f.write(texte)


# ---------------------------------------------------------------- garde-fou
def controle_confidentialite(chemin):
    """Retourne la liste des problemes trouves dans le fichier a publier."""
    txt = lire(chemin)
    problemes = []
    for m in re.finditer(r"[\w.+-]+@([\w-]+\.[\w.-]+)", txt):
        if m.group(1).lower() not in DOMAINES_OK:
            problemes.append("e-mail : " + m.group(0))
    for m in re.finditer(r"(?i)(mot de passe|password|passwd|motdepasse)\s*[:=]\s*[\"'][^\"']{3,}[\"']", txt):
        problemes.append("mot de passe possible : " + m.group(0)[:60])
    return problemes


# ---------------------------------------------------------------- listes JS
def lire_liste(s, nom):
    m = re.search(r"(var " + nom + r"\s*=\s*\[)(.*?)(\n\s*\];)", s, re.S)
    if not m:
        raise Erreur("Liste " + nom + " introuvable dans index.html")
    lignes = []
    for l in m.group(2).split("\n"):
        t = l.strip()
        if not t:
            continue
        if not t.startswith("{"):
            raise Erreur("Ligne inattendue dans " + nom + " (commentaire ?) : " + t[:50] + " - modification a faire a la main.")
        lignes.append(t.rstrip(",").strip())
    return m, lignes


def remplacer_liste(s, m, lignes):
    corps = "\n" + ",\n".join("    " + l for l in lignes)
    return s[:m.start(2)] + corps + s[m.end(2):]


def js(v):
    return json.dumps(v, ensure_ascii=False)


# ---------------------------------------------------------------- index.html
def mettre_a_jour_index(chemin, a, nom_pub, date):
    """Modifie un index. Retourne (modifie, messages)."""
    s = lire(chemin)
    msgs = []
    modifie = False

    # 1. deja present ?
    mt, tools = lire_liste(s, "TOOLS")
    if any(('href:' + js(nom_pub)) in l.replace(" ", "") or ('href:"' + nom_pub + '"') in l.replace(" ", "") for l in tools):
        msgs.append("Carte deja presente dans le hub pour " + nom_pub + " : aucune carte ajoutee (mise a jour du fichier seulement).")
        return False, msgs

    if not a.titre:
        raise Erreur("Nouvel outil : indique --titre (et idealement --texte, --emoji, --couleur).")

    # 2. section
    ms, sections = lire_liste(s, "SECTIONS")
    ids = [re.search(r'id\s*:\s*"([^"]+)"', l).group(1) for l in sections]
    if a.section not in ids:
        if not (a.section_titre and a.pastille):
            raise Erreur("La section '" + a.section + "' n'existe pas : ajoute --section-titre et --pastille pour la creer.")
        ligne_s = "{ id:" + js(a.section) + ", esp:\"e\", titre:" + js(a.section_titre) + ", pastille:" + js(a.pastille) + " }"
        if a.avant and a.avant in ids:
            sections.insert(ids.index(a.avant), ligne_s)
        else:
            sections.append(ligne_s)
        s = remplacer_liste(s, ms, sections)
        msgs.append("Section creee : " + a.section_titre)
        mt, tools = lire_liste(s, "TOOLS")

    # 3. carte
    ligne_t = ("{ esp:\"e\", sec:" + js(a.section) + ", emoji:" + js(a.emoji) + ", titre:" + js(a.titre)
               + ", texte:" + js(a.texte) + ", couleur:" + js(a.couleur) + ", href:" + js(nom_pub)
               + ", etiquette:" + js(a.etiquette) + ", bouton:" + js(a.bouton) + ", ajout:" + js(date) + " }")
    pos = len(tools)
    for i, l in enumerate(tools):
        if re.search(r'sec\s*:\s*"' + re.escape(a.section) + '"', l):
            pos = i + 1
    tools.insert(pos, ligne_t)
    s = remplacer_liste(s, mt, tools)
    msgs.append("Carte ajoutee : " + a.titre + " -> " + nom_pub)

    # 4. version + historique
    ver_txt = ""
    mv = re.search(r"^\s*\|\s*(\d+)\.(\d+)\s*\|", s, re.M)
    if mv:
        nv = mv.group(1) + "." + str(int(mv.group(2)) + 1)
        sep = re.search(r"^\s*\|-{3,}.*$", s, re.M)
        if sep:
            note = "Ajout de la carte « " + a.titre + " » (" + nom_pub + ")"
            ligne_h = "  | " + nv.ljust(7) + " | " + date + " | " + note.ljust(78) + " |"
            s = s[:sep.end()] + "\n" + ligne_h + s[sep.end():]
            ver_txt = nv
        s2 = re.sub(r"(— v)\d+\.\d+", lambda m_: m_.group(1) + nv, s, count=1)
        if s2 != s:
            s = s2
            ver_txt = nv
    if ver_txt:
        msgs.append("Version du hub : v" + ver_txt)
    else:
        msgs.append("Historique/pied de page non reconnus dans " + os.path.basename(chemin) + " : version a mettre a jour a la main.")

    if not a.essai:
        ecrire(chemin, s)
    return True, msgs


# ---------------------------------------------------------------- principal
def main():
    p = argparse.ArgumentParser(description="Publie un outil HTML dans le hub.")
    p.add_argument("fichier", help="fichier HTML a publier")
    p.add_argument("--depot", default=os.environ.get("DEPOT_HUB", "."), help="dossier du depot clone (defaut : dossier courant)")
    p.add_argument("--local", default="", help="chemin de index-complet-local.html (facultatif)")
    p.add_argument("--titre", default="")
    p.add_argument("--texte", default="")
    p.add_argument("--emoji", default="🎮")
    p.add_argument("--couleur", default="vert", choices=COULEURS)
    p.add_argument("--section", default="entrainement")
    p.add_argument("--section-titre", default="")
    p.add_argument("--pastille", default="")
    p.add_argument("--avant", default="", help="id de la section avant laquelle inserer la nouvelle section")
    p.add_argument("--etiquette", default="Outil")
    p.add_argument("--bouton", default="▶ Jouer")
    p.add_argument("--essai", action="store_true", help="simulation : ne modifie rien")
    p.add_argument("--force", action="store_true", help="publier malgre l'alerte de confidentialite")
    p.add_argument("--git", action="store_true", help="faire le commit")
    p.add_argument("--push", action="store_true", help="faire aussi le push (implique --git)")
    a = p.parse_args()

    try:
        depot = os.path.abspath(a.depot)
        index = os.path.join(depot, "index.html")
        if not os.path.isfile(a.fichier):
            raise Erreur("Fichier introuvable : " + a.fichier)
        if not os.path.isfile(index):
            raise Erreur("index.html introuvable dans " + depot + " (utilise --depot).")

        # nom sans version
        base = os.path.basename(a.fichier)
        nom_pub = re.sub(r"[-_]v\d+(?:[._]\d+)*(?=\.html$)", "", base)

        # garde-fou
        pb = controle_confidentialite(a.fichier)
        if pb and not a.force:
            print("ARRET : donnees personnelles detectees (le depot est public) :")
            for x in pb:
                print("  - " + x)
            print("Corrige le fichier, ou relance avec --force si c'est volontaire.")
            return 2

        date = datetime.date.today().isoformat()
        cible = os.path.join(depot, nom_pub)
        print(("[SIMULATION] " if a.essai else "") + "Publication de " + base + " -> " + nom_pub)

        # copie
        if os.path.isfile(cible) and lire(cible) == lire(a.fichier):
            print("Fichier deja identique dans le depot : inchange.")
        else:
            etat = "remplace (mise a jour)" if os.path.isfile(cible) else "copie (nouveau)"
            if not a.essai:
                shutil.copyfile(a.fichier, cible)
            print("Fichier " + etat + " : " + nom_pub)

        # index en ligne, puis index local
        modifie, msgs = mettre_a_jour_index(index, a, nom_pub, date)
        for m in msgs:
            print("  " + m)
        if a.local:
            if not os.path.isfile(a.local):
                raise Erreur("index local introuvable : " + a.local)
            print("Index local :")
            m2, msgs2 = mettre_a_jour_index(a.local, a, nom_pub, date)
            for m in msgs2:
                print("  " + m)

        # git
        message = ("Ajout de " + a.titre + " au hub" if modifie else "Mise a jour de " + nom_pub)
        if (a.git or a.push) and not a.essai:
            try:
                subprocess.run(["git", "-C", depot, "add", "-A"], check=True)
                subprocess.run(["git", "-C", depot, "commit", "-m", message], check=True)
                if a.push:
                    subprocess.run(["git", "-C", depot, "push"], check=True)
                print("Git : commit" + (" + push" if a.push else "") + " effectue.")
            except FileNotFoundError:
                print("Git n'est pas installe en ligne de commande : utilise GitHub Desktop (Commit puis Push).")
            except subprocess.CalledProcessError as e:
                print("Git a echoue : " + str(e))
        else:
            print("Etape finale : dans GitHub Desktop, message de commit suggere : « " + message + " », puis Commit et Push.")
        return 0
    except Erreur as e:
        print("ERREUR : " + str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
