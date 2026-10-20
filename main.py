import os
import shutil
import httpx
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

app = FastAPI(title="AI Camera Studio Free Backend", version="4.0")

# Token gratuito de Hugging Face (puedes crear una cuenta gratis en huggingface.co)
HF_TOKEN = os.getenv("HF_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"

UPLOAD_DIR = "/tmp/ai_media"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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

        print(f"📸 Prompt realista recibido: {prompt}")

        # Petición al modelo gratuito de Stable Diffusion XL en Hugging Face
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        
        # Combinamos el texto del usuario con directrices de fotorrealismo
        full_prompt = f"{prompt}, realistic, highly detailed, cinematic lighting, 8k resolution"

        async with httpx.AsyncClient(timeout=60.0) as client:
            with open(input_file_path, "rb") as img_file:
                response = await client.post(
                    API_URL,
                    headers=headers,
                    files={"image": img_file},
                    data={"inputs": full_prompt}
                )

            if response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Error en IA gratuita: {response.text}")

            output_file_path = os.path.join(UPLOAD_DIR, "result.jpg")
            with open(output_file_path, "wb") as f:
                f.write(response.content)

        return FileResponse(
            output_file_path,
            media_type="image/jpeg",
            filename="ai_result.jpg"
        )

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
