/* hub-commun.js - VERSION 1.1 (2026-11-07)  [1.1 : barre fixe en haut avec « Retour aux jeux », adaptee PC/tablette/telephone]
   Partage entre tous les outils du hub « Mes jeux pour apprendre » :
   1. barre fixe en HAUT avec le bouton « ← Retour aux jeux » (retour au hub) ;
   2. Mode Parent partage (code) pour les outils qui n'ont pas leur propre Mode Parent ;
   3. historique des evaluations (HubHistorique), consultable dans le Mode Parent.
   Les donnees restent dans le navigateur (localStorage) : rien n'est envoye sur internet.
   Le code parent est un simple verrou pour les enfants, pas une protection cryptographique.

   Reglage par page (facultatif) : <meta name="hub-parent" content="propre|partage|aucun">
     propre  = l'outil a son propre Mode Parent -> pas de cadenas partage
     partage = forcer le cadenas partage
     (absent) = detection automatique (texte « Mode Parent » dans la page)          */
(function () {
  "use strict";
  if (window.HubCommun) return;
  var VERSION = "1.1";
  var K_HIST = "hub:historique", K_CODE = "hub:codeParent", K_SESS = "hub:parentActif", MAX = 500;
  var enIframe = false;
  try { enIframe = window.self !== window.top; } catch (e) { enIframe = true; }

  /* ---------- utilitaires ---------- */
  function lire(k, def) { try { var v = JSON.parse(localStorage.getItem(k)); return (v === null || v === undefined) ? def : v; } catch (e) { return def; } }
  function ecrire(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch (e) { return false; } }
  function supprimer(k) { try { localStorage.removeItem(k); } catch (e) {} }
  function esc(s) { return String(s === null || s === undefined ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;"); }
  function hacher(s) { var t = "hub-parent|" + s, h = 5381; for (var i = 0; i < t.length; i++) { h = ((h << 5) + h + t.charCodeAt(i)) >>> 0; } return h.toString(36); }
  function z(n) { return (n < 10 ? "0" : "") + n; }
  function fmtDate(ms) { var d = new Date(ms); return z(d.getDate()) + "/" + z(d.getMonth() + 1) + "/" + d.getFullYear() + " " + z(d.getHours()) + "h" + z(d.getMinutes()); }
  function $(id) { return document.getElementById(id); }

  /* ---------- historique ---------- */
  var Hist = {
    lister: function () { return lire(K_HIST, []); },
    enregistrer: function (e) {
      var l = lire(K_HIST, []);
      e = e || {};
      e.id = Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
      e.date = Date.now();
      l.push(e);
      if (l.length > MAX) l = l.slice(l.length - MAX);
      ecrire(K_HIST, l);
      return e;
    },
    effacer: function () { ecrire(K_HIST, []); }
  };

  /* ---------- Mode Parent partage ---------- */
  function emit() { try { document.dispatchEvent(new CustomEvent("hub:parent", { detail: { actif: Parent.actif() } })); } catch (e) {} majCadenas(); }
  var Parent = {
    actif: function () { try { return sessionStorage.getItem(K_SESS) === "1"; } catch (e) { return false; } },
    ouvrir: function (vue) { construire(); var c = lire(K_CODE, null); if (!c) afficher("creer"); else if (!Parent.actif()) afficher("saisir"); else afficher(vue || "historique"); },
    verrouiller: function () { try { sessionStorage.removeItem(K_SESS); } catch (e) {} emit(); fermer(); }
  };
  function activer() { try { sessionStorage.setItem(K_SESS, "1"); } catch (e) {} emit(); }

  /* ---------- styles ---------- */
  var CSS = [
    ":root{--hubc-h:calc(46px + env(safe-area-inset-top,0px))}",
    "html.hubc-avec-barre{padding-top:var(--hubc-h);scroll-padding-top:var(--hubc-h)}",
    ".hubc-bar{position:fixed;top:0;left:0;right:0;z-index:2147483000;box-sizing:border-box;min-height:var(--hubc-h);display:flex;align-items:center;justify-content:space-between;gap:8px;padding:calc(5px + env(safe-area-inset-top,0px)) calc(8px + env(safe-area-inset-right,0px)) 5px calc(8px + env(safe-area-inset-left,0px));background:linear-gradient(90deg,#4B45D6,#6C5CE7);box-shadow:0 2px 8px rgba(0,0,0,.25);font:700 15px/1.2 system-ui,'Segoe UI',Arial,sans-serif}",
    ".hubc-btn{display:inline-flex;align-items:center;gap:6px;min-height:36px;padding:0 14px;border-radius:20px;border:2px solid rgba(255,255,255,.85);background:rgba(255,255,255,.18);color:#fff;font:inherit;text-decoration:none;cursor:pointer;white-space:nowrap}",
    ".hubc-btn:active{transform:scale(.97)}.hubc-retour{background:#fff;color:#4B45D6;border-color:#fff}.hubc-cadenas.on{background:#2EAD5B;border-color:#2EAD5B}",
    ".hubc-titre{color:#fff;font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}",
    "@media (max-width:340px){.hubc-long{display:none}}",
    ".hubc-fond{position:fixed;inset:0;z-index:2147483600;background:rgba(20,20,40,.6);display:none;align-items:center;justify-content:center;padding:12px;font:16px/1.45 system-ui,'Segoe UI',Arial,sans-serif}",
    ".hubc-fond.on{display:flex}",
    ".hubc-boite{background:#fff;color:#1F2340;border-radius:18px;width:100%;max-width:560px;max-height:92vh;overflow:auto;padding:14px 16px 16px;box-shadow:0 10px 40px rgba(0,0,0,.4)}",
    ".hubc-tete{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;font-size:18px}",
    ".hubc-x{border:none;background:#eef0f7;border-radius:50%;width:38px;height:38px;font-size:18px;cursor:pointer}",
    ".hubc-onglets{display:flex;gap:6px;margin:6px 0 10px}",
    ".hubc-o{flex:1;border:2px solid #cbd0e6;background:#fff;border-radius:12px;padding:8px;font:700 14px system-ui;cursor:pointer;color:#1F2340}.hubc-o.on{background:#ECEBFF;border-color:#4B45D6;color:#4B45D6}",
    ".hubc-boite input,.hubc-boite select{font:inherit;width:100%;padding:10px;border:2px solid #cbd0e6;border-radius:10px;margin:6px 0;background:#fff;color:#1F2340}",
    ".hubc-b{font:700 15px system-ui;border:none;border-radius:12px;padding:11px 16px;background:#4B45D6;color:#fff;cursor:pointer;margin:6px 6px 0 0}.hubc-b.sec{background:#fff;color:#4B45D6;border:2px solid #4B45D6}.hubc-b.danger{background:#C0501A}",
    ".hubc-msg{min-height:20px;font-weight:700;color:#C0501A;font-size:14px;margin:4px 0}",
    ".hubc-lien{background:none;border:none;color:#4B45D6;text-decoration:underline;font:inherit;cursor:pointer;padding:6px 0}",
    ".hubc-filtres{display:grid;grid-template-columns:1fr 1fr;gap:8px}",
    ".hubc-tab{overflow-x:auto}.hubc-tab table{width:100%;border-collapse:collapse;font-size:14px}",
    ".hubc-tab th,.hubc-tab td{border:1px solid #d9dcee;padding:6px 8px;text-align:left}.hubc-tab th{background:#ECEBFF}",
    ".hubc-l{cursor:pointer}.hubc-l:hover{background:#f6f6ff}.hubc-d td{background:#fffaf0;font-size:13.5px}",
    ".hubc-note{font-size:13px;color:#5B6280}.hubc-ok{color:#1b7a3d;font-weight:700}.hubc-ko{color:#C0501A;font-weight:700}",
    ".hubc-d ul{margin:4px 0 8px;padding-left:18px}",
    "@media print{.hubc-bar,.hubc-fond{display:none!important}html.hubc-avec-barre{padding-top:0!important}}"
  ].join("");

  /* ---------- panneau ---------- */
  var fond = null, corps = null, filtre = { outil: "", joueur: "" }, erreurs = 0, bloque = 0, minuteur = null;
  function construire() {
    if (fond) return;
    var st = document.createElement("style"); st.textContent = CSS; document.head.appendChild(st);
    fond = document.createElement("div"); fond.className = "hubc-fond"; fond.setAttribute("role", "dialog"); fond.setAttribute("aria-modal", "true"); fond.setAttribute("aria-label", "Mode Parent");
    fond.innerHTML = "<div class=\"hubc-boite\"><div class=\"hubc-tete\"><b>👨‍👩‍👧 Mode Parent</b><button class=\"hubc-x\" id=\"hubc-fermer\" aria-label=\"Fermer\">✕</button></div><div id=\"hubc-corps\"></div></div>";
    document.body.appendChild(fond);
    corps = $("hubc-corps");
    $("hubc-fermer").onclick = fermer;
    fond.addEventListener("click", function (e) { if (e.target === fond) fermer(); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") fermer(); });
  }
  function fermer() { if (fond) fond.classList.remove("on"); }
  function onglets(v) {
    return "<div class=\"hubc-onglets\"><button class=\"hubc-o" + (v === "historique" ? " on" : "") + "\" id=\"hubc-t1\">📊 Historique</button><button class=\"hubc-o" + (v === "reglages" ? " on" : "") + "\" id=\"hubc-t2\">⚙️ Réglages</button></div>";
  }
  function brancherOnglets() { $("hubc-t1").onclick = function () { afficher("historique"); }; $("hubc-t2").onclick = function () { afficher("reglages"); }; }

  function afficher(v) {
    construire(); fond.classList.add("on");
    if (v === "creer") return vueCreer();
    if (v === "saisir") return vueSaisir();
    if (v === "oubli") return vueOubli();
    if (!Parent.actif()) return vueSaisir();
    if (v === "reglages") return vueReglages();
    return vueHistorique();
  }
  function msg(t) { var m = $("hubc-msg"); if (m) m.textContent = t; }

  function vueCreer() {
    corps.innerHTML = "<p>Choisis un <b>code parent</b> (4 chiffres ou plus). Il protège l'historique des évaluations.</p>" +
      "<input id=\"hubc-c1\" type=\"password\" inputmode=\"numeric\" autocomplete=\"off\" placeholder=\"Code\">" +
      "<input id=\"hubc-c2\" type=\"password\" inputmode=\"numeric\" autocomplete=\"off\" placeholder=\"Répète le code\">" +
      "<div class=\"hubc-msg\" id=\"hubc-msg\"></div><button class=\"hubc-b\" id=\"hubc-ok\">Créer le code</button>";
    $("hubc-c1").focus();
    $("hubc-ok").onclick = function () {
      var a = $("hubc-c1").value, b = $("hubc-c2").value;
      if (a.length < 4) return msg("Le code doit avoir au moins 4 caractères.");
      if (a !== b) return msg("Les deux codes sont différents.");
      ecrire(K_CODE, { h: hacher(a) }); activer(); afficher("historique");
    };
  }
  function vueSaisir() {
    corps.innerHTML = "<p>Entre le code parent.</p><input id=\"hubc-c1\" type=\"password\" inputmode=\"numeric\" autocomplete=\"off\" placeholder=\"Code parent\">" +
      "<div class=\"hubc-msg\" id=\"hubc-msg\"></div><button class=\"hubc-b\" id=\"hubc-ok\">Valider</button><br><button class=\"hubc-lien\" id=\"hubc-oubli\">Code oublié ?</button>";
    $("hubc-c1").focus();
    var go = function () {
      var reste = Math.ceil((bloque - Date.now()) / 1000);
      if (reste > 0) return msg("Trop d'essais : attends " + reste + " secondes.");
      var c = lire(K_CODE, null);
      if (c && hacher($("hubc-c1").value) === c.h) { erreurs = 0; activer(); afficher("historique"); return; }
      erreurs++;
      if (erreurs >= 3) { erreurs = 0; bloque = Date.now() + 30000; msg("3 erreurs : attends 30 secondes."); } else msg("Code incorrect.");
    };
    $("hubc-ok").onclick = go;
    $("hubc-c1").onkeydown = function (e) { if (e.key === "Enter") go(); };
    $("hubc-oubli").onclick = function () { afficher("oubli"); };
  }
  function vueOubli() {
    corps.innerHTML = "<p><b>Code oublié ?</b> La seule solution est d'<b>effacer le code ET tout l'historique</b> de cet appareil. C'est définitif.</p>" +
      "<button class=\"hubc-b danger\" id=\"hubc-oui\">Oui, tout effacer</button><button class=\"hubc-b sec\" id=\"hubc-non\">Annuler</button>";
    $("hubc-oui").onclick = function () { supprimer(K_CODE); Hist.effacer(); try { sessionStorage.removeItem(K_SESS); } catch (e) {} emit(); vueCreer(); };
    $("hubc-non").onclick = function () { vueSaisir(); };
  }
  function vueReglages() {
    corps.innerHTML = onglets("reglages") + "<p><b>Changer le code parent</b></p>" +
      "<input id=\"hubc-c1\" type=\"password\" inputmode=\"numeric\" autocomplete=\"off\" placeholder=\"Nouveau code\">" +
      "<input id=\"hubc-c2\" type=\"password\" inputmode=\"numeric\" autocomplete=\"off\" placeholder=\"Répète le nouveau code\">" +
      "<div class=\"hubc-msg\" id=\"hubc-msg\"></div><button class=\"hubc-b\" id=\"hubc-ok\">Enregistrer</button>" +
      "<hr><button class=\"hubc-b sec\" id=\"hubc-verr\">🔓 Quitter le Mode Parent</button><p class=\"hubc-note\">Version hub-commun " + VERSION + " · données stockées uniquement sur cet appareil.</p>";
    brancherOnglets();
    $("hubc-ok").onclick = function () {
      var a = $("hubc-c1").value, b = $("hubc-c2").value;
      if (a.length < 4) return msg("Le code doit avoir au moins 4 caractères.");
      if (a !== b) return msg("Les deux codes sont différents.");
      ecrire(K_CODE, { h: hacher(a) }); $("hubc-c1").value = ""; $("hubc-c2").value = ""; msg(""); corps.querySelector(".hubc-msg").style.color = "#1b7a3d"; msg("✅ Code modifié.");
    };
    $("hubc-verr").onclick = function () { Parent.verrouiller(); };
  }
  function statut(c) { var p = c.n ? c.ok / c.n : 0; return p >= 0.75 ? "✅" : (p >= 0.5 ? "🟡" : "🌱"); }
  function vueHistorique() {
    var tout = Hist.lister().slice().reverse();
    var outils = {}, joueurs = {};
    tout.forEach(function (e) { outils[e.titre || e.outil || "?"] = 1; joueurs[e.joueur || "joueur"] = 1; });
    var liste = tout.filter(function (e) {
      return (!filtre.outil || (e.titre || e.outil) === filtre.outil) && (!filtre.joueur || (e.joueur || "joueur") === filtre.joueur);
    });
    var opt = function (obj, cur, tous) { var h = "<option value=\"\">" + tous + "</option>"; Object.keys(obj).sort().forEach(function (k) { h += "<option value=\"" + esc(k) + "\"" + (k === cur ? " selected" : "") + ">" + esc(k) + "</option>"; }); return h; };
    var h = onglets("historique");
    if (!tout.length) {
      h += "<p>Aucun résultat enregistré pour l'instant. Les évaluations terminées apparaîtront ici (date, joueur, score et points à revoir).</p>";
    } else {
      h += "<div class=\"hubc-filtres\"><select id=\"hubc-fo\">" + opt(outils, filtre.outil, "Toutes les évaluations") + "</select><select id=\"hubc-fj\">" + opt(joueurs, filtre.joueur, "Tous les joueurs") + "</select></div>";
      var somme = 0, nb = 0;
      liste.forEach(function (e) { if (e.total) { somme += e.score / e.total; nb++; } });
      h += "<p class=\"hubc-note\">" + liste.length + " passage" + (liste.length > 1 ? "s" : "") + (nb ? " · moyenne " + Math.round(100 * somme / nb) + " %" : "") + " · touche une ligne pour voir le détail</p>";
      h += "<div class=\"hubc-tab\"><table><tr><th>Date</th><th>Joueur</th><th>Évaluation</th><th>Score</th></tr>";
      liste.forEach(function (e, k) {
        h += "<tr class=\"hubc-l\" data-k=\"" + k + "\"><td>" + fmtDate(e.date) + "</td><td>" + esc(e.joueur || "joueur") + "</td><td>" + esc(e.titre || e.outil) + "</td><td><b>" + e.score + "/" + e.total + "</b></td></tr>";
        var d = "";
        if (e.competences && e.competences.length) { d += "<b>Bilan par compétence</b><ul>"; e.competences.forEach(function (c) { d += "<li>" + statut(c) + " " + esc(c.label) + " (" + c.ok + "/" + c.n + ")</li>"; }); d += "</ul>"; }
        if (e.aRevoir && e.aRevoir.length) { d += "<b>À revoir</b><ul>"; e.aRevoir.forEach(function (r) { d += "<li><b>Q" + esc(r.q) + "</b> " + esc(r.texte) + "<br><span class=\"hubc-ok\">➜ " + esc(r.correction) + "</span></li>"; }); d += "</ul>"; }
        else d += "<span class=\"hubc-ok\">Rien à revoir 🌟</span>";
        h += "<tr class=\"hubc-d\" id=\"hubc-d" + k + "\" hidden><td colspan=\"4\">" + d + "</td></tr>";
      });
      h += "</table></div><button class=\"hubc-b danger\" id=\"hubc-eff\">🧹 Effacer l'historique</button>";
    }
    h += "<button class=\"hubc-b sec\" id=\"hubc-verr\">🔓 Quitter le Mode Parent</button>";
    corps.innerHTML = h;
    brancherOnglets();
    if ($("hubc-fo")) { $("hubc-fo").onchange = function () { filtre.outil = this.value; vueHistorique(); }; $("hubc-fj").onchange = function () { filtre.joueur = this.value; vueHistorique(); }; }
    Array.prototype.forEach.call(corps.querySelectorAll(".hubc-l"), function (tr) { tr.onclick = function () { var d = $("hubc-d" + tr.getAttribute("data-k")); d.hidden = !d.hidden; }; });
    if ($("hubc-eff")) {
      $("hubc-eff").onclick = function () {
        var b = this;
        if (b.getAttribute("data-c") === "1") { clearTimeout(minuteur); Hist.effacer(); filtre = { outil: "", joueur: "" }; vueHistorique(); return; }
        b.setAttribute("data-c", "1"); b.textContent = "⚠️ Confirmer : effacer définitivement";
        minuteur = setTimeout(function () { if ($("hubc-eff")) { $("hubc-eff").removeAttribute("data-c"); $("hubc-eff").textContent = "🧹 Effacer l'historique"; } }, 5000);
      };
    }
    $("hubc-verr").onclick = function () { Parent.verrouiller(); };
  }

  /* ---------- barre du haut ---------- */
  var cadenas = null;
  function majCadenas() { if (cadenas) { var on = Parent.actif(); cadenas.className = "hubc-btn hubc-cadenas" + (on ? " on" : ""); cadenas.innerHTML = (on ? "🔓" : "🔒") + "<span>Parent</span>"; } }
  function decalerFixes() {
    /* elements deja fixes pres du haut de la page (ex. 14 px) : on les descend sous la barre */
    var H = document.querySelector(".hubc-bar").offsetHeight, els = document.body.querySelectorAll("*");
    for (var i = 0; i < els.length; i++) {
      var e = els[i];
      if (e.closest(".hubc-bar") || e.closest(".hubc-fond")) continue;
      var cs = getComputedStyle(e);
      if (cs.position !== "fixed") continue;
      var t = parseFloat(cs.top);
      if (t > 0 && t < H) e.style.top = (t + H) + "px";
    }
  }
  function boutons() {
    if (enIframe) return;
    var meta = document.querySelector("meta[name=\"hub-parent\"]"), mode = meta ? meta.getAttribute("content") : "auto";
    var propre = (mode === "propre" || mode === "aucun") || (mode === "auto" && /Mode Parent/i.test(document.documentElement.textContent));
    construire();
    var estHub = /(^|\/)(index\.html)?$/.test(location.pathname);
    /* anciens liens vers le hub (ex. « 🏠 Accueil ») : remplaces par le bouton Retour de la barre */
    if (!estHub) {
      var anciens = document.querySelectorAll("a[href=\"index.html\"],a[href=\"./index.html\"]");
      for (var i = 0; i < anciens.length; i++) anciens[i].style.display = "none";
    }
    var bar = document.createElement("div"); bar.className = "hubc-bar"; bar.setAttribute("role", "navigation"); bar.setAttribute("aria-label", "Navigation du hub");
    if (estHub) {
      var t = document.createElement("span"); t.className = "hubc-titre"; t.textContent = "🚀 Mes jeux pour apprendre"; bar.appendChild(t);
    } else {
      var a = document.createElement("a"); a.className = "hubc-btn hubc-retour"; a.href = "index.html"; a.title = "Retour au hub Mes jeux pour apprendre"; a.setAttribute("aria-label", "Retour aux jeux");
      a.innerHTML = "⬅<span>Retour<span class=\"hubc-long\"> aux jeux</span></span>"; bar.appendChild(a);
    }
    if (!propre) {
      cadenas = document.createElement("button"); cadenas.type = "button"; cadenas.setAttribute("aria-label", "Mode Parent");
      cadenas.onclick = function () { Parent.ouvrir("historique"); };
      bar.appendChild(cadenas); majCadenas();
    } else if (!estHub) {
      var vide = document.createElement("span"); bar.appendChild(vide);
    }
    document.body.insertBefore(bar, document.body.firstChild);
    document.documentElement.classList.add("hubc-avec-barre");
    var cs = getComputedStyle(document.body);
    if (Math.abs(parseFloat(cs.minHeight) - window.innerHeight) < 2) document.body.style.minHeight = "calc(100vh - var(--hubc-h))";
    decalerFixes();
  }

  window.HubHistorique = Hist;
  window.HubParent = Parent;
  window.HubCommun = { version: VERSION, aCadenas: function () { return !!cadenas; } };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boutons); else boutons();
})();
