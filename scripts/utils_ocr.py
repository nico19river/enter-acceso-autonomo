import base64
import io
from PIL import Image
import pytesseract
from pdf2image import convert_from_bytes # Asegúrate de importar poppler_path

# --- RUTAS ESPECÍFICAS A LOS EJECUTABLES DE TESSERACT Y POPPLER EN WINDOWS ---
# Esta es la ruta al ejecutable tesseract.exe.

pytesseract.pytesseract.tesseract_cmd = r'C:\cygwin64\bin\tesseract.exe'

# Esta es la ruta a la carpeta 'bin' donde se encuentran los ejecutables de Poppler (ej. pdftoppm.exe).
# pdf2image los buscará en esta carpeta.
poppler_path = r'C:\cygwin64\bin'
# --------------------------------------------------------------------------

def validar_poliza_automaticamente(poliza_base64):
    """
    Función para validar automáticamente la póliza de seguro buscando palabras clave.
    Retorna True si encuentra las palabras clave, False en caso contrario, y un mensaje.
    Esta función es independiente de la lógica de Flask/DB.
    """
    print("DEBUG (OCR): Iniciando validación automática de póliza.")
    texto_extraido = ""

    if not poliza_base64:
        print("DEBUG (OCR): No hay datos de póliza en Base64 para validar automáticamente.")
        return False, "No se adjuntó póliza para validar."

    try:
        poliza_bytes = base64.b64decode(poliza_base64)
        
        # Intentar procesar como PDF primero
        try:
            # `convert_from_bytes` requiere Poppler instalado en el sistema.
            # `first_page=0, last_page=1` para procesar solo la primera página.
            # `dpi=300` para una mejor calidad de OCR.
            # Se pasa el `poppler_path` para que pdf2image sepa dónde buscar.
            images = convert_from_bytes(poliza_bytes, first_page=0, last_page=1, dpi=300, fmt='jpeg', thread_count=1, poppler_path=poppler_path)
            print("DEBUG (OCR): Póliza detectada como PDF. Extrayendo texto con OCR...")
            for img in images:
                # `lang='spa'` es crucial para el reconocimiento de español.
                texto_extraido += pytesseract.image_to_string(img, lang='spa')
                img.close() # Liberar recursos de la imagen
        except Exception as pdf_error:
            # Si falla como PDF, intentar como imagen
            print(f"DEBUG (OCR): Falló la extracción de PDF ({pdf_error}). Intentando como imagen...")
            img = Image.open(io.BytesIO(poliza_bytes))
            texto_extraido = pytesseract.image_to_string(img, lang='spa')
            img.close() # Liberar recursos de la imagen
            
    except Exception as e:
        print(f"ERROR (OCR): Error al extraer texto con OCR de la póliza: {e}")
        return False, f"Error al procesar la póliza para OCR: {e}"

    print(f"DEBUG (OCR): Texto extraído de la póliza (primeros 500 chars):\n--- INICIO TEXTO PÓLIZA ---\n{texto_extraido[:500]}...\n--- FIN TEXTO PÓLIZA ---")

    # Palabras clave a buscar
    palabras_clave_vigencia = ["vigente", "Vigente", "VIGENTE"]
    encontrado = False
    for palabra in palabras_clave_vigencia:
        if palabra in texto_extraido:
            encontrado = True
            break
    
    if encontrado:
        print("DEBUG (OCR): Palabra clave de vigencia encontrada en la póliza.")
        return True, "Póliza validada automáticamente como VIGENTE."
    else:
        print("DEBUG (OCR): No se encontró palabra clave de vigencia en la póliza.")
        return False, "No se pudo validar la vigencia de la póliza automáticamente (palabra clave no encontrada)."