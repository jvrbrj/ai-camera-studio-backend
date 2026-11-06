from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from PIL import Image, ImageDraw, ImageFont
import shutil
import os
import uuid

app = FastAPI(title="AI Camera Studio Backend", version="1.1.1")

UPLOAD_DIR = "uploads"
PROCESSED_DIR = "processed"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

@app.post("/process-media")
async def process_media(
    file: UploadFile = File(...), 
    prompt: str = Form("Imaginación sin límites")
):
    try:
        # 1. Guardar la foto original capturada por el usuario
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        input_filename = f"{uuid.uuid4()}.{file_extension}"
        input_path = os.path.join(UPLOAD_DIR, input_filename)
        
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 2. Cargar la imagen con PIL
        user_image = Image.open(input_path).convert("RGBA")
        width, height = user_image.size
        
        # 3. Crear lienzo de composición (Fondo temático)
        canvas = Image.new("RGBA", (width, height + 160), (20, 20, 25, 255))
        canvas.paste(user_image, (0, 80))
        
        # 4. Dibujar la capa de "Fotos con Imaginación" y el Prompt personalizado
        draw = ImageDraw.Draw(canvas)
        
        # Franja superior para el título
        draw.rectangle([0, 0, width, 75], fill=(10, 10, 15, 230))
        draw.text((25, 25), "✨ AI CAMERA STUDIO — FOTOS CON IMAGINACIÓN", fill=(0, 229, 255))
        
        # Franja inferior para el prompt del usuario
        draw.rectangle([0, height + 80, width, height + 160], fill=(10, 10, 15, 230))
        
        display_prompt = f"Tema: {prompt}"
        if len(display_prompt) > 65:
            display_prompt = display_prompt[:62] + "..."
            
        draw.text((25, height + 105), display_prompt, fill=(255, 215, 0))
        
        # 5. Guardar resultado final fusionado
        output_filename = f"fused_{input_filename}"
        output_path = os.path.join(PROCESSED_DIR, output_filename)
        
        final_image = canvas.convert("RGB")
        final_image.save(output_path, quality=95)
        
        return FileResponse(output_path, media_type="image/jpeg", filename="foto_fusionada.jpg")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"status": "AI Camera Studio Backend (Fusión Activa) is running."}
