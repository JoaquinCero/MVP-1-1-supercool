# backend/main.py

from fastapi import FastAPI
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import json
from typing import Dict, Any, List
import os
import google.generativeai as genai
import math

app = FastAPI()

# --- CONFIGURACIÓN DE IA ---
# ¡Asegúrate de que esta sea tu clave real!
GEMINI_API_KEY = "AIzaSyC9p7uLogI9UmUdwUnVI9nW9W7FEYE65ms" 

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash') 

class AnalysisRequest(BaseModel):
    target_url: str

# --- UTILIDADES ---

def ensure_url_scheme(url: str):
    if not url.startswith('http'):
        return f"https://{url}"
    return url

def clean_domain_name(url: str):
    """Extrae el nombre limpio del dominio."""
    return url.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]

def get_paa_opportunities(score_details: Dict[str, Any]) -> List[str]:
    """Convierte los detalles del score PAA en sugerencias de mejora."""
    opportunities = []

    if score_details['v1_score'] < 1.0:
        opportunities.append("Implementar Schema.org (datos estructurados) para el contexto clave.")
    if score_details['h1_count'] != 1:
        if score_details['h1_count'] == 0:
            opportunities.append("Añadir una etiqueta <h1> para definir el tema central.")
        else:
            opportunities.append(f"Reducir etiquetas <h1> a una sola ({score_details['h1_count']} detectadas).")
    if score_details['v3_score'] < 1.0:
        opportunities.append(f"Aumentar el contenido de texto útil. Tu densidad es baja ({int(score_details['density_ratio']*100)}%).")
    if score_details['v4_score'] < 1.0:
        opportunities.append("Asegurar que <title> y <meta description> sean únicas y descriptivas.")
            
    return opportunities

# --- 1. MOTOR DE ANÁLISIS PAA ---

def calculate_paa_score(url: str) -> Dict[str, Any]:
    """Analiza una URL y devuelve puntaje PAA con detalles de métricas."""
    url = ensure_url_scheme(url)
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; AEOBot/1.0)'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return {"puntuacion": 0, "error": True, "msg": f"Status {response.status_code}"}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        raw_text = soup.get_text(separator=' ', strip=True)[:1500]

    except Exception as e:
        return {"puntuacion": 0, "error": True, "msg": "Error de acceso"}

    # --- CÁLCULO DE MÉTRICAS Y SCORES ---
    schema_present = len(soup.find_all('script', {'type': 'application/ld+json'})) > 0
    s_v1 = 1.0 if schema_present else 0.0
    h1_count = len(soup.find_all('h1'))
    s_v2 = 1.0 if h1_count == 1 else (0.5 if h1_count > 1 else 0.2)
    
    body_text = soup.body.get_text(separator=' ', strip=True) if soup.body else ""
    content_len = len(response.content)
    density_ratio = len(body_text) / content_len if content_len > 0 else 0
    s_v3 = min(1.0, density_ratio / 0.15) 
    
    title_tag = soup.title.string if soup.title else ""
    s_v4 = 1.0 if title_tag and len(title_tag) > 10 else 0.5
    
    score = int(((s_v1 * 0.3) + (s_v2 * 0.2) + (s_v3 * 0.3) + (s_v4 * 0.2)) * 100)

    reasons = []
    if not schema_present: reasons.append("Sin Schema")
    if h1_count != 1: reasons.append(f"{h1_count} H1s")
    if s_v3 < 0.5: reasons.append("Poco texto")
    reason_str = ", ".join(reasons) if reasons else "Óptima"
    
    score_details = {
        'v1_score': s_v1, 'v2_score': s_v2, 'v3_score': s_v3, 'v4_score': s_v4,
        'h1_count': h1_count, 'density_ratio': density_ratio
    }

    return {
        "puntuacion": score,
        "reasons": reason_str,
        "raw_text": raw_text,
        "score_details": score_details,
        "oportunidades": get_paa_opportunities(score_details),
        "error": False
    }

# --- 2. INTELIGENCIA DE MERCADO (Gemini) ---

