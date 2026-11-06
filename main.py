from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from PIL import Image, ImageDraw, ImageFont
import shutil
import os
import uuid

app = FastAPI(title="AI Camera Studio Backend", version="1.0.0")

UPLOAD_DIR = "uploads"
PROCESSED_DIR = "processed"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

@app.post("/process-image")
async def process_image(file: UploadFile = File(...), prompt: Form(default="Imaginación sin límites") = "Imaginación sin límites"):
    try:
        # Guardar imagen temporal de entrada
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        input_filename = f"{uuid.uuid4()}.{file_extension}"
        input_path = os.path.join(UPLOAD_DIR, input_filename)
        
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Procesamiento con PIL (Simulación de fusión y estilo creativo)
        img = Image.open(input_path)
        draw = ImageDraw.Draw(img)
        
        # Añadir marcos cinematográficos superior e inferior
        bar_height = 90
        draw.rectangle([0, 0, img.width, bar_height], fill=(10, 10, 10))
        draw.rectangle([0, img.height - bar_height, img.width, img.height], fill=(10, 10, 10))
        
        # Título y lema estéticos
        draw.text((30, 25), "AI CAMERA STUDIO — FOTOS CON IMAGINACIÓN", fill=(200, 200, 200))
        
        # Estampar la petición abierta del usuario en la parte inferior
        display_prompt = f"Idea: {prompt}"
        # Recortar texto si es muy largo visualmente
        if len(display_prompt) > 85:
            display_prompt = display_prompt[:82] + "..."
            
        draw.text((30, img.height - 60), display_prompt, fill=(255, 215, 0)) # Tono dorado creativo
        
        # Guardar imagen procesada de salida
        output_filename = f"processed_{input_filename}"
        output_path = os.path.join(PROCESSED_DIR, output_filename)
        img.save(output_path, quality=95)
        
        return FileResponse(output_path, media_type="image/jpeg", filename="foto_imaginacion.jpg")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"status": "AI Camera Studio Backend is running active."}
