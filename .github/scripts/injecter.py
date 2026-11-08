#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
injecter.py - VERSION 1.0 (2026-11-07)
Ajoute <script src="hub-commun.js"> dans TOUS les outils HTML de la racine du depot
(bouton « Mes jeux » + Mode Parent partage + historique). Sans effet si deja present.
Lance par GitHub Actions quand hub-commun.js change, ou a la main (Run workflow).
Garde-fou : si hub-commun.js a une erreur de syntaxe JavaScript, rien n'est modifie.
"""
import glob
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import publier  # noqa: E402

RACINE = os.getcwd()


def main():
    js = os.path.join(RACINE, "hub-commun.js")
    if not os.path.isfile(js):
        print("ERREUR : hub-commun.js introuvable a la racine du depot.")
        return 1
    r = subprocess.run(["node", "--check", js], capture_output=True, text=True)
    if r.returncode != 0:
        print("ERREUR : hub-commun.js contient une erreur de syntaxe, rien n'est modifie.")
        print(r.stderr[:600])
        return 1
    faits, deja, ignores = [], [], []
    for f in sorted(glob.glob(os.path.join(RACINE, "*.html"))):
        nom = os.path.basename(f)
        txt, change = publier.injecter_hub_commun(publier.lire(f))
        if change:
            publier.ecrire(f, txt)
            faits.append(nom)
        elif publier.a_balise_hub_commun(txt):
            deja.append(nom)
        else:
            ignores.append(nom)
    print("Balise ajoutee dans : " + (", ".join(faits) or "aucun fichier"))
    print("Deja presente dans : " + (", ".join(deja) or "aucun fichier"))
    if ignores:
        print("Ignores (pas de </body>) : " + ", ".join(ignores))
    with open(os.path.join(tempfile.gettempdir(), "commit_message.txt"), "w", encoding="utf-8") as fh:
        fh.write("Ajout du bouton Mes jeux et du Mode Parent partage (hub-commun v1.0) : " + str(len(faits)) + " outil(s)\n")
    resume = os.environ.get("GITHUB_STEP_SUMMARY")
    if resume:
        with open(resume, "a", encoding="utf-8") as fh:
            fh.write("## hub-commun.js injecte\n\nAjoute : " + (", ".join(faits) or "aucun") + "\n\nDeja present : " + (", ".join(deja) or "aucun") + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
