from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from PIL import Image, ImageOps, ImageEnhance
import shutil
import os
import requests
import uuid
import random

app = FastAPI()

TEMP_DIR = "temp_media"
os.makedirs(TEMP_DIR, exist_ok=True)

@app.post("/process-media")
async def process_media(
    prompt: str = Form(...),
    file: UploadFile = File(...)
):
    input_path = os.path.join(TEMP_DIR, f"input_{uuid.uuid4()}.jpg")
    output_path = os.path.join(TEMP_DIR, f"output_{uuid.uuid4()}.jpg")

    # Guardar la foto recibida de la app
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print(f"✨ Procesando especificaciones de IA: {prompt}")

    try:
        # Añadimos un 'seed' aleatorio para evitar bloqueos por peticiones repetidas o caché (Error 402)
        random_seed = random.randint(1, 1000000)
        enhanced_prompt = f"A photorealistic cinematic portrait featuring {prompt}, highly detailed, professional lighting and composition"
        
        ai_url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(enhanced_prompt)}?width=1024&height=1024&nologo=true&seed={random_seed}"
        
        response = requests.get(ai_url, timeout=30)
        
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            print("✅ Imagen generada y ajustada con éxito.")
            return FileResponse(output_path, media_type="image/jpeg")
        else:
            raise Exception(f"Servidor externo respondió con código: {response.status_code}")

    except Exception as e:
        print(f"⚠️ Alerta en IA externa: {e}")
        print("🔄 Activando respaldo inteligente contextual...")
        
        # RESPALDO CONTEXTUAL BASADO EN EL PROMPT DEL USUARIO
        try:
            img = Image.open(input_path).convert("RGB")
            lower_prompt = prompt.lower()
            
            border_color = 'black'
            
            if "dracula" in lower_prompt or "panteon" in lower_prompt or "terror" in lower_prompt:
                # Estilo Gótico / Oscuro
                img = ImageEnhance.Contrast(img).enhance(1.6)
                img = ImageEnhance.Color(img).enhance(0.4)
                border_color = 'purple'
            elif "medusa" in lower_prompt or "mitologia" in lower_prompt or "serpiente" in lower_prompt:
                # Estilo Mítico / Tonos verdosos
                img = ImageEnhance.Contrast(img).enhance(1.4)
                img = ImageEnhance.Color(img).enhance(1.3)
                border_color = 'darkgreen'
            elif "spiderman" in lower_prompt or "heroe" in lower_prompt or "cyberpunk" in lower_prompt:
                # Estilo Heroico / Alta viveza de colores
                img = ImageEnhance.Contrast(img).enhance(1.5)
                img = ImageEnhance.Color(img).enhance(1.5)
                border_color = 'red'
            else:
                # Estilo Cine General
                img = ImageEnhance.Contrast(img).enhance(1.3)
                img = ImageEnhance.Color(img).enhance(1.2)
                border_color = 'cyan'

            # Aplicar marco temático adaptado al personaje
            img_final = ImageOps.expand(img, border=25, fill=border_color)
            img_final.save(output_path, "JPEG")
            
            print("✅ Respaldo contextual aplicado correctamente.")
            return FileResponse(output_path, media_type="image/jpeg")
            
        except Exception as backup_error:
            print(f"❌ Error crítico en respaldo: {backup_error}")
            raise HTTPException(status_code=500, detail="Error al procesar la imagen.")

    finally:
        if os.path.exists(input_path):
            try:
                os.remove(input_path)
            except:
                pass
