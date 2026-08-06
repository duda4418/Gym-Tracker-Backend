"""Import legacy QR image files into their PostgreSQL user records."""
import mimetypes
from pathlib import Path

from app.core.config import get_settings
from app.db.database import session_scope
from app.db.models.users import User
from app.services.qr_service import QR_IMAGE_URL

MAX_QR_SIZE_BYTES = 1024 * 1024
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}


def import_qr_codes() -> tuple[int, int]:
    settings = get_settings()
    uploads_root = Path(settings.UPLOADS_DIR).resolve()
    imported = 0
    skipped = 0

    with session_scope() as session:
        users = session.query(User).filter(User.qr_code.is_not(None), User.qr_code_data.is_(None)).all()
        for user in users:
            relative_path = str(user.qr_code).removeprefix("/uploads/")
            image_path = (uploads_root / relative_path).resolve()
            content_type, _ = mimetypes.guess_type(image_path.name)

            if (
                not image_path.is_relative_to(uploads_root)
                or not image_path.is_file()
                or image_path.stat().st_size > MAX_QR_SIZE_BYTES
                or content_type not in ALLOWED_CONTENT_TYPES
            ):
                skipped += 1
                continue

            user.qr_code = QR_IMAGE_URL
            user.qr_code_data = image_path.read_bytes()
            user.qr_code_content_type = content_type
            imported += 1

    return imported, skipped


if __name__ == "__main__":
    imported_count, skipped_count = import_qr_codes()
    print(f"Imported {imported_count} QR code(s); skipped {skipped_count}.")