def get_competitors_from_ai(text_content: str, url: str):
    """Pide 5 rivales a la IA con descripción y país."""
    prompt = f"""
    Analiza este texto del sitio {url}: "{text_content}..."
    
    Tarea:
    1. Detecta la INDUSTRIA.
    2. Identifica 5 COMPETIDORES DIRECTOS y REALES que vendan productos o servicios similares.
    3. Para cada uno, provee una descripción de lo que hacen y su país de origen/operación principal.
    
    Responde SOLO JSON válido:
    {{
        "industria": "...",
        "competidores": [
            {{"url": "www.rival1.com", "descripcion": "Descripción del negocio.", "pais": "Chile"}},
            // ... (4 más)
        ]
    }}
    """
    try:
        response = model.generate_content(prompt)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception as e:
        print(f"Error IA en Mercado: {e}")
        return {"industria": "Error de IA", "competidores": []}

# --- 3. ENDPOINT PRINCIPAL ---

@app.post("/analyze")
async def analyze_endpoint(req: AnalysisRequest):
    # 1. Analizar al Cliente
    client_data = calculate_paa_score(req.target_url)
    if client_data["error"]:
        return {"puntuacion": 0, "diagnostico": "Error al acceder a tu URL", "error": True}

    # 2. Obtener Rivales
    ai_data = get_competitors_from_ai(client_data["raw_text"], req.target_url)
    competitors_list = ai_data.get("competidores", [])[:5] 
    
    # 3. Lista Maestra para el Ranking (incluye al cliente)
    ranking_list = [{
        "posicion": 0,
        "empresa": "TU EMPRESA",
        "url": clean_domain_name(req.target_url),
        "score": client_data["puntuacion"],
        "detalles": client_data["reasons"],
        "es_usuario": True,
        "oportunidades": client_data["oportunidades"],
        "descripcion_mercado": f"Tu Empresa ({ai_data.get('industria', 'N/A')})",
        "pais": "N/A" # No se lo pedimos a la IA
    }]
    
    # 4. Analizar a los 5 Rivales y añadir detalles
    for rival_data in competitors_list:
        comp_url = rival_data.get("url", "")
        
        if not comp_url or clean_domain_name(req.target_url) in comp_url:
            continue
            
        comp_result = calculate_paa_score(comp_url)
        
        if not comp_result["error"]:
            ranking_list.append({
                "posicion": 0,
                "empresa": clean_domain_name(comp_url),
                "url": comp_url,
                "score": comp_result["puntuacion"],
                "detalles": comp_result["reasons"],
                "es_usuario": False,
                "descripcion_mercado": rival_data.get("descripcion", "N/A"), # NUEVO
                "pais": rival_data.get("pais", "Global") # NUEVO
            })

    # 5. Ordenar el Ranking y Asignar Posición
    ranking_list.sort(key=lambda x: x['score'], reverse=True)
    user_rank = 0
    for index, item in enumerate(ranking_list):
        item['posicion'] = index + 1
        if item['es_usuario']:
            user_rank = item['posicion']

    # 6. Generar Mensaje de Diagnóstico Detallado (Lógica compleja)
    client_score = client_data["puntuacion"]
    total_sites = len(ranking_list)
    strongest_rival = ranking_list[0]
    
    # ... (Lógica de diagnóstico similar a la anterior, pero ahora con los nuevos detalles) ...
    
    if user_rank == 1 and client_score >= 70:
        ranking_category = "🏆 ¡LÍDER ABSOLUTO!"
    elif client_score >= 50:
        ranking_category = "¡Estás en la Lucha! Pero hay espacio para mejorar."
    else:
        ranking_category = "🚨 ¡Estas quedando atras! Es URGENTE que tomes acción!"

    comparative_msg = f"Tu PAA es **{client_score}/100** (Posición #{user_rank} de {total_sites} sitios analizados)."
    
    # Detalle Competitivo
    if strongest_rival and strongest_rival['empresa'] != "TU EMPRESA":
        rival_name = strongest_rival['empresa']
        rival_score = strongest_rival['score']
        comparative_msg += f"\n\n**ANÁLISIS DE RIVALES:** El líder es **{rival_name}** ({strongest_rival['pais']}) con {rival_score} PAA. "
        comparative_msg += f"Su fortaleza reside en: **{strongest_rival['detalles']}**. "
        
        if rival_score > client_score:
            comparative_msg += f"Debes mejorar tu rendimiento en **Schema** y **Densidad** para superarle."
        else:
            comparative_msg += "¡Tu estrategia de contenido está dominando a tus rivales más fuertes!"

    # 7. Construir Respuesta Final
    return {
        "puntuacion": client_score,
        "diagnostico": f"{ranking_category} | {comparative_msg}",
        "industria": ai_data.get("industria"),
        "ranking_completo": ranking_list # Esta lista ahora incluye país y descripción
    }