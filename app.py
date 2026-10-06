"""Wallpaper Kanri - trang upload và quản lý hình nền (Flask)."""

import math
import os
import uuid
from datetime import datetime
from pathlib import Path

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from PIL import Image, UnidentifiedImageError
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
THUMB_DIR = UPLOAD_DIR / ".thumbs"

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "bmp"}
PER_PAGE_OPTIONS = (6, 12, 24, 48)
DEFAULT_PER_PAGE = 12
THUMB_SIZE = (480, 320)
MAX_UPLOAD_MB = 50

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "wallpaper-kanri-dev")
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024

UPLOAD_DIR.mkdir(exist_ok=True)
THUMB_DIR.mkdir(exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def human_size(num_bytes):
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024 or unit == "GB":
            return f"{num_bytes:.0f} {unit}" if unit == "B" else f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024


def list_images():
    """Trả về danh sách ảnh đã upload, mới nhất trước."""
    images = []
    for path in UPLOAD_DIR.iterdir():
        if not path.is_file() or not allowed_file(path.name):
            continue
        stat = path.stat()
        try:
            with Image.open(path) as img:
                width, height = img.size
        except (UnidentifiedImageError, OSError):
            width = height = 0
        images.append(
            {
                "name": path.name,
                "display_name": path.name.split("_", 1)[-1],
                "size": human_size(stat.st_size),
                "bytes": stat.st_size,
                "width": width,
                "height": height,
                "mtime": stat.st_mtime,
                "uploaded": datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M"),
            }
        )
    images.sort(key=lambda i: i["mtime"], reverse=True)
    return images


def make_thumbnail(filename):
    src = UPLOAD_DIR / filename
    dst = THUMB_DIR / (Path(filename).stem + ".webp")
    if not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime:
        with Image.open(src) as img:
            img = img.convert("RGBA" if img.mode in ("P", "LA", "RGBA") else "RGB")
            img.thumbnail(THUMB_SIZE)
            img.save(dst, "WEBP", quality=82)
    return dst


def page_window(page, total_pages, radius=2):
    """Danh sách số trang để hiển thị, dùng None cho dấu '…'."""
    pages = []
    for p in range(1, total_pages + 1):
        if p in (1, total_pages) or abs(p - page) <= radius:
            pages.append(p)
        elif pages and pages[-1] is not None:
            pages.append(None)
    return pages


def get_per_page():
    per_page = request.args.get("per_page", DEFAULT_PER_PAGE, type=int)
    return per_page if per_page in PER_PAGE_OPTIONS else DEFAULT_PER_PAGE


@app.context_processor
def inject_globals():
    images = list_images()
    return {
        "total_images": len(images),
        "total_size": human_size(sum(i["bytes"] for i in images)),
        "per_page_options": PER_PAGE_OPTIONS,
        "allowed_ext": ", ".join(sorted(ALLOWED_EXTENSIONS)),
        "max_upload_mb": MAX_UPLOAD_MB,
    }


@app.route("/")
def index():
    images = list_images()
    per_page = get_per_page()
    total_pages = max(1, math.ceil(len(images) / per_page))
    page = min(max(1, request.args.get("page", 1, type=int)), total_pages)
    start = (page - 1) * per_page
    return render_template(
        "index.html",
        images=images[start : start + per_page],
        start=start,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        pages=page_window(page, total_pages),
    )


@app.route("/view/<int:position>")
def view(position):
    """Xem từng ảnh một, mỗi ảnh là một trang (paging)."""
    images = list_images()
    if not images:
        return redirect(url_for("index"))
    position = min(max(1, position), len(images))
    return render_template(
        "view.html",
        image=images[position - 1],
        position=position,
        count=len(images),
        pages=page_window(position, len(images)),
        back_page=math.ceil(position / get_per_page()),
        per_page=get_per_page(),
    )


@app.route("/upload", methods=["POST"])
def upload():
    files = [f for f in request.files.getlist("images") if f and f.filename]
    if not files:
        flash("Vui lòng chọn ít nhất một hình ảnh.", "error")
        return redirect(url_for("index"))

    saved, rejected = 0, []
    for file in files:
        if not allowed_file(file.filename):
            rejected.append(file.filename)
            continue
        try:
            Image.open(file.stream).verify()
        except (UnidentifiedImageError, OSError, SyntaxError):
            rejected.append(file.filename)
            continue
        file.stream.seek(0)
        safe = secure_filename(file.filename) or f"image.{file.filename.rsplit('.', 1)[-1]}"
        name = f"{uuid.uuid4().hex[:8]}_{safe}"
        file.save(UPLOAD_DIR / name)
        saved += 1

    if saved:
        flash(f"Đã upload {saved} hình ảnh.", "success")
    if rejected:
        flash("Không hợp lệ, đã bỏ qua: " + ", ".join(rejected), "error")
    return redirect(url_for("index"))


@app.route("/delete/<path:filename>", methods=["POST"])
def delete(filename):
    path = UPLOAD_DIR / secure_filename(filename)
    if not path.is_file():
        abort(404)
    path.unlink()
    (THUMB_DIR / (path.stem + ".webp")).unlink(missing_ok=True)
    flash("Đã xóa hình ảnh.", "success")
    return redirect(request.form.get("next") or url_for("index"))


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(
        UPLOAD_DIR, filename, as_attachment=request.args.get("download") == "1"
    )


@app.route("/thumbs/<path:filename>")
def thumbnail(filename):
    filename = secure_filename(filename)
    if not (UPLOAD_DIR / filename).is_file():
        abort(404)
    thumb = make_thumbnail(filename)
    return send_from_directory(THUMB_DIR, thumb.name)


@app.errorhandler(RequestEntityTooLarge)
def too_large(_):
    flash(f"Tổng dung lượng upload vượt quá {MAX_UPLOAD_MB} MB.", "error")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
