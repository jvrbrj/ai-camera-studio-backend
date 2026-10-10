import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
import shutil

app = FastAPI(title="AI Camera Studio Backend", version="1.0")

# Directorio temporal para procesar archivos
UPLOAD_DIR = "/tmp/ai_media"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def read_root():
    """Endpoint de verificación para saber si el servidor está activo."""
    return {"status": "online", "message": "AI Camera Studio Backend funcionando correctamente"}

@app.post("/process-media")
async def process_media(
    file: UploadFile = File(...),
    prompt: str = Form(...),
    output_type: str = Form("image")
):
    """
    Recibe la imagen de la cámara o galería, el texto/voz del usuario 
    y el tipo de salida ('image' o 'video').
    """
    try:
        # 1. Guardar la imagen recibida temporalmente
        input_file_path = os.path.join(UPLOAD_DIR, file.filename or "input.jpg")
        with open(input_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print(f"Imagen recibida: {input_file_path}")
        print(f"Prompt de IA recibido: {prompt}")
        print(f"Tipo de salida solicitado: {output_type}")

        # ==========================================
        # 💡 AQUÍ INTEGRARÁS TU MODELO DE IA O STABLE DIFFUSION
        # ==========================================
        # Por ahora, simularemos la respuesta devolviendo la misma imagen 
        # (o puedes generar/procesar el resultado deseado).
        
        output_file_path = input_file_path # Reemplaza esto con la ruta de tu resultado real procesado por IA

        if not os.path.exists(output_file_path):
            raise HTTPException(status_code=500, detail="No se pudo generar el archivo multimedia con IA.")

        # 2. Devolver el archivo procesado (imagen o video) de vuelta a la app
        return FileResponse(
            output_file_path, 
            media_type="video/mp4" if output_type == "video" else "image/jpeg",
            filename="result.mp4" if output_type == "video" else "result.jpg"
        )

    except Exception as e:
        print(f"Error procesando la solicitud: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
