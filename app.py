import streamlit as st
import json
import os

from PIL import Image, ImageDraw, ImageFont
import io
import textwrap
import os

def generer_fiche_personnage_png(profil, data_globales):
    """Génère le fichier PNG avec chargement sécurisé de la police Windows et coordonnées pixels réelles."""
    try:
        base_image = Image.open("AC_Fiche de perso.jpg").convert("RGB")
    except FileNotFoundError:
        try:
            base_image = Image.open("AC_Fiche de perso_2.jpg").convert("RGB")
        except FileNotFoundError:
            return b""

    draw = ImageDraw.Draw(base_image)
    
    # --- 📐 CHARGEMENT STRICT DE LA POLICE WINDOWS ---
    # On cible directement le répertoire des polices Windows pour forcer Pillow à l'utiliser
    chemin_police = "C:\\Windows\\Fonts\\arial.ttf"
    if not os.path.exists(chemin_police):
        chemin_police = "arial.ttf" # Repli local au cas où
        
    try:
        font_title = ImageFont.truetype(chemin_police, 32)       # Grand pour l'Identité / Compétences
        font_text = ImageFont.truetype(chemin_police, 18)        # Très lisible pour les lignes blanches
        font_scores = ImageFont.truetype(chemin_police, 34)      # Gros chiffres pour les ronds d'approches
        font_comp_title = ImageFont.truetype(chemin_police, 22)  # Titres des compétences
    except IOError:
        # Si Windows bloque vraiment l'accès, on utilise la police par défaut mais le rendu sera altéré
        font_title = font_text = font_scores = font_comp_title = ImageFont.load_default()

    # --- 🗺️ CARTOGRAPHIE EN PIXELS RÉELS (Basée sur une image de 1000px+ de large) ---
    
    # --- 📐 RECALIBRAGE TOTAL DES COORDONNÉES PIXELS ---
    
    # 1. Identité & Citation (Sautent par-dessus l'étiquette sombre directement dans la grande zone blanche)
    draw.text((450, 162), profil["nom"], fill="#1c2d37", font=font_title)
    draw.text((450, 268), profil.get("citation", ""), fill="#385d6e", font=font_text)

    # 2. Approches / Difficultés (Centrées au milieu des petites cases blanches de leur propre colonne)
    draw.text((315, 342), str(profil["approches"]["action"]), fill="#b13434", font=font_scores)
    draw.text((315, 410), str(profil["approches"]["discretion"]), fill="#b13434", font=font_scores)
    draw.text((315, 476), str(profil["approches"]["intellect"]), fill="#b13434", font=font_scores)
    draw.text((315, 544), str(profil["approches"]["social"]), fill="#b13434", font=font_scores)

    # 3. Caractéristiques du bas (Poussées au début des rectangles blancs horizontaux)
    draw.text((450, 612), profil.get("traits", ""), fill="#1c2d37", font=font_text)
    draw.text((450, 646), profil.get("entrave", ""), fill="#b13434", font=font_text)
    draw.text((450, 680), profil.get("langues", "Français"), fill="#1c2d37", font=font_text)
    draw.text((450, 785), f"Ancêtre lié : {profil.get('ancetre_prioritaire', 'Aucun')}", fill="#1c2d37", font=font_text)

    # 4. Équipement (Décalé vers la droite pour s'aligner sous le bandeau "ÉQUIPEMENT")
    emb = profil.get("equipement_emblematique", ["", ""])
    std = profil.get("equipement_standard", "")
    liste_eq = [f"✦ {x}" for x in emb if x]
    if std:
        liste_eq.extend([f"• {x.strip()}" for x in std.split(",") if x.strip()])
    
    y_eq = 352
    for item in liste_eq[:6]:
        draw.text((540, y_eq), item, fill="#1c2d37", font=font_text)
        y_eq += 34

    # 5. Compétences (Poussées tout à droite, au cœur des 3 grands panneaux clairs de l'Animus)
    comps = profil.get("competences_actives", ["-- Emplacement Vide --", "-- Emplacement Vide --", "-- Emplacement Vide --"])
    atouts_presents = [c for c in comps if c != "-- Emplacement Vide --"]
    
    # Les coordonnées X passent à 1100 pour atterrir directement dans les volets de droite
    coordonnees_competences = [
        (1100, 660),  # Compétence 1 (Bas)
        (1100, 370),  # Compétence 2 (Milieu)
        (1100, 80)    # Compétence 3 (Haut)
    ]
    
    for idx, coords in enumerate(coordonnees_competences):
        if idx < len(atouts_presents):
            c_nom = atouts_presents[idx]
            # Titre de la compétence
            draw.text((coords[0], coords[1]), f"⚡ {c_nom}", fill="#1c2d37", font=font_comp_title)
            
            # Contenu / Description automatique avec retour à la ligne
            c_desc = data_globales.get("competences_globales", {}).get(c_nom, "")
            if c_desc:
                lignes_desc = textwrap.wrap(c_desc, width=32) # Moins large pour ne pas mordre le logo central
                y_offset = coords[1] + 32
                for ligne in lignes_desc[:4]:
                    draw.text((coords[0], y_offset), ligne, fill="#385d6e", font=font_text)
                    y_offset += 24

    img_byte_arr = io.BytesIO()
    base_image.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()


# --- LOGIQUE DE GESTION DES DONNÉES ---
DB_FILE = "cellule_data.json"

