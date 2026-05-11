from django.urls import path
from . import views

urlpatterns = [
     # ── Tes routes existantes ──────────────────
    path("merge",        views.merge_pdfs,   name="pdf-merge"),
    path("split",        views.split_pdf,    name="pdf-split"),
    path("extract-text", views.extract_text, name="pdf-extract-text"),
    path("to-image",     views.to_image,     name="pdf-to-image"),
    path("create",       views.create_pdf,   name="pdf-create"),
    path("protect",      views.protect_pdf,  name="pdf-protect"),
    # ── Vol. VIII  Compresser ────────────────────────────────
    path("compress",     views.compress_pdf,    name="pdf-compress"),

    # ── Vol. IX   Filigrane ──────────────────────────────────
    path("watermark",    views.watermark_pdf,   name="pdf-watermark"),

    # ── Vol. X    Rotation ───────────────────────────────────
    path("rotate",       views.rotate_pdf,      name="pdf-rotate"),

    # ── Vol. XI   Métadonnées ────────────────────────────────
    path("info",         views.pdf_info,        name="pdf-info"),

    # ── Vol. XII  Niveaux de gris ────────────────────────────
    path("grayscale",    views.grayscale_pdf,   name="pdf-grayscale"),
     path("ping", views.ping, name="ping"),
]
