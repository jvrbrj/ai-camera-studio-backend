import os
import shutil
import replicate
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
import httpx

app = FastAPI(title="AI Camera Studio Backend", version="2.5")

# Directorio temporal para almacenar la foto capturada por el Moto G15
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

        # 2. Subir temporalmente la imagen a un servicio temporal para que Replicate pueda leerla por URL
        image_url = await upload_to_temp_host(input_file_path)

        # 3. Ejecutar el modelo en Replicate según lo que pida el usuario
        if output_type == "video":
            output = replicate.run(
                "stability-ai/stable-video-diffusion:3f0457e4619daac512030b4759de3fc3eb5a9bcd34751f2a306f10df54d2d213",
                input={
                    "input_image": image_url,
                    "video_length": "14_frames_with_svd",
                    "fps": 6
                }
            )
            result_url = output[0] if isinstance(output, list) else output
            file_ext = "mp4"
        else:
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
            result_url = output[0] if isinstance(output, list) else output
            file_ext = "jpg"

        # 4. Descargar el resultado procesado devuelto por Replicate
        output_file_path = os.path.join(UPLOAD_DIR, f"result.{file_ext}")
        async with httpx.AsyncClient() as client:
            res = await client.get(result_url)
            with open(output_file_path, "wb") as f:
                f.write(res.content)

        # 5. Enviar el archivo final de regreso a la aplicación en Flutter
        return FileResponse(
            output_file_path,
            media_type="video/mp4" if output_type == "video" else "image/jpeg",
            filename=f"ai_result.{file_ext}"
        )

    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error detallado en el backend: {error_msg}")
        # Esto le enviará el error real a tu Flutter para que lo veas en el SnackBar
        raise HTTPException(status_code=500, detail=f"Error interno: {error_msg}")

async def upload_to_temp_host(file_path: str) -> str:
    """Sube la imagen a un servicio temporal gratuito para que Replicate pueda leerla por URL."""
    async with httpx.AsyncClient() as client:
        with open(file_path, "rb") as f:
            response = await client.post("https://tmpfiles.org/api/v1/upload", files={"file": f})
            if response.status_code == 200:
                data = response.json()
                download_url = data["data"]["url"]
                direct_url = download_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
                return direct_url
    raise Exception("No se pudo preparar la imagen para la IA.")
