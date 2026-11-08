# Dossier a-publier (version 1.4)

Depose ici un fichier `.html` : le robot GitHub le controle, le publie a la racine
(sans numero de version dans le nom), ajoute sa carte au hub et monte la version du hub.

## Ce que le fichier doit contenir
1. Un numero de version visible (ex. `v1.2`) dans le fichier.
2. Une balise `meta name="hub"` dans le <head> (uniquement pour un NOUVEL outil) :

    <meta name="hub" content='{"titre":"Mon outil","texte":"Une phrase pour l’enfant","emoji":"🎮","couleur":"vert","section":"entrainement","etiquette":"Jeu","bouton":"▶ Jouer"}'>

   - couleur : vert, indigo, orange, bleu ou violet
   - nouvelle section : ajouter aussi "section_titre", "pastille" et (facultatif) "avant"
   - pas d'apostrophe droite dans les textes (utiliser ’)

## Ajoute automatiquement par le robot
Le robot insere dans chaque outil publie la balise `hub-commun.js` : barre du haut avec le bouton « ⬅ Retour aux jeux » (retour au hub)
et Mode Parent partage (code + historique des evaluations) pour les outils qui n'ont pas leur propre Mode Parent.
Pour une evaluation, enregistrer le resultat avec `HubHistorique.enregistrer({...})` (voir evaluation-plantes-cm1-v1.3.html).
Rapport pour analyse : `HubHistorique.enregistrer({... questions:[{n,ref,comp,compLabel,type,enonce,reponse,attendu,ok,tempsSec,indice|aide}] })`
alimente l'onglet « Rapport » du Mode Parent (format `hub-rapport` v1, evolutif : tout champ en plus est conserve).
Un outil qui a son propre Mode Parent appelle `HubRapport.ouvrir({outil:{id,titre,version}, passages:[...]})` (voir resolution_problemes_cm1-v1.8.html).
Reglage facultatif : `<meta name="hub-parent" content="propre|partage">`.

Le robot ajoute aussi la date d'ajout (`ajout`) : la carte du hub porte le badge « Nouveau » pendant 14 jours.

## Controles automatiques (si un seul echoue, RIEN n'est publie)
- aucun e-mail ni mot de passe ; aucun « Mode Prof »
- numero de version present, et jamais plus ancien que la version deja en ligne
- JavaScript sans erreur de syntaxe
- aucun script ou style externe hors liste autorisee (Firebase, Google Fonts, cdnjs)
- fichier de moins de 2 Mo ; carte du hub valide ; lien de la carte non casse

## En cas d'echec
Onglet **Actions** du depot, dernier passage en rouge : la raison est ecrite en francais.
Le fichier reste dans a-publier/ : corrige-le et depose-le de nouveau.
Pour annuler une publication : bouton **Revert** du commit dans GitHub Desktop.
