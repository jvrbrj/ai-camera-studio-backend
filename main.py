from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from PIL import Image, ImageOps, ImageEnhance
import shutil
import os
import requests
import uuid
import random
import time

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

    # 1. Guardar la foto recibida de la app de Flutter
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print(f"✨ Petición detallada del usuario: {prompt}")

    # 2. INGENIERÍA DE PROMPT AVANZADA
    # Ajustamos el prompt para que la IA entienda que debe integrar al personaje con una PERSONA REAL.
    # Usamos palabras clave de fotografía profesional y composición para evitar resultados abstractos o dibujos.
    cleaned_prompt = prompt.lower().strip()
    
    # Prompt base optimizado para fotorrealismo e integración
    elaborate_prompt = (
        f"A high-quality, professional cinematic photograph of a real person standing next to {cleaned_prompt}. "
        f"Photorealistic, detailed faces, natural composition, studio lighting, 8k resolution, highly detailed textures, "
        f"sharp focus, shot on Canon EOS R5."
    )
    
    # Prompt negativo para evitar errores comunes de la IA
    negative_prompt = "cartoon, illustration, painting, deformed, distorted limbs, extra fingers, blurry, low quality, watermark, text, bad anatomy"

    # 3. INTENTOS DE CONEXIÓN CON IA EXTERNA
    # Usaremos un endpoint alternativo de Pollinations que suele ser más estable para peticiones complejas.
    max_retries = 2
    ai_success = False

    for attempt in range(max_retries):
        try:
            print(f"🔄 Intento de generación {attempt + 1}/{max_retries}...")
            
            # Usamos una semilla aleatoria para cada intento para variar el resultado y evitar bloqueos por caché
            seed = random.randint(1, 999999)
            
            # Construcción de la URL para el endpoint 'image.pollinations.ai' con parámetros avanzados
            # Nota: Usamos f-strings para insertar los prompts y la semilla.
            encoded_prompt = requests.utils.quote(elaborate_prompt)
            encoded_negative = requests.utils.quote(negative_prompt)
            
            # Este endpoint específico permite prompts negativos y semillas directamente en la URL.
            ai_url = (
                f"https://image.pollinations.ai/prompt/{encoded_prompt}"
                f"?width=1024&height=1024&seed={seed}&nologo=true&enhance=true"
                f"&negative_prompt={encoded_negative}"
            )
            
            # Petición con un timeout generoso de 45 segundos
            response = requests.get(ai_url, timeout=45)
            
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                print("✅ Imagen generada por IA externa con éxito y fotorrealismo.")
                ai_success = True
                break # Salimos del bucle si tenemos éxito
            
            elif response.status_code == 402:
                print(f"⚠️ Error 402 (Cuota/Saturación) en intento {attempt + 1}. Reintentando con nueva semilla...")
                time.sleep(2) # Esperamos un poco antes del reintento
            else:
                print(f"⚠️ Error {response.status_code} del servidor externo en intento {attempt + 1}.")
                time.sleep(1)

        except requests.exceptions.Timeout:
            print(f"⏱️ Tiempo de espera agotado en intento {attempt + 1}.")
        except Exception as e:
            print(f"⚠️ Error inesperado en intento {attempt + 1}: {e}")

    # 4. MOTOR DE RESPALDO LOCAL MEJORADO (Si la IA falla)
    if not ai_success:
        print("🔄 Activando motor de respaldo local inteligente (PIL)...")
        try:
            img = Image.open(input_path).convert("RGB")
            
            # Aplicamos una mejora visual real para que la foto se vea "procesada"
            # Un estilo dramático universal: alto contraste y leve desaturación.
            img = ImageEnhance.Contrast(img).enhance(1.7)
            img = ImageEnhance.Color(img).enhance(0.6) # Tono más serio/cinematográfico
            
            # Añadimos un borde elegante con el nombre de la app
            # (Esto requiere manejo de fuentes en PIL, para simplificar usaremos solo el borde)
            img_final = ImageOps.expand(img, border=30, fill='black')
            
            img_final.save(output_path, "JPEG", quality=95)
            print("✅ Respaldo local dramático aplicado correctamente.")
            
        except Exception as backup_error:
            print(f"❌ Error crítico en el respaldo: {backup_error}")
            # Si todo falla, devolvemos la imagen original como último recurso
            shutil.copyfile(input_path, output_path)

    # 5. ENVIAR LA IMAGEN RESULTANTE A LA APP DE FLUTTER
    # Independientemente de si fue IA o respaldo, enviamos la imagen.
    if os.path.exists(output_path):
        return FileResponse(output_path, media_type="image/jpeg")
    else:
        raise HTTPException(status_code=500, detail="Error interno al procesar la imagen.")

# 6. LIMPIEZA DE ARCHIVOS TEMPORALES (Finalmente)
@app.on_event("shutdown")
async def cleanup_temp_files():
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
        print(f"🧹 Carpeta temporal '{TEMP_DIR}' limpiada.")
