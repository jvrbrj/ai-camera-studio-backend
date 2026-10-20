import os
import shutil
import httpx
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from PIL import Image, ImageEnhance

app = FastAPI(title="AI Camera Studio - Multi-Endpoint Backend", version="5.0")

HF_TOKEN = os.getenv("HF_TOKEN")

# 🔄 Lista de endpoints gratuitos ordenados por prioridad
FREE_ENDPOINTS = [
    "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
    "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5",
    "https://api-inference.huggingface.co/models/prompthero/openjourney",
    "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"
]

UPLOAD_DIR = "/tmp/ai_media"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def read_root():
    return {"status": "online", "message": "Backend con Rotación de Modelos Activo"}

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
        print(f"✨ Prompt solicitado: {prompt}")

        ai_success = False
        enhanced_prompt = f"{prompt}, highly realistic, 8k resolution, cinematic lighting, photorealistic, masterpiece"
        
        # Headers (si hay token lo usa, si no, intenta llamadas públicas)
        headers = {}
        if HF_TOKEN:
            headers["Authorization"] = f"Bearer {HF_TOKEN}"

        payload = {
            "inputs": enhanced_prompt,
            "parameters": {
                "negative_prompt": "blurry, low quality, distorted, cartoon",
                "num_inference_steps": 25
            }
        }

        # 🔄 PASO DE ROTACIÓN: Probar cada endpoint en la lista
        async with httpx.AsyncClient(timeout=40.0) as client_http:
            for index, endpoint in enumerate(FREE_ENDPOINTS, start=1):
                try:
                    print(f"🔄 Intentando con modelo #{index}: {endpoint.split('/')[-1]}...")
                    response = await client_http.post(endpoint, headers=headers, json=payload)

                    if response.status_code == 200:
                        with open(output_file_path, "wb") as f:
                            f.write(response.content)
                        ai_success = True
                        print(f"✅ ¡Éxito con el modelo #{index}!")
                        break # Salir del bucle porque ya se generó la imagen
                    
                    elif response.status_code in [403, 429, 503]:
                        print(f"⚠️ Modelo #{index} sobrecargado/límite alcanzado (Status {response.status_code}). Saltando al siguiente...")
                    else:
                        print(f"⚠️ Respuesta no esperada de modelo #{index}: {response.status_code}")

                except Exception as endpoint_error:
                    print(f"⚠️ Error al conectar con modelo #{index}: {endpoint_error}")

        # 🛡️ MOTOR LOCAL DE RESPALDO (Fallback final si todos los endpoints fallan o están agotados)
        if not ai_success:
            print("🔄 Todos los modelos remotos están ocupados/agotados. Activando respaldo local...")
            img = Image.open(input_file_path).convert("RGB")
            
            # Mejoras de contraste y estilo fotorrealista local
            enhancer_contrast = ImageEnhance.Contrast(img)
            img = enhancer_contrast.enhance(1.3)
            
            enhancer_color = ImageEnhance.Color(img)
            img = enhancer_color.enhance(0.85)
            
            enhancer_sharpness = ImageEnhance.Sharpness(img)
            img = enhancer_sharpness.enhance(1.5)
            
            img.save(output_file_path, "JPEG", quality=95)
            print("✅ Procesamiento local completado.")

        return FileResponse(
            output_file_path,
            media_type="image/jpeg",
            filename="ai_result.jpg"
        )

    except Exception as e:
        error_detail = str(e)
        print(f"❌ Error interno: {error_detail}")
        raise HTTPException(status_code=500, detail=f"Error en servidor: {error_detail}")
