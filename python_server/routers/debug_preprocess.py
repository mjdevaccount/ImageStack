# python_server/routers/debug_preprocess.py

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from tempfile import TemporaryDirectory
from pathlib import Path
import zipfile
import json
from loguru import logger

from ..utils.image_io import save_temp_image
from ..services.image_preprocess import (
    debug_preprocess_ocr_pipeline,
    debug_preprocess_vision_pipeline,
)

router = APIRouter()


@router.post("/preprocess")
async def debug_preprocess(file: UploadFile = File(...)):
    """
    Returns a ZIP containing:
    - original image
    - OCR pipeline stages (gray, denoised, contrast, binarized, deskewed) + final
    - Vision pipeline stages (resized, sharpened) + final
    - metadata.json with shapes, config, etc.
    - viewer.html to inspect all images in a browser
    """

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Save original to your normal storage (so it behaves like the rest of the system)
    original_path = await save_temp_image(file)
    original_ext = Path(original_path).suffix or ".png"
    logger.info(f"[debug] Original image saved: {original_path}")

    with TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)

        # Subdirs inside the zip
        ocr_dir = tmp_root / "ocr"
        vision_dir = tmp_root / "vision"
        ocr_dir.mkdir(parents=True, exist_ok=True)
        vision_dir.mkdir(parents=True, exist_ok=True)

        # Run debug pipelines (write intermediates into ocr/ and vision/)
        ocr_final_rel, ocr_meta = debug_preprocess_ocr_pipeline(
            original_path,
            out_dir=ocr_dir,
        )

        vision_final_rel, vision_meta = debug_preprocess_vision_pipeline(
            original_path,
            out_dir=vision_dir,
        )

        # Build metadata.json contents
        metadata = {
            "original": {
                "file": f"original{original_ext}",
            },
            "ocr": ocr_meta,
            "vision": vision_meta,
        }

        # Create viewer.html
        viewer_html_path = tmp_root / "viewer.html"
        _write_viewer_html(
            viewer_html_path,
            original_name=f"original{original_ext}",
            ocr_meta=ocr_meta,
            vision_meta=vision_meta,
        )

        # Write metadata.json
        metadata_path = tmp_root / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        # Build ZIP
        zip_path = tmp_root / "preprocess_debug.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Original
            zf.write(original_path, f"original{original_ext}")

            # OCR pipeline files
            for stage in ocr_meta.get("stages", []):
                rel = stage["file"]  # e.g. "ocr/ocr_stage_01_gray.png"
                src = tmp_root / rel
                if src.exists():
                    zf.write(src, rel)
            final_ocr = ocr_meta.get("final", {}).get("file")
            if final_ocr:
                src = tmp_root / final_ocr
                if src.exists():
                    zf.write(src, final_ocr)

            # Vision pipeline files
            for stage in vision_meta.get("stages", []):
                rel = stage["file"]  # e.g. "vision/vision_stage_01_resized.png"
                src = tmp_root / rel
                if src.exists():
                    zf.write(src, rel)
            final_vis = vision_meta.get("final", {}).get("file")
            if final_vis:
                src = tmp_root / final_vis
                if src.exists():
                    zf.write(src, final_vis)

            # Metadata + viewer
            zf.write(metadata_path, "metadata.json")
            zf.write(viewer_html_path, "viewer.html")

        logger.info(f"[debug] ZIP file ready: {zip_path}")

        return FileResponse(
            path=str(zip_path),
            media_type="application/zip",
            filename="preprocess_debug.zip",
        )


def _write_viewer_html(
    path: Path,
    original_name: str,
    ocr_meta: dict,
    vision_meta: dict,
) -> None:
    """Generate a simple HTML viewer to compare original/OCR/Vision stages."""
    def img_tag(rel_path: str, label: str) -> str:
        return f"""
        <div class="img-block">
          <div class="img-label">{label}</div>
          <img src="{rel_path}" loading="lazy">
        </div>
        """

    ocr_stages_html = ""
    for stage in ocr_meta.get("stages", []):
        label = stage["name"]
        rel = stage["file"]
        ocr_stages_html += img_tag(rel, label)

    ocr_final = ocr_meta.get("final", {}).get("file")
    if ocr_final:
        ocr_stages_html += img_tag(ocr_final, "final (ocr)")

    vision_stages_html = ""
    for stage in vision_meta.get("stages", []):
        label = stage["name"]
        rel = stage["file"]
        vision_stages_html += img_tag(rel, label)

    vision_final = vision_meta.get("final", {}).get("file")
    if vision_final:
        vision_stages_html += img_tag(vision_final, "final (vision)")

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>ImageStack Preprocess Debug</title>
  <style>
    body {{
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #111;
      color: #eee;
      margin: 0;
      padding: 1rem 2rem 3rem;
    }}
    h1, h2 {{
      margin-top: 1.5rem;
    }}
    .section {{
      margin-bottom: 2rem;
    }}
    .img-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 1rem;
    }}
    .img-block {{
      background: #1e1e1e;
      border-radius: 8px;
      padding: 0.5rem;
      box-shadow: 0 0 10px rgba(0,0,0,0.6);
      max-width: 400px;
    }}
    .img-block img {{
      max-width: 100%;
      border-radius: 4px;
      display: block;
    }}
    .img-label {{
      font-size: 0.85rem;
      margin-bottom: 0.25rem;
      color: #aaa;
    }}
    code {{
      background: #222;
      padding: 0.1rem 0.3rem;
      border-radius: 4px;
    }}
  </style>
</head>
<body>
  <h1>ImageStack &mdash; Preprocess Debug Viewer</h1>

  <div class="section">
    <h2>Original</h2>
    <div class="img-row">
      {img_tag(original_name, "original")}
    </div>
  </div>

  <div class="section">
    <h2>OCR Pipeline</h2>
    <p>Stages show how the image is transformed before EasyOCR.</p>
    <div class="img-row">
      {ocr_stages_html}
    </div>
  </div>

  <div class="section">
    <h2>Vision Pipeline</h2>
    <p>Stages show how the image is prepped for the vision LLM.</p>
    <div class="img-row">
      {vision_stages_html}
    </div>
  </div>

  <div class="section">
    <h2>Metadata</h2>
    <p>See <code>metadata.json</code> in this ZIP for full details.</p>
  </div>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")
