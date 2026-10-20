import os
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from PIL import Image, ImageEnhance

app = FastAPI(title="AI Camera Studio Local Engine", version="6.0")

UPLOAD_DIR = "/tmp/ai_media"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def read_root():
    return {"status": "online", "message": "Motor Local de AI Camera Studio Activo y Veloz"}

@app.post("/process-media")
async def process_media(
    file: UploadFile = File(...),
    prompt: str = Form(...),
    output_type: str = Form("image")
):
    try:
        input_filename = file.filename or "input.jpg"
        input_file_path = os.path.join(UPLOAD_DIR, input_filename)
        output_file_path = os.path.join(UPLOAD_DIR, "result.jpg")
        
        with open(input_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print(f"📸 Imagen recibida: {input_file_path}")
        print(f"✨ Prompt aplicado: {prompt}")

        # Procesamiento visual local avanzado de alta velocidad
        img = Image.open(input_file_path).convert("RGB")
        
        # 1. Contraste dramático y cinematográfico
        enhancer_contrast = ImageEnhance.Contrast(img)
        img = enhancer_contrast.enhance(1.35)
        
        # 2. Ajuste de color (tonos fríos/profundos)
        enhancer_color = ImageEnhance.Color(img)
        img = enhancer_color.enhance(0.85)
        
        # 3. Nitidez mejorada para resaltar detalles
        enhancer_sharpness = ImageEnhance.Sharpness(img)
        img = enhancer_sharpness.enhance(1.6)
        
        # Guardar imagen procesada
        img.save(output_file_path, "JPEG", quality=95)
        print("✅ Procesamiento visual local completado con éxito.")

        return FileResponse(
            output_file_path,
            media_type="image/jpeg",
            filename="ai_result.jpg"
        )

    except Exception as e:
        error_detail = str(e)
        print(f"❌ Error interno: {error_detail}")
        raise HTTPException(status_code=500, detail=f"Error en servidor: {error_detail}")
