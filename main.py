from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
import shutil
import os
import uuid
import requests
from openai import OpenAI

app = FastAPI(title="AI Camera Studio Pro Backend", version="2.0.0")

# Inicializar cliente de OpenAI (asegurate de configurar OPENAI_API_KEY en Render)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

UPLOAD_DIR = "uploads"
PROCESSED_DIR = "processed"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

@app.post("/process-media")
async def process_media(
    file: UploadFile = File(...), 
    prompt: str = Form("Cinematic masterpice, highly detailed")
):
    try:
        # 1. Guardar la foto original capturada por el usuario
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        input_filename = f"{uuid.uuid4()}.{file_extension}"
        input_path = os.path.join(UPLOAD_DIR, input_filename)
        
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 2. Enriquecer el prompt del usuario para garantizar máxima calidad visual y nitidez
        enhanced_prompt = (
            f"A stunning, photorealistic, ultra-sharp 8k resolution cinematic photograph of {prompt}. "
            f"Hyper-detailed textures, dramatic professional studio lighting, masterpiece composition, "
            f"flawless visual clarity and depth of field."
        )

        # 3. Llamar a la API de generación de IA (DALL-E 3 para máxima calidad y nitidez)
        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt=enhanced_prompt,
                size="1024x1024",
                quality="hd",
                n=1,
            )
            image_url = response.data[0].url
            
            # 4. Descargar la imagen de alta calidad generada por la IA
            img_data = requests.get(image_url).content
            output_filename = f"hd_imaginacion_{uuid.uuid4()}.jpg"
            output_path = os.path.join(PROCESSED_DIR, output_filename)
            
            with open(output_path, "wb") as handler:
                handler.write(img_data)
                
            return FileResponse(output_path, media_type="image/jpeg", filename="foto_imaginacion_hd.jpg")
            
        except Exception as ai_error:
            # Fallback seguro en caso de que la API falle temporalmente
            raise HTTPException(status_code=500, detail=f"Error en el motor de IA generativa: {str(ai_error)}")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"status": "AI Camera Studio Pro (HD Generation Engine) is running active."}
