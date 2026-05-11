import io
import os

import pypdfium2 as pdfium
from PIL import Image, ImageDraw, ImageFont

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

import PyPDF2
from reportlab.pdfgen import canvas as rlcanvas
from reportlab.lib.utils import ImageReader


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _get_file(request, key="file"):
    f = request.FILES.get(key)
    if not f:
        return None, JsonResponse({"error": "Fichier manquant."}, status=400)
    return f, None


def _pdf_response(buffer, filename):
    buffer.seek(0)
    resp = HttpResponse(buffer.read(), content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    resp["Access-Control-Expose-Headers"] = "Content-Disposition, X-Compression-Ratio"
    return resp


# ═════════════════════════════════════════════════════════════
# Vol. I — Fusionner
# ═════════════════════════════════════════════════════════════

@csrf_exempt
@require_POST
def merge_pdfs(request):
    files = request.FILES.getlist("files")
    if len(files) < 2:
        return JsonResponse({"error": "Au moins 2 fichiers requis."}, status=400)
    try:
        writer = PyPDF2.PdfWriter()
        for f in files:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                writer.add_page(page)
        out = io.BytesIO()
        writer.write(out)
        return _pdf_response(out, "merged.pdf")
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ═════════════════════════════════════════════════════════════
# Vol. II — Extraire pages
# ═════════════════════════════════════════════════════════════

@csrf_exempt
@require_POST
def split_pdf(request):
    file, err = _get_file(request)
    if err:
        return err
    try:
        start  = int(request.POST.get("start", 1)) - 1
        end    = int(request.POST.get("end",   1)) - 1
        reader = PyPDF2.PdfReader(file)
        total  = len(reader.pages)
        start  = max(0, min(start, total - 1))
        end    = max(start, min(end, total - 1))
        writer = PyPDF2.PdfWriter()
        for i in range(start, end + 1):
            writer.add_page(reader.pages[i])
        out = io.BytesIO()
        writer.write(out)
        return _pdf_response(out, "extracted.pdf")
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ═════════════════════════════════════════════════════════════
# Vol. III — Extraire texte
# ═════════════════════════════════════════════════════════════

@csrf_exempt
@require_POST
def extract_text(request):
    file, err = _get_file(request)
    if err:
        return err
    try:
        reader = PyPDF2.PdfReader(file)
        lines  = []
        for i, page in enumerate(reader.pages):
            lines.append(f"=== Page {i + 1} ===")
            lines.append(page.extract_text() or "(aucun texte)")
        text = "\n\n".join(lines)
        return HttpResponse(text, content_type="text/plain; charset=utf-8")
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ═════════════════════════════════════════════════════════════
# Vol. IV — Convertir en image JPG
# ═════════════════════════════════════════════════════════════

@csrf_exempt
@require_POST
def to_image(request):
    file, err = _get_file(request)
    if err:
        return err
    try:
        raw    = file.read()
        doc    = pdfium.PdfDocument(raw)
        page   = doc[0]
        bitmap = page.render(scale=2.0, rotation=0)
        pil_img = bitmap.to_pil().convert("RGB")
        out = io.BytesIO()
        pil_img.save(out, format="JPEG", quality=90)
        out.seek(0)
        resp = HttpResponse(out.read(), content_type="image/jpeg")
        resp["Content-Disposition"] = 'attachment; filename="page1.jpg"'
        return resp
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ═════════════════════════════════════════════════════════════
# Vol. V — Créer un PDF
# ═════════════════════════════════════════════════════════════

@csrf_exempt
@require_POST
def create_pdf(request):
    content = request.POST.get("content", "").strip()
    if not content:
        return JsonResponse({"error": "Contenu vide."}, status=400)
    try:
        out    = io.BytesIO()
        c      = rlcanvas.Canvas(out, pagesize=(595, 842))  # A4
        c.setFont("Helvetica", 12)
        margin, y, line_h = 50, 800, 16
        for line in content.split("\n"):
            while len(line) > 90:
                c.drawString(margin, y, line[:90])
                line = line[90:]
                y -= line_h
                if y < 60:
                    c.showPage()
                    c.setFont("Helvetica", 12)
                    y = 800
            c.drawString(margin, y, line)
            y -= line_h
            if y < 60:
                c.showPage()
                c.setFont("Helvetica", 12)
                y = 800
        c.save()
        return _pdf_response(out, "created.pdf")
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ═════════════════════════════════════════════════════════════
# Vol. VI — Protéger
# ═════════════════════════════════════════════════════════════

@csrf_exempt
@require_POST
def protect_pdf(request):
    file, err = _get_file(request)
    if err:
        return err
    password = request.POST.get("password", "").strip()
    if not password:
        return JsonResponse({"error": "Mot de passe requis."}, status=400)
    try:
        reader = PyPDF2.PdfReader(file)
        writer = PyPDF2.PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.encrypt(password)
        out = io.BytesIO()
        writer.write(out)
        return _pdf_response(out, "protected.pdf")
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ═════════════════════════════════════════════════════════════
# Vol. VIII — Compresser
# ═════════════════════════════════════════════════════════════

@csrf_exempt
@require_POST
def compress_pdf(request):
    file, err = _get_file(request)
    if err:
        return err

    original_bytes = file.read()
    original_size  = len(original_bytes)

    try:
        doc        = pdfium.PdfDocument(original_bytes)
        output_pdf = PyPDF2.PdfWriter()

        for i in range(len(doc)):
            page    = doc[i]
            bitmap  = page.render(scale=1.0, rotation=0)
            pil_img = bitmap.to_pil()
            if pil_img.mode != "RGB":
                pil_img = pil_img.convert("RGB")

            img_buf = io.BytesIO()
            pil_img.save(img_buf, format="JPEG", quality=60, optimize=True)
            img_buf.seek(0)

            w_pt, h_pt = pil_img.size
            page_buf   = io.BytesIO()
            c = rlcanvas.Canvas(page_buf, pagesize=(w_pt, h_pt))
            c.drawImage(ImageReader(img_buf), 0, 0, width=w_pt, height=h_pt)
            c.save()
            page_buf.seek(0)
            output_pdf.add_page(PyPDF2.PdfReader(page_buf).pages[0])

        out_buf         = io.BytesIO()
        output_pdf.write(out_buf)
        compressed_size = len(out_buf.getvalue())
        ratio_pct       = round((1 - compressed_size / original_size) * 100, 1) if original_size else 0
        ratio_str       = f"{ratio_pct}%" if ratio_pct >= 0 else f"+{abs(ratio_pct)}%"

        out_buf.seek(0)
        resp = HttpResponse(out_buf.read(), content_type="application/pdf")
        resp["Content-Disposition"]           = 'attachment; filename="compressed.pdf"'
        resp["X-Compression-Ratio"]           = ratio_str
        resp["Access-Control-Expose-Headers"] = "Content-Disposition, X-Compression-Ratio"
        return resp

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ═════════════════════════════════════════════════════════════
# Vol. IX — Filigrane
# ═════════════════════════════════════════════════════════════

@csrf_exempt
@require_POST
def watermark_pdf(request):
    file, err = _get_file(request)
    if err:
        return err

    text    = request.POST.get("text",    "CONFIDENTIEL")
    opacity = float(request.POST.get("opacity", "0.15"))
    color   = request.POST.get("color",   "888888").lstrip("#")

    try:
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
    except Exception:
        r, g, b = 136, 136, 136

    alpha = int(max(0.0, min(1.0, opacity)) * 255)

    try:
        doc        = pdfium.PdfDocument(file.read())
        output_pdf = PyPDF2.PdfWriter()

        for i in range(len(doc)):
            page    = doc[i]
            bitmap  = page.render(scale=2.0, rotation=0)
            pil_img = bitmap.to_pil().convert("RGBA")

            font_size = max(40, pil_img.width // 10)
            try:
                font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size
                )
            except Exception:
                try:
                    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", font_size)
                except Exception:
                    font = ImageFont.load_default()

            draw = ImageDraw.Draw(Image.new("RGBA", pil_img.size, (0, 0, 0, 0)))
            bbox = draw.textbbox((0, 0), text, font=font)
            tw   = bbox[2] - bbox[0]
            th   = bbox[3] - bbox[1]
            x    = (pil_img.width  - tw) / 2
            y    = (pil_img.height - th) / 2

            tmp      = Image.new("RGBA", pil_img.size, (255, 255, 255, 0))
            tmp_draw = ImageDraw.Draw(tmp)
            tmp_draw.text((x, y), text, font=font, fill=(r, g, b, alpha))
            tmp      = tmp.rotate(45, expand=False)

            combined = Image.alpha_composite(pil_img, tmp).convert("RGB")
            img_buf  = io.BytesIO()
            combined.save(img_buf, format="JPEG", quality=85)
            img_buf.seek(0)

            w_pt, h_pt = pil_img.size
            page_buf   = io.BytesIO()
            c = rlcanvas.Canvas(page_buf, pagesize=(w_pt, h_pt))
            c.drawImage(ImageReader(img_buf), 0, 0, width=w_pt, height=h_pt)
            c.save()
            page_buf.seek(0)
            output_pdf.add_page(PyPDF2.PdfReader(page_buf).pages[0])

        out = io.BytesIO()
        output_pdf.write(out)
        return _pdf_response(out, "watermarked.pdf")

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ═════════════════════════════════════════════════════════════
# Vol. X — Rotation
# ═════════════════════════════════════════════════════════════

@csrf_exempt
@require_POST
def rotate_pdf(request):
    file, err = _get_file(request)
    if err:
        return err

    try:
        angle     = int(request.POST.get("angle", "90"))
        pages_raw = request.POST.get("pages", "all").strip()
    except ValueError:
        return JsonResponse({"error": "Paramètres invalides."}, status=400)

    try:
        reader = PyPDF2.PdfReader(file)
        writer = PyPDF2.PdfWriter()
        total  = len(reader.pages)

        if pages_raw.lower() == "all":
            target = set(range(total))
        else:
            target = set()
            for part in pages_raw.split(","):
                part = part.strip()
                if part.isdigit():
                    idx = int(part) - 1
                    if 0 <= idx < total:
                        target.add(idx)

        for i, page in enumerate(reader.pages):
            if i in target:
                page.rotate(angle)
            writer.add_page(page)

        out = io.BytesIO()
        writer.write(out)
        return _pdf_response(out, "rotated.pdf")

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ═════════════════════════════════════════════════════════════
# Vol. XI — Informations / Métadonnées
# ═════════════════════════════════════════════════════════════

@csrf_exempt
@require_POST
def pdf_info(request):
    file, err = _get_file(request)
    if err:
        return err

    try:
        raw        = file.read()
        size_bytes = len(raw)
        reader     = PyPDF2.PdfReader(io.BytesIO(raw))
        meta       = reader.metadata or {}
        pages      = len(reader.pages)
        page_dims  = None

        if pages > 0:
            p0   = reader.pages[0]
            w_pt = float(p0.mediabox.width)
            h_pt = float(p0.mediabox.height)
            page_dims = {
                "width_mm":  round(w_pt * 25.4 / 72, 1),
                "height_mm": round(h_pt * 25.4 / 72, 1),
            }

        return JsonResponse({
            "filename":  file.name,
            "size_kb":   round(size_bytes / 1024, 1),
            "size_mb":   round(size_bytes / 1024 / 1024, 2),
            "pages":     pages,
            "encrypted": reader.is_encrypted,
            "page_dims": page_dims,
            "metadata": {
                "title":    meta.get("/Title",    ""),
                "author":   meta.get("/Author",   ""),
                "creator":  meta.get("/Creator",  ""),
                "producer": meta.get("/Producer", ""),
            },
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ═════════════════════════════════════════════════════════════
# Vol. XII — Niveaux de gris
# ═════════════════════════════════════════════════════════════

@csrf_exempt
@require_POST
def grayscale_pdf(request):
    file, err = _get_file(request)
    if err:
        return err

    try:
        dpi   = int(request.POST.get("dpi", "150"))
        scale = dpi / 72.0
    except ValueError:
        scale = 150 / 72.0

    try:
        raw        = file.read()
        doc        = pdfium.PdfDocument(raw)
        output_pdf = PyPDF2.PdfWriter()

        for i in range(len(doc)):
            page    = doc[i]
            bitmap  = page.render(scale=scale, rotation=0)
            pil_img = bitmap.to_pil().convert("L").convert("RGB")

            img_buf = io.BytesIO()
            pil_img.save(img_buf, format="JPEG", quality=85, optimize=True)
            img_buf.seek(0)

            w_px, h_px = pil_img.size
            page_buf   = io.BytesIO()
            c = rlcanvas.Canvas(page_buf, pagesize=(w_px, h_px))
            c.drawImage(ImageReader(img_buf), 0, 0, width=w_px, height=h_px)
            c.save()
            page_buf.seek(0)
            output_pdf.add_page(PyPDF2.PdfReader(page_buf).pages[0])

        out = io.BytesIO()
        output_pdf.write(out)
        return _pdf_response(out, "grayscale.pdf")

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
        # ═════════════════════════════════════════════════════════════
# Keep-alive — Ping
# ═════════════════════════════════════════════════════════════

from django.views.decorators.http import require_http_methods

@csrf_exempt
@require_http_methods(["GET", "HEAD"])
def ping(request):
    return JsonResponse({"status": "ok"})