def charger_donnees():
    base_default = {
        "descendants": {},
        "competences_globales": {
            "AGILE": "Lorsque vous effectuez un test de Discrétion lors d'une infiltration, vous bénéficiez de 1 majoration gratuite.",
            "ALERTE": "Lorsque vous effectuez un test de Réaction, vous pouvez relancer jusqu'à 2 Abstergo.",
            "ASSASSINAT": "Lorsque vous effectuez un test de Discrétion lors d'une situation où vous faites appel à vos capacités d'Assassin, vous pouvez considérer jusqu'à 2 Intellect comme 1 correspondance supplémentaire chacun.",
            "BLUFF": "Lorsque vous effectuez un test Social lors d'un acte de tromperie, vous bénéficiez de 1 majoration gratuite.",
            "CHARME": "Lorsque vous effectuez un test Social lors d'une situation où vous faites appel à vos capacités de séduction, vous pouvez ajouter 1 correspondance. De plus, lorsque vous effectuez un test Social, vous pouvez utiliser 2 Intellect pour obtenir une information supplémentaire de la part de quelqu'un ou de quelque chose impliqué dans la scène.",
            "COMBATTANT NÉ": "Lorsque vous effectuez un test d'Action en combat, vous obtenez une majoration gratuite.",
            "COMPAGNON ANIMAL": "Votre esprit et celui de votre animal ne font qu'un, ce qui vous permet de voir à travers ses yeux et de contrôler ses mouvements. Votre compagnon peut vous aider en combat ou faire diversion, détournant l'attention des gens. Enfin, lorsque vous effectuez un test d'Action ou de Discrétion, vous pouvez relancer 1 Abstergo.",
            "COURSE LIBRE": "Lorsque vous pratiquez la course libre, vous pouvez ajouter 1 correspondance à tout test d'Action lié. De plus, lorsque vous effectuez un test d'Action, vous pouvez utiliser 2 Discrétion pour disparaître du champ de vision de vos adversaires.",
            "CRAN": "Lorsque vous effectuez un test d'Intellect, vous pouvez considérer jusqu'à 1 Action comme une correspondance supplémentaire.",
            "DÉPLACEMENTS STRATÉGIQUES": "Lorsque vous effectuez un test d'Action, vous pouvez considérer jusqu'à 1 Intellect comme 1 correspondance supplémentaire.",
            "FORMATION DE LA CONFRÉRIE": "Lorsque vous utilisez une arme secrète, vous pouvez considérer 1 Credo comme 1 correspondance supplémentaire. Ceci en plus de toute correspondance accordée par l'activation d'un équipement emblématique (arme secrète).",
            "HYPNOSE": "Lorsque vous effectuez un test Social, vous pouvez considérer jusqu'à 1 Discrétion comme une correspondance supplémentaire.",
            "MOUVEMENTS TROMPEURS": "Lorsque vous effectuez un test d'Action lors d'une situation où vous faites appel à vos capacités de tromperie, vous pouvez considérer jusqu'à 2 Social comme 1 correspondance supplémentaire chacun.",
            "OBSERVATEUR": "Lorsque vous effectuez un test d'Intellect dans une situation où vous faites appel à vos capacités d'investigation, vous pouvez considérer jusqu'à 2 Discrétion comme une correspondance supplémentaire.",
            "PASSE-PASSE": "Lorsque vous essayez de dissimuler un petit objet ou d'en dérober un, vous pouvez ajouter 1 correspondance à tout test de Discrétion lié. En outre, lorsque vous effectuez un test d'Action ou Social, vous pouvez utiliser 2 Discrétion pour dérober un petit objet à une personne impliquée dans la scène.",
            "PRESSION": "Lorsque vous effectuez un test Social lors d'une situation où vous faites appel à vos capacités d'intimidation, vous pouvez considérer jusqu'à 2 Action comme 1 correspondance supplémentaire chacun.",
            "RUSE": "Lorsque vous effectuez un test d'Intellect durant une activité de bricolage, vous bénéficiez de 1 majoration gratuite.",
            "SAPEUR": "Lorsque vous tentez de saboter un appareil, vous pouvez ajouter 1 correspondance à tout test d'Intellect lié. De plus, lorsque vous effectuez un test d'Action ou de Discrétion, vous pouvez utiliser 2 Intellect pour créer un leurre ou une diversion durant la scène.",
            "SE CACHER AU GRAND JOUR": "Lorsque vous effectuez un test de Discrétion, vous pouvez considérer jusqu'à 1 Social comme une correspondance supplémentaire.",
            "SENS D'AIGLE": "Le Sens d'aigle affine vos sens au point de pouvoir percevoir les battements de cœur de votre cible dans la zone ou même prévoir sa prochaine action. De plus, vous pouvez entrapercevoir les souvenirs de vos cibles lorsque vous les tuez, obtenant ainsi toutes les informations qu'elles ont à offrir.",
            "VISION D'AIGLE": "La Vision d'aigle est une forme de perception extrasensorielle, ou « sixième sens », et l'un des dons de vos gènes Isu. Vous pouvez aisément repérer les alliés, ennemis, objectifs, sources d'informations et cibles à courte portée. En outre, lorsque vous effectuez un test d'Approche, vous pouvez considérer 1 Intellect comme 1 correspondance supplémentaire."
        },
        "ancetres_officiels": {
            # --- LA ROYAUTÉ ROMAINE ---
            "romulus": {
                "nom": "Romulus", "periode": "Royauté romaine",
                "citation": "Les mots enseignent, les exemples entraînent.",
                "action": 2, "discretion": 3, "intellect": 2, "social": 1,
                "traits": "Vétéran, Déterminé", "entrave": "Agressif", "langues": "Étrusque, grec ancien, latin",
                "equipement": "Bouclier, Épée, Armure de roi, Lance, Médaillon de Mars, Fronde"
            },
            "prima": {
                "nom": "Prima", "periode": "Royauté romaine",
                "citation": "Nous sommes façonnés by les tempêtes que nous traversons.",
                "action": 2, "discretion": 2, "intellect": 2, "social": 2,
                "traits": "Rapide, Rusée", "entrave": "Intrépide", "langues": "Dialecte sabin, grec ancien, latin",
                "equipement": "Faucille, Lame dissimulée, Fronde, Livre des Lois, Brassard 'Boucliers de Mars', Bijoux"
            },
            "venator": {
                "nom": "Venator", "periode": "Royauté romaine",
                "citation": "Sois le prédateur, pas la proie.",
                "action": 2, "discretion": 1, "intellect": 2, "social": 3,
                "traits": "Patient, Chasseur", "entrave": "Irascible", "langues": "Latin",
                "equipement": "Arc et flèches, Dague, Outre, Appât, Paillasse, Corde"
            },
            "gardienne_du_feu": {
                "nom": "La Gardienne du Feu", "periode": "Royauté romaine",
                "citation": "Seuls les dieux je sers.",
                "action": 3, "discretion": 2, "intellect": 2, "social": 1,
                "traits": "Fervente, Érudite", "entrave": "Pieuse", "langues": "Étrusque, latin, osque",
                "equipement": "Torche de vestale, Herbes médicinales, Silex, Flasque d'huile, Fronde, Parchemins du temple"
            },
            # --- ANTIQUITÉ GRECQUE ---
            "kassandra": {
                "nom": "Kassandra", "periode": "Antiquité grecque",
                "citation": "Si j'étais ta punition, tu serais déjà mort.",
                "action": 2, "discretion": 2, "intellect": 2, "social": 2,
                "traits": "Agile, Spartiate", "entrave": "Clémente", "langues": "Grec ancien, laconien",
                "equipement": "Lance de Léonidas, Armure de misthios, Arc et flèches, Bouteille de feu grégeois, Phobos (cheval), Ikaros (aigle)"
            },
            "xenia": {
                "nom": "Xenia", "periode": "Antiquité grecque",
                "citation": "J'ai un faible pour les choses rares.",
                "action": 2, "discretion": 3, "intellect": 2, "social": 1,
                "traits": "Contacts, Pirate", "entrave": "Cupidité", "langues": "Grec ancien",
                "equipement": "Marteau de guerre, Documents de contrebande, Armure, Cartes maritimes, Dague, Bourse de drachmes"
            },
            "herodote": {
                "nom": "Hérodote", "periode": "Antiquité grecque",
                "citation": "Je suis un conteur, du moins, je l'étais. Cette guerre nous pousse à changer.",
                "action": 3, "discretion": 2, "intellect": 1, "social": 2,
                "traits": "Érudit, Observateur", "entrave": "Neutralité", "langues": "Attique, dorien, grec ancien, laconien",
                "equipement": "Cartes et documents, Bouteille de feu grégeois, Bâton de combat, Sacoche à parchemins, Nécessaire de crochetage, Dague"
            },
            "griffe_de_nemee": {
                "nom": "La Griffe de Némée", "periode": "Antiquité grecque",
                "citation": "Je suis né pour porter cette épée et ce bouclier.",
                "action": 1, "discretion": 3, "intellect": 2, "social": 2,
                "traits": "Hardi, Combattant d'arène", "entrave": "Égoïste", "langues": "Grec ancien",
                "equipement": "Épée, Bouclier, Armure, Javelot, Rouleaux de primes, Médaillon d'Arès"
            },
            # --- 2NDE GUERRE MONDIALE ---
            "major_gallagher": {
                "nom": "Major Gallagher", "periode": "Seconde Guerre mondiale",
                "citation": "Je m'apprête à vous tuer avec cette tasse de thé.",
                "action": 1, "discretion": 2, "intellect": 2, "social": 3,
                "traits": "Vigueur, Béret vert", "entrave": "Code d'honneur", "langues": "Allemand, anglais",
                "equipement": "Khukuri (couteau), Browning (pistolet), Sten (mitraillette), Béret vert, Cape anti-gaz, Appareil photo Leica III"
            },
            "lambassadeur": {
                "nom": "L'Ambassadeur", "periode": "Seconde Guerre mondiale",
                "citation": "Quand l'injustice devient la règle, se rebeller est un devoir.",
                "action": 2, "discretion": 2, "intellect": 2, "social": 2,
                "traits": "Féroce, Rapide", "entrave": "Vengeance", "langues": "Allemand, anglais, français, polonais, russe",
                "equipement": "Revolver Webley, Fusil Lebel modèle 1886, Machette (bolo), Masque à gaz, Grenade M1 « Frangible », Couteau pliant"
            },
            "nancy_drake": {
                "nom": "Nancy Drake", "periode": "Seconde Guerre mondiale",
                "citation": "La liberté est la seule chose qui vaille la peine de vivre.",
                "action": 2, "discretion": 2, "intellect": 2, "social": 2,
                "traits": "Impitoyable, Saboteuse", "entrave": "Vengeance", "langues": "Allemand, anglais, français",
                "equipement": "Berthier modèle 92 (fusil), Luger P08 (pistolet), Grenade à manche, Grenade fumigène, Morphine, Fairbairn-Sykes (couteau)"
            },
            "reboante": {
                "nom": "Reboante", "periode": "Seconde Guerre mondiale",
                "citation": "Il faut prendre parti, car il n'y a pas de courage dans la neutralité.",
                "action": 1, "discretion": 1, "intellect": 3, "social": 3,
                "traits": "Altruiste, Combatif", "entrave": "Passionné", "langues": "Français, hébreu, italien",
                "equipement": "Mitraillette, Explosifs, Couteau à cran d'arrêt, Vin, Grenade à manche, Pinces coupantes"
            },
            "josephine_boulanger": {
                "nom": "Joséphine Boulanger", "periode": "Seconde Guerre mondiale",
                "citation": "Je danserai toute ma vie... J'aimerais mourir à bout de souffle, épuisée, à la fin d'une danse.",
                "action": 3, "discretion": 2, "intellect": 2, "social": 1,
                "traits": "Espionne, Artiste", "entrave": "Justice", "langues": "Allemand, anglais, espagnol, français",
                "equipement": "FP-45 Liberator (pistolet), Couteau dissimulé, Robe élégante, Partitions musicales, Briquet, Cigarettes"
            },
            # --- ÂGE VIKING ---
            "eivor": {
                "nom": "Eivor", "periode": "Âge des Vikings",
                "citation": "...C'est à moi de tisser ma destinée.",
                "action": 2, "discretion": 2, "intellect": 2, "social": 2,
                "traits": "Rusée, Dure à cuire", "entrave": "Code d'honneur", "langues": "Anglais, français, vieux norrois",
                "equipement": "Armure du clan du Grand Corbeau, Lame secrète, Arc et flèches, Deux haches, Corde, Pendentif d'Odin"
            },
            "valka": {
                "nom": "Valka", "periode": "Âge des Vikings",
                "citation": "J'ai besoin de silence pour entendre les chants de la nature.",
                "action": 3, "discretion": 2, "intellect": 1, "social": 2,
                "traits": "Sage, Respectée", "entrave": "Superstitieuse", "langues": "Vieux norrois",
                "equipement": "Plantes hallucinogènes, Poudres alchimiques, Runes de divination, Dague en os, Tenue de volva, Peintures rituelles"
            },
            "chevalier_dragon": {
                "nom": "Le Chevalier Dragon", "periode": "Âge des Vikings",
                "citation": "Je combattrai quiconque refuse la liberté à autrui.",
                "action": 1, "discretion": 3, "intellect": 2, "social": 2,
                "traits": "Stoïque, Robuste", "entrave": "Impétueux", "langues": "Anglais, vieux norrois",
                "equipement": "Armure de chevalier, Claíomh Solais (épée), Outre de vin, Scutum (bouclier), Seax (couteau), Merlin (cheval)"
            },
            "hytham": {
                "nom": "Hytham", "periode": "Âge des Vikings",
                "citation": "Ce n'est pas une question de valeur, mais de dévotion envers le credo.",
                "action": 2, "discretion": 1, "intellect": 2, "social": 3,
                "traits": "Discipliné, Vigilant", "entrave": "Idéaliste", "langues": "Anglais, grec byzantin, latin, vieux norrois",
                "equipement": "Lame secrète, Saif (épée), Dague, Bombes fumigènes, Dagues de lancer, Tunique d'acolyte"
            },
            # --- AUTRES ARCHIVES ---
            "altair": {
                "nom": "Altaïr Ibn-La'Ahad", "periode": "Troisième Croisade",
                "citation": "Je comprends maintenant que le Credo ne nous demande pas d'être libres, mais d'être sages.",
                "action": 2, "discretion": 1, "intellect": 3, "social": 2,
                "traits": "Sage, Vétéran", "entrave": "Impulsif", "langues": "Arabe, français, grec, mongol",
                "equipement": "Doubles lames secrètes, Cape d'assassin, Épée, Épée courte, Couteaux de lancer, Armure de cuir"
            },
            "shao_jun": {
                "nom": "Shao Jun", "periode": "Dynastie Ming",
                "citation": "Tant que vous n'avez pas ressenti la soif de vengeance, vous ignorerez la rage qu'elle insuffle.",
                "action": 2, "discretion": 2, "intellect": 2, "social": 2,
                "traits": "Wushu, Vigilante", "entrave": "Impitoyable", "langues": "Chinois, italien, japonais",
                "equipement": "Dague à corde, Jian écarlate (épée), Fléchettes appeaux, Lame de semelle, Aiguilles de lancer, Pétards"
            },
            "akira": {
                "nom": "Akira", "periode": "Sengoku-Jidai",
                "citation": "Je mourrai par le sabre. Le mien ou celui de mon ennemi.",
                "action": 1, "discretion": 3, "intellect": 2, "social": 2,
                "traits": "Résistance, Honneur", "entrave": "Inflexible", "langues": "Japonais",
                "equipement": "Sabre familial, Arc yumi, Armure de samouraï, Éventail pliable, Wakizashi, Gourde en bambou"
            },
            "mochizuki_chiyome": {
                "nom": "Mochizuki Chiyome", "periode": "Sengoku-Jidai",
                "citation": "On enseigne aux kunoichi à triompher avant même d'avoir dégainé la blade.",
                "action": 2, "discretion": 2, "intellect": 2, "social": 2,
                "traits": "Ninjutsu, Agilité", "entrave": "Ambition", "langues": "Chinois, japonais",
                "equipement": "Lame secrète, Poison d'amandes, Tanto, Grappin, Tetsubishi (chausse-trappes), Torinoko (pétards)"
            },
            "arno_dorian": {
                "nom": "Arno Dorian", "periode": "Révolution française",
                "citation": "Tout ce que nous faisons, tout ce que nous sommes... débute... et prend fin... avec nous.",
                "action": 2, "discretion": 2, "intellect": 2, "social": 2,
                "traits": "Impitoyable, Érudit", "entrave": "Rédemption", "langues": "Français",
                "equipement": "Sabre d'officier, Lame fantôme, Lame secrète, Pistolet à silex, Nécessaire de crochetage, Bombe à gaz toxique"
            }
        }
    }
    
    if not os.path.exists(DB_FILE):
        return base_default
    with open(DB_FILE, "r", encoding="utf-8") as f:
        local_data = json.load(f)
    for k, v in base_default.items():
        if k not in local_data:
            local_data[k] = v
    return local_data

