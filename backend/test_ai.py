import google.generativeai as genai

# --- IMPORTANTE: PEGA TU CLAVE REAL AQUÍ ABAJO ---
MY_API_KEY = "AIzaSyC9p7uLogI9UmUdwUnVI9nW9W7FEYE65ms" 

print("--- INICIANDO PRUEBA DE CONEXIÓN IA ---")

try:
    genai.configure(api_key=MY_API_KEY)
    
    print(f"1. Clave configurada: {MY_API_KEY[:5]}... (Oculta por seguridad)")
    print("2. Consultando modelos disponibles a Google...")
    
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"   - Modelo encontrado: {m.name}")
            available_models.append(m.name)

    if not available_models:
        print("❌ ERROR: No se encontraron modelos. Tu API Key podría no tener permisos o ser inválida.")
    else:
        print(f"✅ ÉXITO: Se encontraron {len(available_models)} modelos disponibles.")
        print("   Recomendación: Usa uno de los nombres de arriba en tu archivo main.py")

        # Prueba de generación real
        print("\n3. Intentando generar un 'Hola Mundo' con el primer modelo...")
        model = genai.GenerativeModel(available_models[0].replace('models/', ''))
        response = model.generate_content("Di 'Hola Mundo'")
        print(f"✅ RESPUESTA DE GOOGLE: {response.text}")

except Exception as e:
    print(f"\n❌ ERROR FATAL: {e}")