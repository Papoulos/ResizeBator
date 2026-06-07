import streamlit as st
import fitz  # PyMuPDF
from logic import PosterGenerator, PAPER_SIZES, get_paper_size
import io
from PIL import Image

st.set_page_config(page_title="Resize Bator - PDF & Image Poster", layout="wide")

st.title("Resize Bator 🖼️")
st.subheader("Créez votre poster géant à partir d'un PDF ou d'une Image")

uploaded_file = st.sidebar.file_uploader("Choisissez un fichier", type=["pdf", "jpg", "jpeg", "png"])

if uploaded_file:
    # Use a BytesIO to avoid closing the original uploaded_file stream
    file_bytes = uploaded_file.read()
    uploaded_file.seek(0)

    generator = PosterGenerator(io.BytesIO(file_bytes))

    st.sidebar.header("Configuration")

    paper_size = st.sidebar.selectbox("Taille de la feuille", list(PAPER_SIZES.keys()), index=1) # Default A4
    orientation = st.sidebar.radio("Orientation", ["Portrait", "Landscape"])

    col1, col2 = st.sidebar.columns(2)
    with col1:
        target_dim_label = st.selectbox("Fixer la taille par", ["Largeur", "Hauteur"])
        target_dim = "Width" if target_dim_label == "Largeur" else "Height"
    with col2:
        num_pages = st.number_input("Nombre de feuilles", min_value=1, value=2)

    overlap_mm = st.sidebar.slider("Zone de recouvrement (mm)", 0, 50, 10)
    show_cut_marks = st.sidebar.checkbox("Afficher les aides à la découpe", value=True)

    # Calculation
    cols, rows, total_w_mm, total_h_mm = generator.calculate_grid(
        paper_size, orientation, num_pages, target_dim, overlap_mm
    )

    # Check Ratio: Source vs Single Sheet
    src_ratio = generator.src_width_pt / generator.src_height_pt
    paper_w_mm, paper_h_mm = get_paper_size(paper_size, orientation)
    sheet_ratio = paper_w_mm / paper_h_mm

    ratio_diff = abs(src_ratio - sheet_ratio) / sheet_ratio

    mode = "Fit"
    if ratio_diff > 0.05: # 5% tolerance
        st.warning(f"⚠️ Le ratio du fichier ({src_ratio:.2f}) ne correspond pas au ratio d'une feuille {paper_size} {orientation} ({sheet_ratio:.2f}).")
        mode_label = st.radio("Comment ajuster le contenu sur les feuilles ?",
                        ["Marges (Fit)", "Remplissage (Fill)", "Étirer (Stretch)"],
                        help="Fit: Garde tout le contenu avec des marges. Fill: Remplit tout l'espace (coupe les bords). Stretch: Déforme le contenu.")
        mode = mode_label.split(" ")[0] # Get "Fit", "Fill" or "Stretch"

    st.info(f"📏 **Taille finale du poster :** {total_w_mm/10:.1f} cm x {total_h_mm/10:.1f} cm  \n"
            f"📄 **Disposition :** {cols} colonnes x {rows} lignes = **{cols*rows} feuilles** {paper_size}")

    if st.button("Générer le Poster PDF"):
        with st.spinner("Génération en cours..."):
            output_pdf = generator.generate(paper_size, orientation, cols, rows, overlap_mm, mode, show_cut_marks)
            st.success("Poster généré avec succès !")
            st.download_button(
                label="Télécharger le Poster PDF",
                data=output_pdf,
                file_name="poster_resize_bator.pdf",
                mime="application/pdf"
            )

    # Preview
    st.divider()
    st.subheader("Aperçu du découpage")

    # Generate a low-res image for preview
    if uploaded_file.name.lower().endswith(".pdf"):
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        page = doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5)) # low res
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    else:
        img = Image.open(io.BytesIO(file_bytes))
        # Resize for preview if it's too large
        max_preview_size = 1000
        if max(img.size) > max_preview_size:
            ratio = max_preview_size / max(img.size)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.LANCZOS)
        if img.mode != "RGB":
            img = img.convert("RGB")

    preview_w, preview_h = img.size

    # Overlay the grid on the preview image
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.imshow(img)

    # Calculate grid lines
    paper_w_pt, paper_h_pt = [x * (72/25.4) for x in get_paper_size(paper_size, orientation)]
    overlap_pt = overlap_mm * (72/25.4)
    eff_w_pt = paper_w_pt - overlap_pt
    eff_h_pt = paper_h_pt - overlap_pt

    total_w_pt = (cols * eff_w_pt) + overlap_pt
    total_h_pt = (rows * eff_h_pt) + overlap_pt

    src_w = generator.src_width_pt
    src_h = generator.src_height_pt

    scale_x = total_w_pt / src_w
    scale_y = total_h_pt / src_h

    if mode == "Fit":
        s = min(scale_x, scale_y)
        scale_x = scale_y = s
    elif mode == "Fill":
        s = max(scale_x, scale_y)
        scale_x = scale_y = s

    scaled_w = src_w * scale_x
    scaled_h = src_h * scale_y
    offset_x = (total_w_pt - scaled_w) / 2
    offset_y = (total_h_pt - scaled_h) / 2

    for r in range(rows):
        for c in range(cols):
            x_min = (c * eff_w_pt - offset_x) / scale_x
            y_min = ((rows - 1 - r) * eff_h_pt - offset_y) / scale_y

            w_tile = paper_w_pt / scale_x
            h_tile = paper_h_pt / scale_y

            # Map to image coordinates
            img_x = x_min * (preview_w / src_w)
            img_y = (src_h - (y_min + h_tile)) * (preview_h / src_h)
            img_w = w_tile * (preview_w / src_w)
            img_h = h_tile * (preview_h / src_h)

            rect = patches.Rectangle((img_x, img_y), img_w, img_h, linewidth=1, edgecolor='r', facecolor='none', linestyle='--')
            ax.add_patch(rect)

    ax.axis('off')
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight')
    st.image(buf, use_container_width=True)
    plt.close(fig)

else:
    st.info("Veuillez charger un fichier PDF ou Image pour commencer.")
