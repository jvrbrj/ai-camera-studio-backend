import os
import shutil
import httpx
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

app = FastAPI(title="AI Camera Studio Free Backend", version="4.0")

# 🛡️ El token de Hugging Face se lee de las variables de entorno en Render
HF_TOKEN = os.getenv("HF_TOKEN")

# Modelo de generación de imágenes fotorrealistas de código abierto
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"

UPLOAD_DIR = "/tmp/ai_media"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def read_root():
    return {"status": "online", "message": "AI Camera Studio Backend Activo y Sin Costo"}

@app.post("/process-media")
async def process_media(
    file: UploadFile = File(...),
    prompt: str = Form(...),
    output_type: str = Form("image")
):
    try:
        # Guardar la imagen enviada por la app de Flutter
        input_filename = file.filename or "input.jpg"
        input_file_path = os.path.join(UPLOAD_DIR, input_filename)
        
        with open(input_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print(f"📸 Imagen recibida: {input_file_path}")
        print(f"✨ Prompt realista: {prompt}")

        # Enriquecer el prompt del usuario para forzar máxima calidad y fotorrealismo
        enhanced_prompt = f"{prompt}, highly realistic, 8k resolution, cinematic lighting, photorealistic, detailed texture, masterpiece"

        headers = {}
        if HF_TOKEN:
            headers["Authorization"] = f"Bearer {HF_TOKEN}"

        # Petición a la API de inferencia de IA fotorrealista
        async with httpx.AsyncClient(timeout=90.0) as client_http:
            # Enviamos el prompt enriquecido al motor de generación
            payload = {
                "inputs": enhanced_prompt,
                "parameters": {
                    "negative_prompt": "blurry, low quality, distorted, cartoon, anime, drawing, fake",
                    "num_inference_steps": 30
                }
            }

            response = await client_http.post(
                API_URL,
                headers=headers,
                json=payload
            )

            if response.status_code != 200:
                print(f"❌ Error en API IA: {response.text}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"Error al generar imagen con IA (Status {response.status_code})"
                )

            # Guardar el resultado fotorrealista generado
            output_file_path = os.path.join(UPLOAD_DIR, "result.jpg")
            with open(output_file_path, "wb") as f:
                f.write(response.content)

        # Retornar la imagen fotorrealista a tu Moto G15
        return FileResponse(
            output_file_path,
            media_type="image/jpeg",
            filename="ai_result.jpg"
        )

    except Exception as e:
        error_detail = str(e)
        print(f"❌ Error interno: {error_detail}")
        raise HTTPException(status_code=500, detail=f"Error en servidor: {error_detail}")
