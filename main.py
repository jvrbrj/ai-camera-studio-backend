from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from PIL import Image, ImageDraw, ImageFont
import shutil
import os
import uuid

app = FastAPI(title="AI Camera Studio Backend", version="1.1.0")

UPLOAD_DIR = "uploads"
PROCESSED_DIR = "processed"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

@app.post("/process-media")
async def process_media(
    file: UploadFile = File(...), 
    prompt: Form(default="Imaginación sin límites") = "Imaginación sin límites"
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
        
        # 3. Crear un lienzo de composición (Fondo temático basado en la imaginación)
        # Mantenemos las proporciones de la foto del usuario asegurando visibilidad
        width, height = user_image.size
        
        # Creamos un marco cinematográfico y artístico que incluye la foto real al centro
        canvas = Image.new("RGBA", (width, height + 160), (20, 20, 25, 255))
        
        # Pegamos la foto original del usuario en el lienzo principal
        canvas.paste(user_image, (0, 80))
        
        # 4. Dibujar la capa de "Fotos con Imaginación" y el Prompt personalizado
        draw = ImageDraw.Draw(canvas)
        
        # Franja superior para el título de la app
        draw.rectangle([0, 0, width, 75], fill=(10, 10, 15, 230))
        draw.text((25, 25), "✨ AI CAMERA STUDIO — FOTOS CON IMAGINACIÓN", fill=(0, 229, 255))
        
        # Franja inferior para estampar la solicitud creativa del usuario (ej. Medusa en Egipto)
        draw.rectangle([0, height + 80, width, height + 160], fill=(10, 10, 15, 230))
        
        display_prompt = f"Tema: {prompt}"
        if len(display_prompt) > 65:
            display_prompt = display_prompt[:62] + "..."
            
        draw.text((25, height + 105), display_prompt, fill=(255, 215, 0)) # Color dorado creativo
        
        # 5. Guardar el resultado final fusionado
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
