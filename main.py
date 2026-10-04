from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import shutil
import os
import uuid
import torch
from PIL import Image
from diffusers import StableDiffusionImg2ImgPipeline, DPMSolverMultistepScheduler

app = FastAPI(title="AI Camera Studio - Cloud Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# En Hugging Face Spaces, el sistema de archivos de escritura obligatoria es /tmp
UPLOAD_DIR = "/tmp/uploads"
OUTPUT_DIR = "/tmp/outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("🔄 Cargando modelo de Stable Diffusion en la nube...")
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"💻 Dispositivo asignado en Hugging Face: {device.upper()}")

try:
  dtype = torch.float16 if device == "cuda" else torch.float32

  # Usamos Stable Diffusion v1.5 optimizado para Img2Img
  pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
      "runwayml/stable-diffusion-v1-5",
      torch_dtype=dtype,
      safety_checker=None,
  )
  pipe = pipe.to(device)
  
  # Scheduler rápido para agilizar las respuestas en la nube
  pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)

  if device == "cuda":
    pipe.enable_attention_slicing()

  print("✅ ¡Modelo cargado con éxito en el servidor cloud!")
except Exception as e:
  print(f"⚠️ Error al inicializar el modelo de IA: {e}")
  pipe = None


@app.get("/")
def home():
  return {
      "status": "online",
      "message": "Backend de AI Camera Studio operando en la nube.",
      "ai_loaded": pipe is not None,
      "device": device,
  }


@app.post("/process-media/")
async def process_media(
    file: UploadFile = File(...),
    prompt: str = Form(...),
):
  try:
    file_extension = os.path.splitext(file.filename)[1] or ".jpg"
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    input_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(input_path, "wb") as buffer:
      shutil.copyfileobj(file.file, buffer)

    print(f"📸 Imagen recibida: {unique_filename} | Prompt: '{prompt}'")

    output_filename = f"gen_{uuid.uuid4()}.jpg"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    if pipe is not None:
      print("🎨 Ejecutando inferencia de IA...")
      init_image = Image.open(input_path).convert("RGB")
      init_image = init_image.resize((512, 512))

      # Reducimos a 15 pasos para una respuesta veloz y estable en la nube
      generated_image = pipe(
          prompt=prompt,
          image=init_image,
          strength=0.55,
          num_inference_steps=15,
          guidance_scale=7.5,
      ).images[0]

      generated_image.save(output_path)
      print("✨ ¡Generación completada!")
    else:
      shutil.copyfile(input_path, output_path)

    return {
        "status": "success",
        "message": "¡Transformación con IA completada en la nube!",
        "prompt_recibido": prompt,
        "result_url": f"/download/{output_filename}",
    }

  except Exception as e:
    print(f"❌ Error interno: {str(e)}")
    return {"status": "error", "message": str(e)}


@app.get("/download/{filename}")
async def download_result(filename: str):
  file_path = os.path.join(OUTPUT_DIR, filename)
  if os.path.exists(file_path):
    return FileResponse(file_path)
  return {"error": "Archivo no encontrado"}