import os
import shutil
import replicate
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
import httpx

app = FastAPI(title="AI Camera Studio Backend", version="2.8")

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
        # 1. Guardar la imagen localmente de forma temporal
        input_filename = file.filename or "input.jpg"
        input_file_path = os.path.join(UPLOAD_DIR, input_filename)
        
        with open(input_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print(f"📸 Imagen recibida: {input_file_path}")
        print(f"✨ Prompt de IA: {prompt}")
        print(f"🎬 Tipo de salida: {output_type}")

        # 2. Subir imagen a un host temporal público para que Replicate la lea
        image_url = await upload_to_temp_host(input_file_path)
        print(f"🌐 URL pública temporal: {image_url}")

        # 3. Ejecutar modelo en Replicate con manejo seguro
        if output_type == "video":
            # Stable Video Diffusion
            output = replicate.run(
                "stability-ai/stable-video-diffusion:3f0457e4619daac512030b4759de3fc3eb5a9bcd34751f2a306f10df54d2d213",
                input={
                    "input_image": image_url,
                    "video_length": "14_frames_with_svd",
                    "fps": 6
                }
            )
            file_ext = "mp4"
        else:
            # SDXL (Img2Img / Text-to-Image con referencia)
            output = replicate.run(
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

        # 4. Descargar el archivo resultante de la IA
        output_file_path = os.path.join(UPLOAD_DIR, f"result.{file_ext}")
        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.get(result_url)
            if res.status_code != 200:
                raise Exception(f"No se pudo descargar el archivo resultante de Replicate (Status: {res.status_code})")
            with open(output_file_path, "wb") as f:
                f.write(res.content)

        # 5. Enviar el archivo procesado de regreso a la app de Flutter
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
    """Sube la imagen a un servicio temporal para generar la URL pública."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        with open(file_path, "rb") as f:
            response = await client.post("https://tmpfiles.org/api/v1/upload", files={"file": f})
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "url" in data["data"]:
                    download_url = data["data"]["url"]
                    # Transformar a enlace de descarga directa
                    direct_url = download_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
                    return direct_url
    raise Exception("Fallo al subir la imagen al host temporal para Replicate.")
