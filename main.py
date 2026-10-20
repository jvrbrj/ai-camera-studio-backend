import os
import shutil
import urllib.parse
import httpx
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

app = FastAPI(title="AI Camera Studio Public AI Engine", version="7.0")

UPLOAD_DIR = "/tmp/ai_media"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def read_root():
    return {"status": "online", "message": "Motor de IA Pública Activo"}

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

        print(f"📸 Imagen de referencia recibida: {input_file_path}")
        print(f"✨ Generando con IA pública el prompt: {prompt}")

        # Enriquecer el prompt para asegurar un resultado fotorrealista y cinematográfico
        full_prompt = f"{prompt}, photorealistic, 8k resolution, cinematic lighting, highly detailed masterpiece"
        
        # Codificar el prompt para que sea compatible con una URL web
        encoded_prompt = urllib.parse.quote(full_prompt)
        
        # URL de la IA pública gratuita (genera imágenes directas por URL sin tokens)
        ai_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"

        # Descargar la imagen generada por la IA
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.get(ai_url)
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Error al generar imagen con la IA pública")
            
            with open(output_file_path, "wb") as f:
                f.write(response.content)

        print("✅ ¡Imagen generada e interpretada por la IA con éxito!")

        return FileResponse(
            output_file_path,
            media_type="image/jpeg",
            filename="ai_result.jpg"
        )

    except Exception as e:
        error_detail = str(e)
        print(f"❌ Error en servidor: {error_detail}")
        raise HTTPException(status_code=500, detail=f"Error en servidor: {error_detail}")
