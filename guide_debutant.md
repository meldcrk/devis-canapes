# 🎓 Guide Ultra-Simplifié pour Débutants

**Pour utiliser cette application, AUCUNE connaissance en programmation n'est nécessaire !**  
Suivez simplement ces étapes comme une recette de cuisine. 👨‍🍳

---

## 🔧 PREMIÈRE FOIS : Installation (15 minutes)

### Étape 1 : Installer Python

#### Sur Windows :
1. Allez sur **https://www.python.org/downloads/**
2. Cliquez sur le gros bouton jaune "Download Python"
3. **IMPORTANT** : Lors de l'installation, **cochez la case "Add Python to PATH"** ✅
4. Cliquez sur "Install Now"
5. Attendez que l'installation se termine

#### Sur Mac :
1. Allez sur **https://www.python.org/downloads/**
2. Téléchargez la version pour Mac
3. Ouvrez le fichier téléchargé
4. Suivez l'assistant d'installation

### Étape 2 : Préparer vos Fichiers

1. **Créez un nouveau dossier** sur votre bureau nommé `Devis-Canapes`
2. **Téléchargez tous ces fichiers** et mettez-les dans ce dossier :
   - `app.py`
   - `pricing.py`
   - `pdf_generator.py`
   - `canapefullv14.py` (votre fichier existant)
   - `requirements.txt`
   - `lancer_app.bat` (si vous êtes sur Windows)

Votre dossier doit ressembler à ça :
```
📁 Devis-Canapes/
   📄 app.py
   📄 pricing.py
   📄 pdf_generator.py
   📄 canapefullv14.py
   📄 requirements.txt
   📄 lancer_app.bat
```

### Étape 3 : Installer les Outils Nécessaires

#### Sur Windows :
1. Ouvrez le dossier `Devis-Canapes`
2. Dans la barre d'adresse en haut, tapez `cmd` et appuyez sur Entrée
3. Une fenêtre noire s'ouvre (c'est normal !)
4. Tapez exactement : `pip install -r requirements.txt`
5. Appuyez sur Entrée
6. Attendez 2-3 minutes (ça installe des outils automatiquement)
7. Quand c'est fini, vous voyez un message de succès ✅

#### Sur Mac :
1. Ouvrez "Terminal" (cherchez dans Spotlight)
2. Tapez : `cd Desktop/Devis-Canapes`
3. Appuyez sur Entrée
4. Tapez : `pip3 install -r requirements.txt`
5. Appuyez sur Entrée
6. Attendez 2-3 minutes

---

## ▶️ LANCER L'APPLICATION (Chaque Fois)

### Méthode Super Simple (Windows) :
1. **Double-cliquez sur `lancer_app.bat`** dans votre dossier
2. Une fenêtre noire s'ouvre
3. Votre navigateur s'ouvre automatiquement avec l'application ! 🎉
4. **NE FERMEZ PAS la fenêtre noire** (c'est elle qui fait tourner l'app)

### Méthode Alternative (Tous systèmes) :
1. Ouvrez le dossier `Devis-Canapes`
2. Tapez `cmd` dans la barre d'adresse (Windows) ou ouvrez Terminal (Mac)
3. Tapez : `streamlit run app.py`
4. Appuyez sur Entrée
5. Allez sur : **http://localhost:8501** dans votre navigateur

---

## 📝 CRÉER UN DEVIS (L'Utilisation Quotidienne)

### Vue d'Ensemble
L'écran est divisé en 2 parties :
```
┌─────────────────┬──────────────────────┐
│                 │                      │
│   FORMULAIRE    │    APERÇU + PDF      │
│   (À gauche)    │    (À droite)        │
│                 │                      │
│   Vous remplissez│   Vous voyez le     │
│   ici            │   résultat ici       │
│                 │                      │
└─────────────────┴──────────────────────┘
```

### Étape par Étape

#### 1️⃣ TYPE DE CANAPÉ
Cliquez sur la liste déroulante et choisissez :
- **Simple** : canapé droit basique
- **L sans angle** : forme en L normale
- **L avec angle** : forme en L avec angle arrondi
- **U sans angle** : forme en U
- **U avec 1 angle** : forme en U avec 1 angle arrondi
- **U avec 2 angles** : forme en U avec 2 angles arrondis

#### 2️⃣ DIMENSIONS
Entrez les mesures en centimètres :
- Utilisez les flèches ⬆️⬇️ ou tapez directement
- Les champs changent selon le type de canapé choisi

