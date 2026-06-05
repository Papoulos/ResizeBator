import math
from pypdf import PdfReader, PdfWriter, PageObject, Transformation
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import io

# Standard paper sizes in mm
PAPER_SIZES = {
    "A3": (297, 420),
    "A4": (210, 297),
    "A5": (148, 210),
}

def get_paper_size(name, orientation):
    width, height = PAPER_SIZES[name]
    if orientation == "Landscape":
        return height, width
    return width, height

class PosterGenerator:
    def __init__(self, input_pdf_stream):
        self.reader = PdfReader(input_pdf_stream)
        self.source_page = self.reader.pages[0]
        # pypdf uses points (1/72 inch). 1mm = 72/25.4 points
        self.src_width_pt = float(self.source_page.mediabox.width)
        self.src_height_pt = float(self.source_page.mediabox.height)
        self.mm_to_pt = 72 / 25.4

    def calculate_grid(self, paper_size_name, orientation, target_pages, target_dimension="Width", overlap_mm=10):
        paper_w_mm, paper_h_mm = get_paper_size(paper_size_name, orientation)

        # Effective printable area per sheet
        effective_w_mm = paper_w_mm - overlap_mm
        effective_h_mm = paper_h_mm - overlap_mm

        src_ratio = self.src_width_pt / self.src_height_pt

        if target_dimension == "Width":
            cols = target_pages
            # Total width in mm (approximately, including overlaps)
            # Actually, the total width is: (cols * effective_w_mm) + overlap_mm
            total_w_mm = (cols * effective_w_mm) + overlap_mm
            total_h_mm = total_w_mm / src_ratio
            rows = math.ceil((total_h_mm - overlap_mm) / effective_h_mm)
        else:
            rows = target_pages
            total_h_mm = (rows * effective_h_mm) + overlap_mm
            total_w_mm = total_h_mm * src_ratio
            cols = math.ceil((total_w_mm - overlap_mm) / effective_w_mm)

        return cols, rows, total_w_mm, total_h_mm

    def generate(self, paper_size_name, orientation, cols, rows, overlap_mm=10, mode="Fit", show_cut_marks=True):
        paper_w_mm, paper_h_mm = get_paper_size(paper_size_name, orientation)
        paper_w_pt = paper_w_mm * self.mm_to_pt
        paper_h_pt = paper_h_mm * self.mm_to_pt
        overlap_pt = overlap_mm * self.mm_to_pt

        eff_w_pt = paper_w_pt - overlap_pt
        eff_h_pt = paper_h_pt - overlap_pt

        # Final poster total size in points
        total_w_pt = (cols * eff_w_pt) + overlap_pt
        total_h_pt = (rows * eff_h_pt) + overlap_pt

        # Scaling
        scale_x = total_w_pt / self.src_width_pt
        scale_y = total_h_pt / self.src_height_pt

        if mode == "Fit":
            scale = min(scale_x, scale_y)
            scale_x = scale_y = scale
        elif mode == "Fill":
            scale = max(scale_x, scale_y)
            scale_x = scale_y = scale
        # "Stretch" would keep scale_x and scale_y as they are

        scaled_w = self.src_width_pt * scale_x
        scaled_h = self.src_height_pt * scale_y

        # Offset to center if needed (for Fit or Fill)
        offset_x = (total_w_pt - scaled_w) / 2
        offset_y = (total_h_pt - scaled_h) / 2

        writer = PdfWriter()

        for r in range(rows):
            for c in range(cols):
                # New page for the tile
                page = writer.add_blank_page(width=paper_w_pt, height=paper_h_pt)

                # Translation: we want to show the part of the scaled PDF that corresponds to this tile
                # r=0 is top row. Bottom edge of row r is at total_h_pt - (r*eff_h_pt + paper_h_pt)
                # Wait:
                # Row 0: Top = total_h_pt, Bottom = total_h_pt - paper_h_pt
                # Row 1: Top = total_h_pt - eff_h_pt, Bottom = total_h_pt - eff_h_pt - paper_h_pt
                # Row r: Bottom = total_h_pt - (r * eff_h_pt) - paper_h_pt

                y_bottom = total_h_pt - (r * eff_h_pt) - paper_h_pt
                x_left = c * eff_w_pt

                tx = offset_x - x_left
                ty = offset_y - y_bottom

                # Apply transformation
                transformation = Transformation().scale(scale_x, scale_y).translate(tx, ty)

                # Apply transformation to the source page and merge
                page.merge_transformed_page(self.source_page, transformation)

                # Add cut marks if requested
                if show_cut_marks:
                    packet = io.BytesIO()
                    can = canvas.Canvas(packet, pagesize=(paper_w_pt, paper_h_pt))
                    can.setDash(1, 2)
                    can.setStrokeColorRGB(0.5, 0.5, 0.5)
                    can.setLineWidth(0.5)

                    # Draw dotted rectangle for the overlap area
                    # The printable/visible area is [0, eff_w_pt] x [0, eff_h_pt] ?
                    # No, the overlap is on the right and bottom (or left and top).
                    # Let's say we overlap on the right and top.
                    # Or even better, just show where the "next" page starts.

                    # Draw borders of the effective area
                    if c < cols - 1: # Vertical line on the right
                        can.line(eff_w_pt, 0, eff_w_pt, paper_h_pt)
                    if r > 0: # Horizontal line on the top (since r=0 is top)
                        can.line(0, paper_h_pt - eff_h_pt, paper_w_pt, paper_h_pt - eff_h_pt)
                    # Actually, let's just draw a border around the effective area
                    # can.rect(0, 0, eff_w_pt, eff_h_pt) # No, coordinates are tricky

                    can.save()
                    packet.seek(0)
                    mark_page = PdfReader(packet).pages[0]
                    page.merge_page(mark_page)

        output_stream = io.BytesIO()
        writer.write(output_stream)
        output_stream.seek(0)
        return output_stream
