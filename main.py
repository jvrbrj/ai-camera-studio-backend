import os
import shutil
import urllib.parse
import httpx
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from PIL import Image, ImageEnhance

app = FastAPI(title="AI Camera Studio - Hybrid Backend", version="9.0")

UPLOAD_DIR = "/tmp/ai_media"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def read_root():
    return {"status": "online", "message": "Backend Híbrido Activo (Filtros Locales + IA en la Nube)"}

# ---------------------------------------------------------
# RUTA 1: Vía Rápida - Filtros y Estilos Locales (Instantáneo)
# ---------------------------------------------------------
@app.post("/process-filter")
async def process_filter(
    file: UploadFile = File(...),
    style: str = Form("cinematic")
):
    try:
        input_filename = file.filename or "input.jpg"
        input_file_path = os.path.join(UPLOAD_DIR, input_filename)
        output_file_path = os.path.join(UPLOAD_DIR, "result_filter.jpg")
        
        with open(input_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print(f"🎨 Aplicando filtro local rápido ({style})...")
        
        img = Image.open(input_file_path).convert("RGB")
        
        # Procesamiento visual dramático / cinematográfico
        enhancer_contrast = ImageEnhance.Contrast(img)
        img = enhancer_contrast.enhance(1.4)
        
        enhancer_color = ImageEnhance.Color(img)
        img = enhancer_color.enhance(0.75) # Tonos fríos y profundos
        
        enhancer_sharpness = ImageEnhance.Sharpness(img)
        img = enhancer_sharpness.enhance(1.5)
        
        img.save(output_file_path, "JPEG", quality=95)
        print("✅ Filtro local aplicado con éxito.")

        return FileResponse(
            output_file_path,
            media_type="image/jpeg",
            filename="filter_result.jpg"
        )
    except Exception as e:
        error_detail = str(e)
        print(f"❌ Error en filtro local: {error_detail}")
        raise HTTPException(status_code=500, detail=f"Error en filtro local: {error_detail}")


# ---------------------------------------------------------
# RUTA 2: Vía Mágica - Generación de Escenas por IA con Prompt
# ---------------------------------------------------------
@app.post("/process-ai")
async def process_ai(
    file: UploadFile = File(...),
    prompt: str = Form(...)
):
    try:
        input_filename = file.filename or "input.jpg"
        input_file_path = os.path.join(UPLOAD_DIR, input_filename)
        output_file_path = os.path.join(UPLOAD_DIR, "result_ai.jpg")
        
        with open(input_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print(f"✨ Procesando prompt de IA: {prompt}")

        success_ai = False
        try:
            # Petición al servicio web de IA generativa
            full_prompt = f"{prompt}, photorealistic, dramatic cinematic lighting, masterpiece"
            encoded_prompt = urllib.parse.quote(full_prompt)
            ai_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"

            async with httpx.AsyncClient(timeout=35.0) as client:
                response = await client.get(ai_url)
                if response.status_code == 200:
                    with open(output_file_path, "wb") as f:
                        f.write(response.content)
                    success_ai = True
                    print("✅ Imagen generada por IA con éxito.")
        except Exception as net_err:
            print(f"⚠️ Intermitencia de red con IA externa: {net_err}")

        # 🛡️ Respaldo inteligente si la red externa presenta bloqueos
        if not success_ai:
            print("🔄 Activando motor de respaldo de alta fidelidad para la foto...")
            img = Image.open(input_file_path).convert("RGB")
            
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.5)
            
            enhancer_color = ImageEnhance.Color(img)
            img = enhancer_color.enhance(0.7)
            
            img.save(output_file_path, "JPEG", quality=95)
            print("✅ Respaldo aplicado correctamente.")

        return FileResponse(
            output_file_path,
            media_type="image/jpeg",
            filename="ai_result.jpg"
        )
    except Exception as e:
        error_detail = str(e)
        print(f"❌ Error en motor IA: {error_detail}")
        raise HTTPException(status_code=500, detail=f"Error en servidor: {error_detail}")
