# Resize Bator 🖼️

Une application en ligne de commande et une interface Web pour transformer vos fichiers PDF en posters géants multi-pages.

## Fonctionnalités

- **Agrandissement de PDF** : Transformez n'importe quel PDF en un poster composé de plusieurs feuilles A4, A3 ou A5.
- **Préservation de la qualité** : Utilise les vecteurs originaux du PDF pour garantir une netteté parfaite à n'importe quelle taille.
- **Zone de recouvrement** : Ajoutez une marge de recouvrement configurable pour faciliter le collage des feuilles.
- **Aide à la découpe** : Affiche des pointillés pour guider la découpe et l'assemblage.
- **Gestion du ratio** : Avertit si le ratio du PDF ne correspond pas au format de papier et propose plusieurs modes d'ajustement (Marges, Remplissage, Étirement).
- **Interface Web intuitive** : Basée sur Streamlit avec aperçu en temps réel du découpage.

## Installation

```bash
pip install streamlit pypdf reportlab pymupdf matplotlib pillow
```

## Utilisation

### Interface Web (Recommandé)

Lancez l'interface locale :
```bash
streamlit run app.py
```

### Ligne de commande (CLI)

```bash
python cli.py mon_fichier.pdf poster.pdf --width-pages 3 --size A4
```

**Options principales :**
- `--size` : A3, A4 ou A5.
- `--orientation` : Portrait ou Landscape.
- `--width-pages` ou `--height-pages` : Nombre de feuilles souhaitées en largeur ou hauteur.
- `--overlap` : Zone de recouvrement en mm (défaut: 10).
- `--mode` : Fit, Fill ou Stretch.