#### 3️⃣ ACCOUDOIRS
Cochez les cases pour ajouter des accoudoirs :
- ✅ = avec accoudoir
- ☐ = sans accoudoir

#### 4️⃣ DOSSIERS
Même principe que les accoudoirs

#### 5️⃣ MÉRIDIENNE (OPTIONNEL)
Si le client veut une méridienne :
1. Cochez "Ajouter une méridienne"
2. Choisissez le côté
3. Entrez la longueur

#### 6️⃣ COUSSINS
Choisissez dans la liste :
- **auto** : le système calcule automatiquement (recommandé !)
- **65/80/90** : taille fixe en cm
- **valise** : tailles variables optimisées

#### 7️⃣ TRAVERSINS (OPTIONNEL)
Si vous voulez des traversins décoratifs :
1. Cochez "Ajouter des traversins"
2. Choisissez les positions

#### 8️⃣ MOUSSE & TISSU
- **Type de mousse** : D25 (confort standard) recommandé
- **Épaisseur** : 25cm par défaut

#### 9️⃣ COULEURS
Tapez le nom de la couleur en français :
- Exemples : `gris`, `beige`, `taupe`, `gris clair`, `gris foncé`
- Vous pouvez aussi utiliser des codes comme `#cccccc`

#### 🔟 OPTIONS
- **Coussins déco** : nombre de coussins décoratifs supplémentaires
- **Traversins supp.** : traversins en plus
- **Surmatelas** : cochez si le client veut un surmatelas

#### 1️⃣1️⃣ INFORMATIONS CLIENT
- **Nom** : OBLIGATOIRE
- **Email** : optionnel

### Générer le Devis

1. Cliquez sur **"🎨 Générer l'Aperçu"** (bouton bleu)
   - Attendez quelques secondes
   - Le prix s'affiche à droite

2. Vérifiez que tout est correct

3. Cliquez sur **"📄 Générer le Devis PDF"**
   - Un bouton de téléchargement apparaît
   - Cliquez dessus pour télécharger le PDF

4. Le PDF est prêt ! 🎉
   - Ouvrez-le pour vérifier
   - Envoyez-le au client

---

## ❓ Questions Fréquentes

### "La fenêtre noire se ferme toute seule"
➜ C'est normal si vous avez fermé le navigateur. Relancez l'application.

### "Erreur : Streamlit n'est pas reconnu"
➜ Réinstallez avec : `pip install streamlit`

### "Le PDF ne se télécharge pas"
➜ Vérifiez que vous avez rempli le nom du client (obligatoire)

### "Je veux changer les prix"
➜ Ouvrez le fichier `pricing.py` avec Notepad (clic droit > Ouvrir avec > Bloc-notes)
➜ Modifiez les nombres à côté des articles
➜ Sauvegardez (Ctrl+S)
➜ Relancez l'application

### "Comment arrêter l'application ?"
➜ Fermez la fenêtre noire (cmd/terminal)
➜ Ou appuyez sur Ctrl+C dans la fenêtre noire

---

## 🎯 Conseils Pro

### Pour Aller Plus Vite
1. Créez un raccourci de `lancer_app.bat` sur votre bureau
2. Changez l'icône pour une icône de canapé
3. Un double-clic et c'est parti !

### Pour les Devis Rapides
1. Gardez l'application ouverte toute la journée
2. Créez plusieurs devis d'affilée
3. Téléchargez-les tous à la fin

### Pour Personnaliser
- Les couleurs du PDF sont dans `pdf_generator.py`
- Les prix sont dans `pricing.py`
- Ouvrez ces fichiers avec Notepad pour les modifier

---

## 🆘 Problème ? Pas de Panique !

### Ça ne marche pas du tout ?
1. Vérifiez que Python est installé : tapez `python --version` dans cmd
2. Réinstallez tout : `pip install -r requirements.txt --force-reinstall`
3. Redémarrez votre ordinateur

### Ça marchait et maintenant ça ne marche plus ?
1. Vérifiez que vous n'avez pas modifié les fichiers par accident
2. Re-téléchargez les fichiers originaux
3. Réinstallez

---

## 📞 Support

Si vraiment vous êtes bloqué :
1. Faites une capture d'écran du message d'erreur
2. Notez ce que vous faisiez juste avant
3. Contactez votre support technique avec ces infos

---

**🎉 Félicitations ! Vous êtes prêt à créer des devis professionnels !**

*Rappel : Aucune connaissance en programmation n'est nécessaire.  
Suivez simplement les étapes, c'est aussi simple qu'utiliser Word ou Excel !*