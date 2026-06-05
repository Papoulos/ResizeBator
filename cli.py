import argparse
import sys
from logic import PosterGenerator

def main():
    parser = argparse.ArgumentParser(description="Resize Bator - Transformez un PDF en poster multi-pages")
    parser.add_argument("input", help="Fichier PDF d'entrée")
    parser.add_argument("output", help="Fichier PDF de sortie")
    parser.add_argument("--size", choices=["A3", "A4", "A5"], default="A4", help="Taille de la feuille (default: A4)")
    parser.add_argument("--orientation", choices=["Portrait", "Landscape"], default="Portrait", help="Orientation (default: Portrait)")
    parser.add_argument("--width-pages", type=int, help="Nombre de pages en largeur")
    parser.add_argument("--height-pages", type=int, help="Nombre de pages en hauteur")
    parser.add_argument("--overlap", type=int, default=10, help="Recouvrement en mm (default: 10)")
    parser.add_argument("--mode", choices=["Fit", "Fill", "Stretch"], default="Fit", help="Mode d'ajustement si le ratio diffère (default: Fit)")
    parser.add_argument("--no-marks", action="store_true", help="Désactiver les traits de coupe")

    args = parser.parse_args()

    if not args.width_pages and not args.height_pages:
        print("Erreur: Vous devez spécifier soit --width-pages soit --height-pages")
        sys.exit(1)

    target_dim = "Width" if args.width_pages else "Height"
    num_pages = args.width_pages if args.width_pages else args.height_pages

    try:
        with open(args.input, "rb") as f:
            generator = PosterGenerator(f)

            cols, rows, total_w, total_h = generator.calculate_grid(
                args.size, args.orientation, num_pages, target_dim, args.overlap
            )

            print(f"Génération d'un poster de {total_w/10:.1f}x{total_h/10:.1f} cm")
            print(f"Disposition: {cols} colonnes x {rows} lignes ({cols*rows} feuilles {args.size})")

            output_stream = generator.generate(
                args.size, args.orientation, cols, rows, args.overlap, args.mode, not args.no_marks
            )

            with open(args.output, "wb") as out_f:
                out_f.write(output_stream.getbuffer())

            print(f"Succès ! Fichier enregistré sous {args.output}")

    except Exception as e:
        print(f"Erreur lors de la génération: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
