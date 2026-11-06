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
) -> FileResponse:
    input_path = os.path.join(TEMP_DIR, f"input_{uuid.uuid4()}.jpg")
    output_path = os.path.join(TEMP_DIR, f"output_{uuid.uuid4()}.jpg")
    bg_temp = os.path.join(TEMP_DIR, f"bg_{uuid.uuid4()}.jpg")

    # 1. Guardar la foto real tomada desde tu Moto G55 5G
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print(f"✨ Creando escena compuesta para: {prompt}")

    try:
        # 2. Generar el fondo temático con la IA (enfocándonos en el escenario y el personaje)
        bg_prompt = f"A cinematic background of {prompt}, highly detailed, dramatic lighting, 8k resolution, empty scene"
        seed = random.randint(1, 999999)
        ai_url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(bg_prompt)}?width=1024&height=1024&seed={seed}&nologo=true"
        
        response = requests.get(ai_url, timeout=35)
        
        if response.status_code == 200:
            with open(bg_temp, "wb") as f:
                f.write(response.content)
            
            # 3. FUSIÓN INTELIGENTE: Unir tu foto real con el fondo de la IA
            bg_img = Image.open(bg_temp).convert("RGB")
            user_img = Image.open(input_path).convert("RGB")
            
            # Redimensionar tu foto para que encaje perfectamente como elemento principal integrado
            user_img.thumbnail((450, 450))
            
            # Añadir un marco elegante estilo "fotografía impresa" a tu foto
            user_framed = ImageOps.expand(user_img, border=12, fill='white')
            
            # Calcular posición (esquina inferior derecha del fondo generado)
            position = (bg_img.width - user_framed.width - 50, bg_img.height - user_framed.height - 50)
            
            # Pegar tu foto sobre la escena creada por la IA
            bg_img.paste(user_framed, position)
            bg_img.save(output_path, "JPEG", quality=95)
            
            print("✅ ¡Fusión completada! Tu foto y la IA unidas con éxito.")
            return FileResponse(output_path, media_type="image/jpeg")
            
        else:
            raise Exception("El servidor de IA no respondió al fondo.")

    except Exception as e:
        print(f"⚠️ Aviso: {e}. Aplicando respaldo fotográfico local...")
        
        # Respaldo de emergencia si falla la red externa
        try:
            img = Image.open(input_path).convert("RGB")
            img_final = ImageOps.expand(img, border=30, fill='deepskyblue')
            img_final.save(output_path, "JPEG")
            return FileResponse(output_path, media_type="image/jpeg")
        except Exception as backup_error:
            raise HTTPException(status_code=500, detail=str(backup_error))

    finally:
        # Limpieza de archivos temporales internos
        for path in [input_path, bg_temp]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
