import os
import shutil
import replicate
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
import httpx

app = FastAPI(title="AI Camera Studio Backend", version="3.2")

# 🔑 REEMPLAZA "r8_AQUI_VA_TU_TOKEN_REAL_DE_REPLICATE" con tu token real de Replicate
REPLICATE_API_TOKEN = "r8_tu_token_real_de_replicate_aqui..."

UPLOAD_DIR = "/tmp/ai_media"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def read_root():
    return {"status": "online", "message": "AI Camera Studio Backend con Replicate activo"}

@app.post("/process-media")
async def process_media(
    file: UploadFile = File(...),
    prompt: str = Form(...),
    output_type: str = Form("image")
):
    try:
        input_filename = file.filename or "input.jpg"
        input_file_path = os.path.join(UPLOAD_DIR, input_filename)
        
        with open(input_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print(f"📸 Imagen recibida: {input_file_path}")
        print(f"✨ Prompt de IA: {prompt}")
        print(f"🎬 Tipo de salida: {output_type}")

        # Subir imagen a host temporal para que Replicate pueda leerla
        image_url = await upload_to_temp_host(input_file_path)
        print(f"🌐 URL pública temporal: {image_url}")

        # 🛡️ Crear cliente explícito con tu token real para evitar errores 401
        client = replicate.Client(api_token=REPLICATE_API_TOKEN)

        # Ejecutar modelo en Replicate usando el cliente explícito
        if output_type == "video":
            output = client.run(
                "stability-ai/stable-video-diffusion:3f0457e4619daac512030b4759de3fc3eb5a9bcd34751f2a306f10df54d2d213",
                input={
                    "input_image": image_url,
                    "video_length": "14_frames_with_svd",
                    "fps": 6
                }
            )
            file_ext = "mp4"
        else:
            output = client.run(
                "stability-ai/sdxl:39ed62f2a79043531b1a0fe3b88c9fef9ba157648c49d43f2ff15f00c702ef8d",
                input={
                    "image": image_url,
                    "prompt": prompt,
                    "negative_prompt": "blurry, low quality, distorted",
                    "image_strength": 0.45,
                    "num_outputs": 1
                }
            )
            file_ext = "jpg"

        # Extraer la URL del resultado de forma segura
        if isinstance(output, list) and len(output) > 0:
            result_url = str(output[0])
        else:
            result_url = str(output)

        print(f"🎨 Resultado obtenido de Replicate: {result_url}")

        # Descargar el archivo procesado resultante
        output_file_path = os.path.join(UPLOAD_DIR, f"result.{file_ext}")
        async with httpx.AsyncClient(timeout=60.0) as client_http:
            res = await client_http.get(result_url)
            if res.status_code != 200:
                raise Exception(f"No se pudo descargar el archivo resultante (Status: {res.status_code})")
            with open(output_file_path, "wb") as f:
                f.write(res.content)

        # Retornar el archivo procesado a la aplicación en Flutter
        return FileResponse(
            output_file_path,
            media_type="video/mp4" if output_type == "video" else "image/jpeg",
            filename=f"ai_result.{file_ext}"
        )

    except Exception as e:
        error_detail = str(e)
        print(f"❌ Error interno crítico: {error_detail}")
        raise HTTPException(status_code=500, detail=f"Error en servidor: {error_detail}")

async def upload_to_temp_host(file_path: str) -> str:
    """Sube la imagen a un servicio temporal para generar la URL pública accesible por Replicate."""
    async with httpx.AsyncClient(timeout=30.0) as client_http:
        with open(file_path, "rb") as f:
            response = await client_http.post("https://tmpfiles.org/api/v1/upload", files={"file": f})
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "url" in data["data"]:
                    download_url = data["data"]["url"]
                    direct_url = download_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
                    return direct_url
    raise Exception("Fallo al subir la imagen al host temporal.")
