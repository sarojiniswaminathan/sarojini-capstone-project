"""HTTP endpoints for the ambient inventory glance strip (plan.md Section 15:
Visual Fabric Inventory) — no dedicated inventory page, just data + photo
upload for the strip rendered on the calendar page itself.
"""

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from agent import inventory
from agent.db import get_connection

router = APIRouter()

UPLOAD_DIR = Path(__file__).resolve().parent / "static" / "uploads" / "materials"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


class AdjustRequest(BaseModel):
    delta: float
    note: str


@router.get("/inventory/glance")
async def inventory_glance():
    conn = get_connection()
    materials = []
    for row in inventory.list_materials(conn):
        summary = inventory.material_summary(conn, row["id"])
        if not summary:
            continue
        summary["photo_url"] = (
            f"/static/uploads/materials/{row['photo_path']}" if row["photo_path"] else None
        )
        materials.append(summary)
    return {"materials": materials}


@router.post("/inventory/{material_id}/adjust")
async def inventory_adjust(material_id: str, payload: AdjustRequest):
    conn = get_connection()
    if inventory.get_material(conn, material_id) is None:
        raise HTTPException(status_code=404, detail="Unknown material")
    new_qty = inventory.manual_correction(conn, material_id, payload.delta, payload.note)
    return {"material_id": material_id, "new_physical_qty": new_qty}


@router.post("/inventory/{material_id}/photo")
async def inventory_photo(material_id: str, file: UploadFile = File(...)):
    conn = get_connection()
    if inventory.get_material(conn, material_id) is None:
        raise HTTPException(status_code=404, detail="Unknown material")

    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {extension or 'unknown'}")

    filename = f"{material_id}-{uuid.uuid4().hex[:8]}{extension}"
    destination = UPLOAD_DIR / filename
    with destination.open("wb") as out_file:
        shutil.copyfileobj(file.file, out_file)

    conn.execute(
        "UPDATE materials SET photo_path = ?, updated_at = datetime('now') WHERE id = ?",
        (filename, material_id),
    )
    conn.commit()
    return {"material_id": material_id, "photo_url": f"/static/uploads/materials/{filename}"}
