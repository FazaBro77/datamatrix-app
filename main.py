import cv2
import fitz  # PyMuPDF
import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, Response
from pylibdmtx.pylibdmtx import decode

app = FastAPI()


@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
def index():
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Конвертер PDF в GoLabel</title>
        <style>
            body { font-family: system-ui, sans-serif; padding: 24px; max-width: 480px; margin: auto; }
            input, button { width: 100%; margin: 12px 0; padding: 12px; font-size: 16px; box-sizing: border-box; }
            button { background: #0070f3; color: white; border: none; border-radius: 8px; font-weight: bold; }
        </style>
    </head>
    <body>
        <h2>PDF &rarr; GoLabel (znak.txt)</h2>
        <form action="/process" method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept="application/pdf" required />
            <button type="submit">Обработать и скачать</button>
        </form>
    </body>
    </html>
    """


@app.post("/process")
async def process_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Нужен PDF файл")

    content = await file.read()
    raw_codes = []

    try:
        doc = fitz.open(stream=content, filetype="pdf")
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            pix = page.get_pixmap(dpi=300)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                pix.h, pix.w, pix.n
            )

            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY) if pix.n >= 3 else img
            barcodes = decode(gray)
            barcodes.sort(key=lambda b: (b.rect.top, b.rect.left))

            for b in barcodes:
                raw_codes.append(b.data.decode("utf-8", errors="ignore"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки: {e}")

    if not raw_codes:
        raise HTTPException(
            status_code=422, detail="Коды DataMatrix не найдены"
        )

    output_text = "KM\r\n" + "\r\n".join(raw_codes) + "\r\n"

    return Response(
        content=output_text.encode("utf-8"),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="znak.txt"'},
    )