def sauvegarder_donnees(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

data = charger_donnees()

# --- FORMATEUR D'ÉQUIPEMENT ---
def formater_equipement_html(texte_equipement):
    if not texte_equipement:
        return ""
    if "\n" in texte_equipement:
        lignes = [item.strip() for item in texte_equipement.split("\n") if item.strip()]
    else:
        lignes = [item.strip() for item in texte_equipement.split(",") if item.strip()]
        
    html_formatted = []
    for idx, item in enumerate(lignes):
        if idx < 2:
            html_formatted.append(f"• <b>✦ {item}</b>")
        else:
            html_formatted.append(f"• {item}")
            
    return "<br>".join(html_formatted)

# --- DESIGN DES CARTES STYLISÉES ANCIENNES ---
HTML_ANCESTRE_TEMPLATE = """
<div style="background-color: #dbe4e9; border-radius: 12px; padding: 15px; border: 1px solid #b0c2cc; font-family: 'Arial', sans-serif; color: #1c2d37; margin-bottom: 20px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); min-height: 520px;">
    <div style="background-color: #56727c; color: #dbe4e9; font-size: 0.75rem; font-weight: bold; text-transform: uppercase; padding: 4px 10px; border-radius: 6px; display: inline-block; margin-bottom: 8px; letter-spacing: 0.5px;">
        ⏳ {periode}
    </div>
    <div style="background-color: #385d6e; padding: 10px; border-radius: 4px; color: white;">
        <h3 style="margin: 0; font-size: 1.25rem; text-transform: uppercase; color: white; letter-spacing: 1px;">{nom}</h3>
    </div>
    <div style="background-color: #cbd7df; font-style: italic; padding: 8px; font-size: 0.85rem; border-left: 3px solid #385d6e; margin: 10px 0;">
        "{citation}"
    </div>
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 10px;">
        <tr style="border-bottom: 1px solid #b0c2cc;">
            <td style="width: 20%; font-size: 1.4rem; font-weight: bold; color: #b13434; text-align: center; background: #eef2f5;">{action}</td>
            <td style="width: 35%; font-size: 0.75rem; text-transform: uppercase; font-weight: bold; padding-left: 5px; color: #555;">💥 ACTION</td>
            <td style="font-size: 0.85rem; padding-left: 10px; font-weight: bold; color: #2c3e50;">🎒 ÉQUIPEMENT</td>
        </tr>
        <tr style="border-bottom: 1px solid #b0c2cc;">
            <td style="font-size: 1.4rem; font-weight: bold; color: #b13434; text-align: center; background: #eef2f5;">{discretion}</td>
            <td style="font-size: 0.75rem; text-transform: uppercase; font-weight: bold; padding-left: 5px; color: #555;">👥 DISCRÉTION</td>
            <td rowspan="3" style="font-size: 0.8rem; vertical-align: top; padding: 8px 10px; color: #333; line-height: 1.4; background: #f4f7f9; border-radius: 4px;">{equipement_html}</td>
        </tr>
        <tr style="border-bottom: 1px solid #b0c2cc;">
            <td style="font-size: 1.4rem; font-weight: bold; color: #b13434; text-align: center; background: #eef2f5;">{intellect}</td>
            <td style="font-size: 0.75rem; text-transform: uppercase; font-weight: bold; padding-left: 5px; color: #555;">👁 INTELLECT</td>
        </tr>
        <tr>
            <td style="font-size: 1.4rem; font-weight: bold; color: #b13434; text-align: center; background: #eef2f5;">{social}</td>
            <td style="font-size: 0.75rem; text-transform: uppercase; font-weight: bold; padding-left: 5px; color: #555;">🎭 SOCIAL</td>
        </tr>
    </table>
    <div style="background: #eef2f5; padding: 6px; border-radius: 4px; font-size: 0.85rem; font-weight: bold; margin-bottom: 5px; border: 1px solid #cbd7df;">✨ TRAITS : <span style="font-weight: normal;">{traits}</span></div>
    <div style="background: #eef2f5; padding: 6px; border-radius: 4px; font-size: 0.85rem; font-weight: bold; color: #b13434; margin-bottom: 5px; border: 1px solid #cbd7df;">⚠️ ENTRAVE : <span style="font-weight: normal; color: #555;">{entrave}</span></div>
    <div style="background: #eef2f5; padding: 6px; border-radius: 4px; font-size: 0.85rem; font-weight: bold; border: 1px solid #cbd7df;">🌐 LANGUES : <span style="font-weight: normal; color: #555;">{langues}</span></div>
</div>
"""

# --- DESIGN DES CARTES UNIFIÉES POUR LES DESCENDANTS ---
HTML_DESCENDANT_TEMPLATE = """
<div style="background-color: #dbe4e9; border-radius: 12px; padding: 15px; border: 1px solid #b0c2cc; font-family: 'Arial', sans-serif; color: #1c2d37; margin-bottom: 20px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); min-height: 520px;">
    <div style="background-color: #56727c; color: #dbe4e9; font-size: 0.75rem; font-weight: bold; text-transform: uppercase; padding: 4px 10px; border-radius: 6px; display: inline-block; margin-bottom: 8px; letter-spacing: 0.5px;">
        ⏳ {periode}
    </div>
    <div style="background-color: #385d6e; padding: 10px; border-radius: 4px; color: white;">
        <h3 style="margin: 0; font-size: 1.25rem; text-transform: uppercase; color: white; letter-spacing: 1px;">{nom}</h3>
    </div>
    <div style="background-color: #cbd7df; font-style: italic; padding: 8px; font-size: 0.85rem; border-left: 3px solid #385d6e; margin: 10px 0;">
        "{citation}"
    </div>
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 10px;">
        <tr style="border-bottom: 1px solid #b0c2cc;">
            <td style="width: 20%; font-size: 1.4rem; font-weight: bold; color: #b13434; text-align: center; background: #eef2f5;">{action}</td>
            <td style="width: 35%; font-size: 0.75rem; text-transform: uppercase; font-weight: bold; padding-left: 5px; color: #555;">💥 ACTION</td>
            <td style="font-size: 0.85rem; padding-left: 10px; font-weight: bold; color: #2c3e50;">🎒 ÉQUIPEMENT</td>
        </tr>
        <tr style="border-bottom: 1px solid #b0c2cc;">
            <td style="font-size: 1.4rem; font-weight: bold; color: #b13434; text-align: center; background: #eef2f5;">{discretion}</td>
            <td style="font-size: 0.75rem; text-transform: uppercase; font-weight: bold; padding-left: 5px; color: #555;">👥 DISCRÉTION</td>
            <td rowspan="3" style="font-size: 0.8rem; vertical-align: top; padding: 8px 10px; color: #333; line-height: 1.4; background: #f4f7f9; border-radius: 4px;">{equipement_html}</td>
        </tr>
        <tr style="border-bottom: 1px solid #b0c2cc;">
            <td style="font-size: 1.4rem; font-weight: bold; color: #b13434; text-align: center; background: #eef2f5;">{intellect}</td>
            <td style="font-size: 0.75rem; text-transform: uppercase; font-weight: bold; padding-left: 5px; color: #555;">👁 INTELLECT</td>
        </tr>
        <tr>
            <td style="font-size: 1.4rem; font-weight: bold; color: #b13434; text-align: center; background: #eef2f5;">{social}</td>
            <td style="font-size: 0.75rem; text-transform: uppercase; font-weight: bold; padding-left: 5px; color: #555;">🎭 SOCIAL</td>
        </tr>
    </table>
    <div style="background: #eef2f5; padding: 6px; border-radius: 4px; font-size: 0.85rem; font-weight: bold; margin-bottom: 5px; border: 1px solid #cbd7df;">✨ TRAITS : <span style="font-weight: normal;">{traits}</span></div>
    <div style="background: #eef2f5; padding: 6px; border-radius: 4px; font-size: 0.85rem; font-weight: bold; color: #b13434; margin-bottom: 5px; border: 1px solid #cbd7df;">⚠️ ENTRAVE : <span style="font-weight: normal; color: #555;">{entrave}</span></div>
    <div style="background: #eef2f5; padding: 6px; border-radius: 4px; font-size: 0.85rem; font-weight: bold; margin-bottom: 5px; border: 1px solid #cbd7df;">🌐 LANGUES : <span style="font-weight: normal; color: #555;">{langues}</span></div>
    <div style="background: #eef2f5; padding: 6px; border-radius: 4px; font-size: 0.85rem; font-weight: bold; margin-bottom: 5px; border: 1px solid #cbd7df;">🔗 ANCÊTRE LIÉ : <span style="color: #385d6e; font-weight: bold;">{ancetre_nom}</span></div>
    <div style="background: #eef2f5; padding: 6px; border-radius: 4px; font-size: 0.85rem; font-weight: bold; border: 1px solid #cbd7df;">🎴 COMPÉTENCES ANCRÉES :{competences_badges_html}</div>
</div>
"""

# --- DESIGN DES CARTES COMPÉTENCES STYLISÉES ---
HTML_SKILL_CARD_TEMPLATE = """
<div style="background: linear-gradient(135deg, #445f6e, #2c3e4a); border-radius: 10px; padding: 18px; border: 1px solid #5d7482; font-family: 'Arial', sans-serif; color: #eaf1f4; margin-bottom: 20px; box-shadow: 2px 4px 12px rgba(0,0,0,0.15); min-height: 220px; position: relative;">
    <div style="border-bottom: 1px solid #5d7482; padding-bottom: 8px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
        <span style="font-size: 1.15rem; font-weight: bold; text-transform: uppercase; color: #ffffff;">{titre}</span>
        <span style="font-size: 0.65rem; background: #385d6e; color: #cbd7df; padding: 2px 6px; border-radius: 4px; font-weight: bold;">🧬 ABSTERGO CORE</span>
    </div>
    <div style="font-size: 0.9rem; line-height: 1.5; color: #dbe4e9; margin-bottom: 15px;">{description}</div>
    <div style="position: absolute; bottom: 10px; left: 18px; font-size: 0.7rem; text-transform: uppercase; color: #879ea9; font-weight: bold;">▮▮▮ 🗃️ CARTE COMPÉTENCE ANIMUS</div>
</div>
"""

# --- INTERFACE ---
st.set_page_config(page_title="Animus OS", layout="wide")
st.title("🦅 Système de Gestion de Cellule - Animus OS")

tab_descendants, tab_ancetres, tab_competences = st.tabs([
    "👤 Fiches des Descendants", 
    "📜 Base Génétique des Ancêtres", 
    "🃏 Bibliothèque des Compétences"
])

# =========================================================================
# 🧬 SUPSUPPROTOCOLE CENTRALISÉ (POP-UP MODALE DE SÉCURITÉ)
# =========================================================================
@st.dialog("🚨 PROTOCOLE DE PURGE DE DONNÉES SECRÈTES")
def valider_suppression_donnees(type_donnee, cle, intitule_texte):
    st.error(f"⚠️ **ALERTE CRITIQUE :** Vous demandez la destruction de l'élément : **{intitule_texte}**.")
    st.write("Cette action effacera définitivement le bloc de la mémoire flash.")
    
    c_pop1, c_pop2 = st.columns(2)
    if c_pop1.button("🔥 CONFIRMER LA PURGE", type="primary", use_container_width=True):
        if type_donnee == "descendant":
            del data["descendants"][cle]
            if st.session_state.get("active_view_id") == cle:
                st.session_state.active_view_id = None
        elif type_donnee == "ancetre":
            del data["ancetres_officiels"][cle]
        elif type_donnee == "competence":
            del data["competences_globales"][cle]
            
        sauvegarder_donnees(data)
        st.success("Données nettoyées avec succès.")
        st.rerun()
        
    if c_pop2.button("❌ ABANDONNER PROTOCOLE", type="secondary", use_container_width=True):
        st.rerun()

# =========================================================================
# 1. ONGLET : DESCENDANTS (INTERFACE TRITYQUE ET ATELIER FILTRÉ)
# =========================================================================
with tab_descendants:
    st.header("🦅 Matrice Animus : Registre des Descendants")

    # Initialisations des variables de session globales
    if "tmp_repart" not in st.session_state: st.session_state.tmp_repart = "3, 3, 2, 2"
    if "tmp_act" not in st.session_state: st.session_state.tmp_act = 3
    if "tmp_disc" not in st.session_state: st.session_state.tmp_disc = 3
    if "tmp_intel" not in st.session_state: st.session_state.tmp_intel = 2
    if "tmp_soc" not in st.session_state: st.session_state.tmp_soc = 2
    
    if "edit_target_id" not in st.session_state: st.session_state.edit_target_id = None
    if "active_view_id" not in st.session_state: st.session_state.active_view_id = None
    if "wizard_step" not in st.session_state: st.session_state.wizard_step = 1

    # Barre de recherche globale haute
    col_tools_1, col_tools_2 = st.columns([7, 3])
    with col_tools_2:
        if st.button("➕ Initialiser un nouveau Descendant", type="primary", use_container_width=True, key="btn_init_global_desc"):
            st.session_state.edit_target_id = "NOUVEAU"
            st.rerun()
    with col_tools_1:
        recherche_desc = st.text_input("🔍 Rechercher un agent par son identité...", "", key="search_bar_desc").strip().lower()

    # --- ATELIER DE TRAVAIL UNIQUE PLEIN ÉCRAN (WIZARD PAR ÉTAPES) ---
    if st.session_state.edit_target_id:
        target = st.session_state.edit_target_id
        is_new = (target == "NOUVEAU")
        
        st.write("---")
        col_title_wizard, col_close_wizard = st.columns([8, 2])
        col_title_wizard.subheader("🛠️ Atelier de Configuration Synaptique" + (" (Nouveau Sujet)" if is_new else " (Modification)"))
        
        if col_close_wizard.button("❌ Annuler et fermer l'atelier", use_container_width=True):
            # 1. Purge complète des variables de saisie de l'atelier
            cles_a_nettoyer = [
                "w_nom", "w_cit", "w_emb1", "w_emb2", 
                "w_ord1", "w_ord2", "w_ord3", "w_ord4",
                "w_trait1", "w_trait2", "w_entrave", "w_langues", 
                "w_xp_level", "wiz_slot_comp1", "wiz_slot_comp2", "wiz_slot_comp3", 
                "wiz_anc_select", f"init_done_{target}"
            ]
            for k in cles_a_nettoyer:
                if k in st.session_state:
                    del st.session_state[k]
            
            # 2. Réinitialisation des états de l'atelier
            st.session_state.edit_target_id = None
            st.session_state.wizard_step = 1
            st.rerun()

        # Jauge de progression calculée selon l'étape actuelle
        progression_map = {1: 0.33, 2: 0.66, 3: 1.0}
        st.progress(progression_map[st.session_state.wizard_step], text=f"Étape {st.session_state.wizard_step} / 3 en cours de traitement...")

        # Chargement initial des données en Session State si modification
        if not is_new and target in data["descendants"]:
            ag_data = data["descendants"][target]
            if f"init_done_{target}" not in st.session_state:
                st.session_state.w_nom = ag_data["nom"]
                st.session_state.w_cit = ag_data.get("citation", "")
                st.session_state.w_entrave = ag_data["entrave"]
                ts = ag_data["traits"].split(", ")
                st.session_state.w_trait1 = ts[0] if len(ts) > 0 else ""
                st.session_state.w_trait2 = ts[1] if len(ts) > 1 else ""
                emb_data = ag_data["equipement_emblematique"]
                st.session_state.w_emb1 = emb_data[0] if len(emb_data) > 0 else ""
                st.session_state.w_emb2 = emb_data[1] if len(emb_data) > 1 else ""
                stds_data = [x.strip() for x in ag_data.get("equipement_standard", "").split(",") if x.strip()]
                for i in range(4): st.session_state[f"w_ord{i+1}"] = stds_data[i] if i < len(stds_data) else ""
                st.session_state.tmp_act = ag_data["approches"]["action"]
                st.session_state.tmp_disc = ag_data["approches"]["discretion"]
                st.session_state.tmp_intel = ag_data["approches"]["intellect"]
                st.session_state.tmp_soc = ag_data["approches"]["social"]
                st.session_state.w_langues = ag_data.get("langues", "Français")
                st.session_state.w_xp_level = ag_data.get("niveau_xp", 1)
                
                # Charger les compétences enregistrées
                c_actives_old = ag_data.get("competences_actives", ["-- Emplacement Vide --", "-- Emplacement Vide --", "-- Emplacement Vide --"])
                st.session_state.wiz_slot_comp1 = c_actives_old[0]
                st.session_state.wiz_slot_comp2 = c_actives_old[1]
                st.session_state.wiz_slot_comp3 = c_actives_old[2]
                st.session_state.wiz_anc_select = ag_data.get("ancetre_prioritaire", "")
                st.session_state[f"init_done_{target}"] = True

        step = st.session_state.wizard_step
        col_form_panel, col_preview_panel = st.columns([6, 6])
        
        with col_form_panel:
            # --- ÉTAPE 1 : IDENTITÉ ---
            if step == 1:
                st.markdown("#### 👤 Étape 1 : Identité & Philosophie")
                w_nom = st.text_input("Nom de l'Agent *", value=st.session_state.get("w_nom", ""), key="input_wizard_nom")
                w_cit = st.text_input("Citation / Devise Fondamentale", value=st.session_state.get("w_cit", ""), key="input_wizard_cit")
                
                st.write("")
                if st.button("➡️ Continuer vers les Approches", type="primary", use_container_width=True):
                    if w_nom.strip():
                        # SAUVEGARDE EN MÉMOIRE PERSISTANTE
                        st.session_state.w_nom = w_nom.strip()
                        st.session_state.w_cit = w_cit.strip()
                        st.session_state.wizard_step = 2
                        st.rerun()
                    else:
                        st.error("❌ Le nom de l'agent est requis pour continuer.")

            # --- ÉTAPE 2 : APPROCHES & MATÉRIEL ---
            elif step == 2:
                st.markdown("#### 📊 Étape 2 : Approches & Équipement")
                st.write("**💥 Distribution d'Effort Réglementaire**")
                repart_cible = st.selectbox("Grille cible :", ["3, 3, 2, 2", "3, 3, 3, 1"], index=0 if st.session_state.tmp_repart == "3, 3, 2, 2" else 1, key="wizard_repart_select")
                st.session_state.tmp_repart = repart_cible
                
                cx1, cx2, cx3, cx4 = st.columns(4)
                w_act = cx1.number_input("Action", 1, 3, st.session_state.tmp_act, key="wiz_act")
                w_disc = cx2.number_input("Discrétion", 1, 3, st.session_state.tmp_disc, key="wiz_disc")
                w_intel = cx3.number_input("Intellect", 1, 3, st.session_state.tmp_intel, key="wiz_intel")
                w_soc = cx4.number_input("Social", 1, 3, st.session_state.tmp_soc, key="wiz_soc")
                st.session_state.tmp_act, st.session_state.tmp_disc, st.session_state.tmp_intel, st.session_state.tmp_soc = w_act, w_disc, w_intel, w_soc
                
                st.write("**🎒 Equipement**")
                w_emb1 = st.text_input("Objet Emblématique 1 ✦ *", value=st.session_state.get("w_emb1", ""), key="wiz_emb1")
                w_emb2 = st.text_input("Objet Emblématique 2 ✦ *", value=st.session_state.get("w_emb2", ""), key="wiz_emb2")
                w_ord1 = st.text_input("Matériel standard 1", value=st.session_state.get("w_ord1", ""), key="wiz_ord1")
                w_ord2 = st.text_input("Matériel standard 2", value=st.session_state.get("w_ord2", ""), key="wiz_ord2")
                w_ord3 = st.text_input("Matériel standard 3", value=st.session_state.get("w_ord3", ""), key="wiz_ord3")
                w_ord4 = st.text_input("Matériel standard 4", value=st.session_state.get("w_ord4", ""), key="wiz_ord4")

                st.write("")
                c_nav1, c_nav2 = st.columns(2)
                if c_nav1.button("⬅️ Retour", key="back_to_1", use_container_width=True):
                    st.session_state.wizard_step = 1
                    st.rerun()
                if c_nav2.button("➡️ Continuer vers la Synchro", type="primary", key="next_to_3", use_container_width=True):
                    if w_emb1.strip() and w_emb2.strip():
                        scores_attendus = sorted([int(x) for x in repart_cible.split(", ")])
                        scores_saisis = sorted([w_act, w_disc, w_intel, w_soc])
                        
                        # MODIFICATION : Si c'est un nouveau perso, on valide la grille. 
                        # Si c'est une édition, on laisse passer peu importe l'évolution des scores !
                        if is_new:
                            if scores_saisis == scores_attendus:
                                st.session_state.w_emb1 = w_emb1.strip()
                                st.session_state.w_emb2 = w_emb2.strip()
                                st.session_state.wizard_step = 3
                                st.rerun()
                            else:
                                st.error(f"❌ Déséquilibre d'effort initial : {scores_saisis}. Requis : {scores_attendus} pour un nouveau sujet.")
                        else:
                            # Mode édition : On valide directement sans bloquer sur la grille de départ
                            st.session_state.w_emb1 = w_emb1.strip()
                            st.session_state.w_emb2 = w_emb2.strip()
                            st.session_state.wizard_step = 3
                            st.rerun()
                    else:
                        st.error("❌ Les deux objets emblématiques (✦) sont requis.")

            # --- ÉTAPE 3 : TRAITS, SYNCHRONISATION & ATOUTS ---
            elif step == 3:
                st.markdown("#### 🃏 Étape 3 : Traits, Synchronisation & Atouts")
                w_trait1 = st.text_input("Trait 1 *", value=st.session_state.get("w_trait1", ""), key="wiz_t1")
                w_trait2 = st.text_input("Trait 2 *", value=st.session_state.get("w_trait2", ""), key="wiz_t2")
                w_entrave = st.text_input("Entrave *", value=st.session_state.get("w_entrave", ""), key="wiz_ent")
                w_langues = st.text_input("Langues ", value=st.session_state.get("w_langues", "Français"), key="wiz_lan")
                
                st.write("---")
                st.markdown("##### 📊 Jauge de Synchronisation (XP)")
                current_xp = st.slider("Ajuster le niveau de Synchro Campagne (XP) :", 1, 6, int(st.session_state.get("w_xp_level", 1)), key="wiz_xp_slider")
                st.session_state.w_xp_level = current_xp

                st.write("")
                c_nav3, c_nav4 = st.columns(2)
                if c_nav3.button("⬅️ Retour aux Approches", key="back_to_2", use_container_width=True):
                    st.session_state.wizard_step = 2
                    st.rerun()
                    
                if c_nav4.button("🧬 COMPILER ET ENREGISTRER LE PROFIL", type="primary", use_container_width=True):
                    # Récupération sécurisée depuis le Session State (Étapes 1 & 2)
                    f_nom = st.session_state.get("w_nom", "").strip()
                    f_cit = st.session_state.get("w_cit", "").strip()
                    f_emb1 = st.session_state.get("w_emb1", "").strip()
                    f_emb2 = st.session_state.get("w_emb2", "").strip()
                    
                    # Récupération locale (Étape 3 - Gauche)
                    f_t1 = w_trait1.strip()
                    f_t2 = w_trait2.strip()
                    f_ent = w_entrave.strip()
                    f_lan = w_langues.strip()
                    
                    # Récupération des compétences (Étape 3 - Droite via Session State)
                    c1_saved = st.session_state.get("wiz_slot_comp1", "-- Emplacement Vide --")
                    c2_saved = st.session_state.get("wiz_slot_comp2", "-- Emplacement Vide --")
                    c3_saved = st.session_state.get("wiz_slot_comp3", "-- Emplacement Vide --")
                    f_anc = st.session_state.get("wiz_anc_select", "")

                    if f_nom and f_emb1 and f_emb2 and f_t1 and f_t2 and f_ent:
                        import time
                        fid = target if not is_new else f"subject_{int(time.time())}"
                        
                        # Reconstruction de l'inventaire standard
                        o_list = [st.session_state.get("w_ord1", ""), st.session_state.get("w_ord2", ""), st.session_state.get("w_ord3", ""), st.session_state.get("w_ord4", "")]
                        string_stds = ", ".join([obj.strip() for obj in o_list if obj.strip()])
                        
                        data["descendants"][fid] = {
                            "nom": f_nom, 
                            "citation": f_cit, 
                            "entrave": f_ent, 
                            "traits": f"{f_t1}, {f_t2}",
                            "equipement_emblematique": [f_emb1, f_emb2], 
                            "equipement_standard": string_stds,
                            "approches": {
                                "action": st.session_state.tmp_act, 
                                "discretion": st.session_state.tmp_disc, 
                                "intellect": st.session_state.tmp_intel, 
                                "social": st.session_state.tmp_soc
                            },
                            "langues": f_lan, 
                            "ancetre_prioritaire": f_anc,
                            "niveau_xp": st.session_state.w_xp_level, 
                            "competences_actives": [c1_saved, c2_saved, c3_saved]
                        }
                        sauvegarder_donnees(data)
                        
                        # Nettoyage complet pour le prochain personnage
                        for k in ["w_id", "w_nom", "w_cit", "w_emb1", "w_emb2", "w_ord1", "w_ord2", "w_ord3", "w_ord4", "w_trait1", "w_trait2", "w_traits", "w_entrave", "w_langues", "w_xp_level", "wiz_slot_comp1", "wiz_slot_comp2", "wiz_slot_comp3", "wiz_anc_select", f"init_done_{target}"]:
                            if k in st.session_state: del st.session_state[k]
                        st.session_state.edit_target_id = None
                        st.session_state.wizard_step = 1
                        st.rerun()
                    else:
                        st.error("❌ Erreur : Veuillez remplir toutes les particularités requises (*) à l'étape 3.")

        with col_preview_panel:
            # --- ÉTAPES 1 & 2 : APERÇU FIXE SELON LA SÉLECTION INITIALE ---
            if step in [1, 2]:
                st.markdown("<b style='color:#385d6e;'>📜 LIAISON GÉNÉTIQUE : APERÇU DE L'ANCESTRE</b>", unsafe_allow_html=True)
                ancetres_par_nom = {v["nom"]: v for v in data["ancetres_officiels"].values()}
                
                # Récupération sécurisée du nom de l'ancêtre en cours
                default_anc = st.session_state.get("wiz_anc_select", list(ancetres_par_nom.keys())[0])
                if default_anc not in ancetres_par_nom:
                    default_anc = list(ancetres_par_nom.keys())[0]
                    
                p_a = ancetres_par_nom[default_anc]
                
                # CORRECTION : Utilisation de HTML_ANCESTRE_TEMPLATE à la place de HTML_CARD_TEMPLATE
                st.markdown(HTML_ANCESTRE_TEMPLATE.format(
                    nom=p_a["nom"], 
                    periode=p_a.get("periode", "Inconnue"), 
                    citation=p_a["citation"], 
                    action=p_a["action"], 
                    discretion=p_a["discretion"], 
                    intellect=p_a["intellect"], 
                    social=p_a["social"], 
                    equipement_html=formater_equipement_html(p_a["equipement"]), 
                    traits=p_a["traits"], 
                    entrave=p_a["entrave"], 
                    langues=p_a.get("langues", "Inconnu")
                ), unsafe_allow_html=True)
            
            # --- ÉTAPE 3 : CHOIX COMPLÈT DU COMPAGNON ET DES ATOUTS ---
            # --- ÉTAPE 3 : CHOIX COMPLET DU COMPAGNON ET DES ATOUTS ---
            elif step == 3:
                st.markdown("<b style='color:#385d6e;'>📜 CONFIGURATION DE LA MÉMOIRE GÉNÉTIQUE</b>", unsafe_allow_html=True)
                ancetres_par_nom = {v["nom"]: v for v in data["ancetres_officiels"].values()}
                
                curr_anc_saved = st.session_state.get("wiz_anc_select", list(ancetres_par_nom.keys())[0])
                if curr_anc_saved not in ancetres_par_nom:
                    curr_anc_saved = list(ancetres_par_nom.keys())[0]
                    
                idx_anc_wiz = list(ancetres_par_nom.keys()).index(curr_anc_saved)
                w_anc_lies = st.selectbox("Lier à l'ancêtre témoin :", list(ancetres_par_nom.keys()), index=idx_anc_wiz, key="wiz_anc_select")

                # Affichage dynamique de l'ancêtre sélectionné à l'étape 3
                p_a = ancetres_par_nom[w_anc_lies]
                with st.expander("🔍 Visualiser la fiche de l'Ancêtre témoin sélectionné", expanded=True):
                    # CORRECTION PROTOCOLE : Remplacement par HTML_ANCESTRE_TEMPLATE
                    st.markdown(HTML_ANCESTRE_TEMPLATE.format(
                        nom=p_a["nom"], 
                        periode=p_a.get("periode", "Inconnue"), 
                        citation=p_a["citation"], 
                        action=p_a["action"], 
                        discretion=p_a["discretion"], 
                        intellect=p_a["intellect"], 
                        social=p_a["social"], 
                        equipement_html=formater_equipement_html(p_a["equipement"]), 
                        traits=p_a["traits"], 
                        entrave=p_a["entrave"], 
                        langues=p_a.get("langues", "Inconnu")
                    ), unsafe_allow_html=True)

                st.write("---")
                st.markdown("<b style='color:#385d6e;'>🎴 SÉLECTION ET SYNC DES SKILLS DE L'ANIMUM</b>", unsafe_allow_html=True)
                base_comps_all = sorted(list(data["competences_globales"].keys()))
                v_c1 = st.session_state.get("wiz_slot_comp1", "-- Emplacement Vide --")
                v_c2 = st.session_state.get("wiz_slot_comp2", "-- Emplacement Vide --")
                v_c3 = st.session_state.get("wiz_slot_comp3", "-- Emplacement Vide --")

                # Slot 1
                f1 = ["-- Emplacement Vide --"] + [c for c in base_comps_all if c not in [v_c2, v_c3]]
                w_c1 = st.selectbox("Slot Atout 1 (Disponible immédiatement)", f1, index=f1.index(v_c1) if v_c1 in f1 else 0, key="wiz_slot_comp1")
                if w_c1 != "-- Emplacement Vide --":
                    st.markdown(HTML_SKILL_CARD_TEMPLATE.format(titre=w_c1, description=data['competences_globales'][w_c1]), unsafe_allow_html=True)
                
                # Slot 2
                if st.session_state.w_xp_level >= 3:
                    f2 = ["-- Emplacement Vide --"] + [c for c in base_comps_all if c not in [w_c1, v_c3]]
                    w_c2 = st.selectbox("Slot Atout 2 (Débloqué au Palier 55%+)", f2, index=f2.index(v_c2) if v_c2 in f2 else 0, key="wiz_slot_comp2")
                    if w_c2 != "-- Emplacement Vide --":
                        st.markdown(HTML_SKILL_CARD_TEMPLATE.format(titre=w_c2, description=data['competences_globales'][w_c2]), unsafe_allow_html=True)
                else:
                    st.error("🔒 Slot Atout 2 verrouillé (Requiert le palier de Synchro 55% ou 70%)")
                    st.session_state.wiz_slot_comp2 = "-- Emplacement Vide --"
                    
                # Slot 3
                if st.session_state.w_xp_level >= 5:
                    f3 = ["-- Emplacement Vide --"] + [c for c in base_comps_all if c not in [w_c1, st.session_state.get("wiz_slot_comp2", "-- Emplacement Vide --")]]
                    w_c3 = st.selectbox("Slot Atout 3 (Débloqué au Palier 85%+)", f3, index=f3.index(v_c3) if v_c3 in f3 else 0, key="wiz_slot_comp3")
                    if w_c3 != "-- Emplacement Vide --":
                        st.markdown(HTML_SKILL_CARD_TEMPLATE.format(titre=w_c3, description=data['competences_globales'][w_c3]), unsafe_allow_html=True)
                else:
                    st.error("🔒 Slot Atout 3 verrouillé (Requiert le palier de Synchro 85% ou 100%)")
                    st.session_state.wiz_slot_comp3 = "-- Emplacement Vide --"

    # =========================================================================
    # 🖥️ ÉCRAN DE SYNCHRONISATION DÉDIÉ (MODE VISION PROPRE)
    # =========================================================================
    if st.session_state.active_view_id and st.session_state.active_view_id in data["descendants"] and not st.session_state.edit_target_id:
        st.write("---")
        profil_v = data["descendants"][st.session_state.active_view_id]
        st.markdown(f"### 🖥️ Écran de Synchronisation : Matrix [{profil_v['nom']}]")
        
        if st.button("❌ Masquer l'écran de vision", type="secondary"):
            st.session_state.active_view_id = None
            st.rerun()
            
        v_col_gauche, v_col_milieu, v_col_droite = st.columns([5, 2, 4])
        
        with v_col_gauche:
            emb_v = profil_v.get("equipement_emblematique", ["", ""])
            std_v = profil_v.get("equipement_standard", "")
            inv_v = [x for x in emb_v if x]
            if std_v: inv_v.extend([x.strip() for x in std_v.split(",") if x.strip()])
            
            # Récupération et formatage pour l'affichage unifié dans la vision
            ancetre_nom_v = profil_v.get("ancetre_prioritaire", "Aucun")
            comps_actives_v = profil_v.get("competences_actives", ["-- Emplacement Vide --", "-- Emplacement Vide --", "-- Emplacement Vide --"])
            atouts_presents_v = [c for c in comps_actives_v if c != "-- Emplacement Vide --" and c in data["competences_globales"]]
            
            # Reconstruction des badges sans retour à la ligne
            html_badges_v = ""
            if atouts_presents_v:
                for atout in atouts_presents_v:
                    eff = data["competences_globales"].get(atout, "")
                    html_badges_v += f'<div style="background-color: #385d6e; color: white; border-radius: 4px; padding: 4px 8px; margin-top: 4px; font-size: 0.8rem; border-left: 3px solid #b13434;" title="{eff}">⚡ <b>{atout}</b></div>'
            else:
                html_badges_v = '<span style="font-weight: normal; color: #777; font-style: italic;">Aucun atout mémorisé</span>'

            # Utilisation du nouveau gabarit pour le descendant moderne
            st.markdown(HTML_DESCENDANT_TEMPLATE.format(
                nom=profil_v["nom"], 
                periode="Monde Moderne — Agent Cellule", 
                citation=profil_v.get("citation", "Aucune devise."),
                action=profil_v["approches"]["action"], 
                discretion=profil_v["approches"]["discretion"], 
                intellect=profil_v["approches"]["intellect"], 
                social=profil_v["approches"]["social"],
                equipement_html=formater_equipement_html(", ".join(inv_v)), 
                traits=profil_v["traits"], 
                entrave=profil_v["entrave"], 
                langues=profil_v.get("langues", "Français"),
                ancetre_nom=ancetre_nom_v,
                competences_badges_html=html_badges_v
            ), unsafe_allow_html=True)
            
            st.write("")
            # Au lieu de stocker la variable avant, on force l'exécution au chargement du bouton
            st.download_button(
                label="📥 EXPORTER LA FICHE OFFICIELLE (PNG)",
                data=generer_fiche_personnage_png(profil_v, data),
                file_name=f"Fiche_{profil_v['nom'].replace(' ', '_')}.png",
                mime="image/png",
                use_container_width=True,
                type="primary",
                key="btn_export_vision_unique"
            )
            
            if bytes_vision:
                st.download_button(
                    label="📥 EXPORTER LA FICHE OFFICIELLE (PNG)",
                    data=bytes_vision,
                    file_name=f"Fiche_{profil_v['nom'].replace(' ', '_')}.png",
                    mime="image/png",
                    use_container_width=True,
                    type="primary"
                )
            else:
                st.error("⚠️ Fichier 'AC_Fiche de perso.jpg' introuvable à la racine pour l'export.")
            
            
        with v_col_milieu:
            st.markdown("<div style='text-align:center; font-weight:bold;'>📊 PALIER</div>", unsafe_allow_html=True)
            xp_v = profil_v.get("niveau_xp", 1)
            paliers_v = [(6, "100 %"), (5, "85 %"), (4, "70 %"), (3, "55 %"), (2, "40 %"), (1, "25 %")]
            for p_id, label in paliers_v:
                st.button(f"🧬 {label}" if xp_v >= p_id else f"⬜ {label}", key=f"v_xp_act_{p_id}", type="primary" if xp_v >= p_id else "secondary", use_container_width=True)
                    
        with v_col_droite:
            # 1. Accordéon de la mémoire génétique de l'ancêtre
            anc_nom_lie = profil_v.get("ancetre_prioritaire", "")
            anc_dict = {v["nom"]: v for v in data["ancetres_officiels"].values()}
            if anc_nom_lie in anc_dict:
                p_a = anc_dict[anc_nom_lie]
                with st.expander(f"📜 Mémoire Génétique de {anc_nom_lie}", expanded=True):
                    st.markdown(HTML_ANCESTRE_TEMPLATE.format(
                        nom=p_a["nom"], 
                        periode=p_a.get("periode", "Inconnue"), 
                        citation=p_a["citation"], 
                        action=p_a["action"], 
                        discretion=p_a["discretion"], 
                        intellect=p_a["intellect"], 
                        social=p_a["social"], 
                        equipement_html=formater_equipement_html(p_a["equipement"]), 
                        traits=p_a["traits"], 
                        entrave=p_a["entrave"], 
                        langues=p_a.get("langues", "Inconnu")
                    ), unsafe_allow_html=True)
            
            # 2. Accordéon unique regroupant TOUTES les compétences sélectionnées
            comps_v = profil_v.get("competences_actives", ["-- Emplacement Vide --", "-- Emplacement Vide --", "-- Emplacement Vide --"])
            atouts_presents_vision = [c for c in comps_v if c != "-- Emplacement Vide --" and c in data["competences_globales"]]
            
            with st.expander("🃏 Compétences", expanded=True):
                if atouts_presents_vision:
                    for c_nom in atouts_presents_vision:
                        # Toutes les cartes se génèrent ici, l'une sous l'autre, dans le même accordéon
                        st.markdown(HTML_SKILL_CARD_TEMPLATE.format(
                            titre=f"Atout : {c_nom}", 
                            description=data["competences_globales"][c_nom]
                        ), unsafe_allow_html=True)
                else:
                    st.caption("⚡ *Aucune compétence active synchronisée sur cette jauge d'ADN.*")

    # =========================================================================
    # 📂 LE REGISTRE DES CARTES PRINCIPAL (GRILLE COMPLETE)
    # =========================================================================
    if not st.session_state.edit_target_id:
        st.write("---")
        st.subheader("🗃️ Archives Systèmes des Agents")
        
        desc_filtres = {k: v for k, v in data["descendants"].items() if recherche_desc in v["nom"].lower()}
        desc_tries = sorted(desc_filtres.items(), key=lambda x: x[1]["nom"].lower())

        if desc_tries:
            grid_cols = st.columns(3)
            for idx, (cle_desc, profil) in enumerate(desc_tries):
                with grid_cols[idx % 3]:
                    emb = profil.get("equipement_emblematique", ["", ""])
                    std_text = profil.get("equipement_standard", "")
                    inv_total = [x for x in emb if x]
                    if std_text: inv_total.extend([x.strip() for x in std_text.split(",") if x.strip()])
                    
                    # Récupération de l'ancêtre et des compétences
                    ancetre_nom = profil.get("ancetre_prioritaire", "Aucun")
                    comps_actives = profil.get("competences_actives", ["-- Emplacement Vide --", "-- Emplacement Vide --", "-- Emplacement Vide --"])
                    atouts_presents = [c for c in comps_actives if c != "-- Emplacement Vide --"]
                    
                    # Construction des badges de compétences sans aucun retour à la ligne pour éviter le bug Markdown
                    html_badges = ""
                    if atouts_presents:
                        for atout in atouts_presents:
                            eff = data["competences_globales"].get(atout, "")
                            # TOUT SUR UNE SEULE LIGNE :
                            html_badges += f'<div style="background-color: #385d6e; color: white; border-radius: 4px; padding: 4px 8px; margin-top: 4px; font-size: 0.8rem; border-left: 3px solid #b13434;" title="{eff}">⚡ <b>{atout}</b></div>'
                    else:
                        html_badges = '<span style="font-weight: normal; color: #777; font-style: italic;">Aucun atout mémorisé</span>'
                    
                    # Rendu final unifié sans coupure ni bloc de code noir
                    st.markdown(HTML_DESCENDANT_TEMPLATE.format(
                        nom=profil["nom"], 
                        periode=f"Monde Moderne — Niveau {profil.get('niveau_xp', 1)}/6", 
                        citation=profil.get("citation", "Aucune devise."), 
                        action=profil["approches"]["action"], 
                        discretion=profil["approches"]["discretion"], 
                        intellect=profil["approches"]["intellect"], 
                        social=profil["approches"]["social"], 
                        equipement_html=formater_equipement_html(", ".join(inv_total)), 
                        traits=profil["traits"], 
                        entrave=profil["entrave"], 
                        langues=profil.get("langues", "Français"),
                        ancetre_nom=ancetre_nom,
                        competences_badges_html=html_badges
                    ), unsafe_allow_html=True)
                    
                    # 4. Ligne de boutons d'action élargie pour accueillir l'export
                    c_b1, c_b2, c_b3, c_b4 = st.columns([4, 3, 3, 2])
                    
                    if c_b1.button("👁️ Ouvrir", key=f"v_b_{cle_desc}", use_container_width=True, type="secondary"):
                        st.session_state.active_view_id = cle_desc
                        st.rerun()
                        
                    if c_b2.button("📝 Éditer", key=f"e_b_{cle_desc}", use_container_width=True):
                        st.session_state.edit_target_id = cle_desc
                        st.rerun()

                    # Bouton d'export direct au format vignette
                    bytes_vignette = generer_fiche_personnage_png(profil, data)
                    if bytes_vignette:
                        c_b3.download_button(
                            label="💾",
                            data=bytes_vignette,
                            file_name=f"Fiche_{profil['nom'].replace(' ', '_')}.png",
                            mime="image/png",
                            key=f"exp_v_{cle_desc}",
                            use_container_width=True,
                            help="Exporter la fiche officielle en PNG"
                        )
                    else:
                        c_b3.button("❌", key=f"exp_err_{cle_desc}", disabled=True, use_container_width=True, help="Fiche de base manquante")
                        
                    if c_b4.button("🚨", key=f"d_b_{cle_desc}", use_container_width=True):
                        valider_suppression_donnees("descendant", cle_desc, profil["nom"])
        else:
            st.warning("⚠️ Aucun agent enregistré.")

# ==========================================
# 2. ONGLET : ARCHIVES DES ANCÊTRES (RECHERCHE + BOUTONS FILTRES)
# ==========================================
with tab_ancetres:
    st.header("Mémoire Génétique (Fichiers de Témoin)")
    toutes_periodes = sorted(list(set(v.get("periode", "Inconnue") for v in data["ancetres_officiels"].values())))
    
    if "filtre_periode" not in st.session_state:
        st.session_state.filtre_periode = None

    st.write("📌 **Trier par Position Temporelle :**")
    badge_cols = st.columns(len(toutes_periodes) + 1)
    
    if badge_cols[0].button("🌍 Tout afficher", type="primary" if st.session_state.filtre_periode is None else "secondary"):
        st.session_state.filtre_periode = None
        st.rerun()
        
    for idx, per in enumerate(toutes_periodes):
        col_bouton = badge_cols[idx + 1]
        style_type = "primary" if st.session_state.filtre_periode == per else "secondary"
        if col_bouton.button(per, key=f"btn_{idx}", type=style_type):
            st.session_state.filtre_periode = per
            st.rerun()

    recherche = st.text_input("🔍 Recherche textuelle ciblée (par nom)...", "").strip().lower()
    
    ancetres_filtres = {k: v for k, v in data["ancetres_officiels"].items() if recherche in v["nom"].lower()}
    if st.session_state.filtre_periode:
        st.info(f"Filtre temporel actif : **{st.session_state.filtre_periode}**")
        ancetres_filtres = {k: v for k, v in data["ancetres_officiels"].items() if v.get("periode") == st.session_state.filtre_periode}
        
    ancetres_tries = sorted(ancetres_filtres.items(), key=lambda x: x[1]["nom"].lower())
    
    if ancetres_tries:
        cols = st.columns(3)
        for idx, (cle_anc, profil) in enumerate(ancetres_tries):
            col_actuelle = cols[idx % 3]
            with col_actuelle:
                st.markdown(HTML_ANCESTRE_TEMPLATE.format(
                    nom=profil["nom"], periode=profil.get("periode", "Période inconnue"),
                    citation=profil["citation"], action=profil["action"], discretion=profil["discretion"],
                    intellect=profil["intellect"], social=profil["social"],
                    equipement_html=formater_equipement_html(profil["equipement"]),
                    traits=profil["traits"], entrave=profil["entrave"], langues=profil.get("langues", "Inconnu"),
                    bloc_moderne_html=""
                ), unsafe_allow_html=True)
    else:
        st.warning("⚠️ Aucun ancêtre ne correspond aux filtres génétiques sélectionnés.")

    st.write("---")
    st.subheader("🛠️ Outils d'administration ADN (Ajouter / Modifier / Supprimer)")
    col_admin1, col_admin2 = st.columns(2)
    
    with col_admin1:
        with st.expander("➕ Couronner un nouvel Ancêtre sur-mesure"):
            with st.form("form_creer_ancetre"):
                id_anc = st.text_input("Clé ADN unique (ex: ezio_02)").strip()
                nom_anc = st.text_input("Nom de l'Assassin")
                per_anc = st.text_input("Période temporelle")
                cit_anc = st.text_input("Philosophie / Citation")
                ent_anc = st.text_input("Entrave")
                traits_anc = st.text_input("Traits (séparés par des virgules)")
                lang_anc = st.text_input("Langues parlées")
                eq_anc = st.text_area("Équipements")
                
                st.write("Attributs (3,3,1,1 ou 3,2,2,1 ou 2,2,2,2) :")
                v1, v2, v3, v4 = st.columns(4)
                a_act = v1.number_input("Action ", 1, 3, 3)
                a_disc = v2.number_input("Discrétion ", 1, 3, 2)
                a_intel = v3.number_input("Intellect ", 1, 3, 2)
                a_soc = v4.number_input("Social ", 1, 3, 1)
                
                if st.form_submit_button("Matérialiser l'Ancêtre"):
                    if id_anc and nom_anc:
                        rep_anc = [a_act, a_disc, a_intel, a_soc]
                        if sorted(rep_anc) in [sorted([3, 3, 1, 1]), sorted([3, 2, 2, 1]), sorted([2, 2, 2, 2])]:
                            data["ancetres_officiels"][id_anc] = {
                                "nom": nom_anc, "periode": per_anc, "citation": cit_anc, "entrave": ent_anc,
                                "action": a_act, "discretion": a_disc, "intellect": a_intel, "social": a_soc,
                                "traits": traits_anc, "langues": lang_anc, "equipement": eq_anc
                            }
                            sauvegarder_donnees(data)
                            st.success(f"Fichier initialisé.")
                            st.rerun()

    with col_admin2:
        if data["ancetres_officiels"]:
            with st.expander("📝 Éditer ou Supprimer une séquence existante"):
                ancetres_selection_tries = sorted(data["ancetres_officiels"].items(), key=lambda x: x[1]["nom"].lower())
                options_selection = {v["nom"]: k for k, v in ancetres_selection_tries}
                choix_nom_label = st.selectbox("Sélectionner l'Ancêtre", list(options_selection.keys()))
                choix_anc = options_selection[choix_nom_label]
                curr_anc = data["ancetres_officiels"][choix_anc]
                
                with st.form(f"form_mod_anc_{choix_anc}"):
                    m_anom = st.text_input("Nom de l'Assassin", value=curr_anc["nom"])
                    m_aper = st.text_input("Période temporelle", value=curr_anc.get("periode", ""))
                    m_cit = st.text_input("Citation de combat", value=curr_anc["citation"])
                    m_ent = st.text_input("Entrave", value=curr_anc["entrave"])
                    m_traits = st.text_input("Traits", value=curr_anc["traits"])
                    m_lang = st.text_input("Langues", value=curr_anc.get("langues", ""))
                    m_eq = st.text_area("Équipement", value=curr_anc["equipement"])
                    
                    if st.form_submit_button("Confirmer les modifications"):
                        data["ancetres_officiels"][choix_anc] = {
                            "nom": m_anom, "periode": m_aper, "citation": m_cit, "entrave": m_ent, "traits": m_traits,
                            "action": curr_anc["action"], "discretion": curr_anc["discretion"],
                            "intellect": curr_anc["intellect"], "social": curr_anc["social"],
                            "langues": m_lang, "equipement": m_eq
                        }
                        sauvegarder_donnees(data)
                        st.success("Données mises à jour.")
                        st.rerun()
                        
                # Sécurisation pop-up dialog
                if st.button("❌ REJETER L'ANCÊTRE", key=f"del_anc_{choix_anc}", type="primary", use_container_width=True):
                    valider_suppression_donnees("ancetre", choix_anc, curr_anc["nom"])

# ==========================================
# 3. ONGLET : PAQUET DE COMPÉTENCES
# ==========================================
with tab_competences:
    st.header("Annexe A : Paquet des Compétences de l'Animum")
    
    with st.expander("➕ Forger une carte compétence sur-mesure"):
        with st.form("form_creer_comp"):
            nom_comp = st.text_input("Titre de la carte").strip()
            desc_comp = st.text_area("Effets en jeu")
            if st.form_submit_button("Ajouter au paquet"):
                if nom_comp and desc_comp:
                    data["competences_globales"][nom_comp] = desc_comp
                    sauvegarder_donnees(data)
                    st.rerun()

    if data["competences_globales"]:
        choix_comp = st.selectbox("Sélectionner une carte", sorted(list(data["competences_globales"].keys())))
        
        with st.form(f"form_mod_comp_{choix_comp}"):
            st.subheader(f"Carte : {choix_comp}")
            m_desc_comp = st.text_area("Règles et Effets", value=data["competences_globales"][choix_comp])
            
            if st.form_submit_button("Éditer la carte"):
                data["competences_globales"][choix_comp] = m_desc_comp
                sauvegarder_donnees(data)
                st.success("Effets mis à jour.")
                st.rerun()
                
        # Sécurisation pop-up dialog
        if st.button("❌ RETIRER LA CARTE", key=f"del_comp_{choix_comp}", type="primary", use_container_width=True):
            valider_suppression_donnees("competence", choix_comp, choix_comp)