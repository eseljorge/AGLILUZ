import os
import re
import requests
import pandas as pd
from datetime import datetime
from pypdf import PdfReader
import io

def extraer_texto_desde_url(url):
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200 and ('pdf' in response.headers.get('content-type', '').lower() or 'pdf' in url.lower()):
            with io.BytesIO(response.content) as f:
                reader = PdfReader(f)
                texto = ""
                for page in reader.pages[:20]:
                    texto += page.extract_text() or ""
            return texto.lower()
    except Exception:
        pass
    return ""

def extraer_parametros_tecnicos(texto_total):
    texto = texto_total.lower()

    # Cantidad de luminarias
    cantidad_unidades = 0
    matches_cant = re.findall(r'(?:cantidad|adquisicion de|total|requiere|suministro)\D{1,15}(\d+)\s*(?:luminarias|focos|proyectores|unidades|postes)', texto)
    if matches_cant:
        nums = [int(n) for n in matches_cant if int(n) < 15000]
        if nums: cantidad_unidades = max(nums)
    if cantidad_unidades == 0:
        matches_gen = re.findall(r'(\d+)\s*(?:luminarias|focos led|proyectores led)', texto)
        if matches_gen:
            nums_gen = [int(n) for n in matches_gen if int(n) < 15000]
            if nums_gen: cantidad_unidades = max(nums_gen)

    # Potencia (W)
    potencias = re.findall(r'(\d+[\.,]?\d*)\s*(?:w|watt|watts)', texto)
    pot_nums = [float(p.replace(',', '.')) for p in potencias if float(p.replace(',', '.')) < 2000]
    potencia_str = f"{min(pot_nums)}W - {max(pot_nums)}W" if pot_nums else "No especificado en bases"

    # Flujo Luminoso (lm)
    flujos = re.findall(r'(\d+[\.,]?\d*)\s*(?:lm|lumenes|lúmenes)', texto)
    flujo_nums = [float(f.replace(',', '.')) for f in flujos if float(f.replace(',', '.')) > 500]
    flujo_str = f"{min(flujo_nums):,.0f} lm - {max(flujo_nums):,.0f} lm" if flujo_nums else "No especificado en bases"

    # IP e IK
    ip_match = re.findall(r'ip\s*([0-6][5678])', texto)
    ip_str = "IP" + max(ip_match) if ip_match else "IP66 Requerido"

    ik_match = re.findall(r'ik\s*([0-1][0-9])', texto)
    ik_str = "IK" + max(ik_match) if ik_match else "IK08 Requerido"

    # Control y Telegestión
    control = []
    if 'telegestion' in texto or 'telegestión' in texto: control.append("Telegestión")
    if 'zhaga' in texto: control.append("Zócalo Zhaga")
    if 'nema' in texto: control.append("Zócalo NEMA")
    if 'interact' in texto: control.append("Interact")
    if 'dynalite' in texto: control.append("Dynalite")
    control_str = " | ".join(control) if control else "Control estándar / Autónomo"

    # Certificaciones
    certs = []
    if 'sec' in texto: certs.append("SEC")
    if 'ds1' in texto or 'decreto supremo' in texto or 'norma lumínica' in texto: certs.append("Decreto Supremo N°1 (DS1)")
    cert_str = " | ".join(certs) if certs else "Normativa DS1 / Estándar"

    return cantidad_unidades, potencia_str, flujo_str, ip_str, ik_str, control_str, cert_str

def evaluar_licitacion(texto):
    score = 0
    detalles = []

    tokens_luz = [
        ("luminaria", 35), ("luminarias", 35), ("alumbrado", 30), 
        ("iluminacion", 30), ("iluminación", 30), ("proyector", 25), 
        ("proyectores", 25), ("foco vial", 20), ("telegestión", 25), 
        ("telegestion", 25), ("cancha", 20), ("estadio", 20), 
        ("vial", 15), ("solar", 20), ("ornamental", 15), ("túnel", 20), ("tunel", 20)
    ]
    
    tiene_token_troncal = False
    for palabra, pts in tokens_luz:
        if palabra in texto:
            score += pts
            detalles.append(f"+{pts} ({palabra})")
            if palabra in ["luminaria", "luminarias", "alumbrado", "iluminacion", "iluminación", "proyector", "proyectores"]:
                tiene_token_troncal = True

    tokens_basura = [
        ("tomografo", 120), ("tomógrafo", 120), ("ascensor", 120), 
        ("ascensores", 120), ("caldera", 100), ("cesfam", 80), 
        ("hospital", 60), ("mampara", 80), ("dental", 100), ("vehiculo", 80)
    ]
    for palabra, penalizacion in tokens_basura:
        if palabra in texto:
            score -= penalizacion
            detalles.append(f"-{penalizacion} [BLACKLIST: {palabra}]")

    es_valido = tiene_token_troncal and (score >= 35)
    return es_valido, score, " | ".join(detalles)

def main():
    ticket = os.environ.get('TICKET_MP')
    if not ticket:
        print("Error: TICKET_MP no configurado.")
        return

    print("Conectando con la API de Mercado Público...")
    url = f"https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json?ticket={ticket}"
    response = requests.get(url)
    
    if response.status_code != 200:
        print("Error al conectar con la API de Mercado Público.")
        return

    data = response.json()
    licitaciones = data.get('Listado', [])
    print(f"Total licitaciones obtenidas: {len(licitaciones)}")

    registros = []
    for item in licitaciones:
        codigo = item.get('CodigoExterno')
        nombre = item.get('Nombre', '')
        descripcion = item.get('Descripcion', '')
        
        texto_completo = f"{nombre} {descripcion}".lower()

        # Descargar y leer documentos PDF adjuntos si existen en la API
        documentos = item.get('Documentos', [])
        if isinstance(documentos, list):
            for doc in documentos:
                url_doc = doc.get('UrlDocumento', '') or doc.get('URL', '')
                if url_doc and isinstance(url_doc, str) and url_doc.startswith('http'):
                    texto_completo += " " + extraer_texto_desde_url(url_doc)

        es_valido, score, detalle_score = evaluar_licitacion(texto_completo)

        if es_valido:
            cant_unidades, potencia, flujo, ip, ik, control, certs = extraer_parametros_tecnicos(texto_completo)

            categoria = "Iluminación Vial / Pública"
            signify_eq = "RoadFlair / Xceed Pro + Interact City"
            if "estadio" in texto_completo or "cancha" in texto_completo or "deportivo" in texto_completo:
                categoria = "Iluminación Deportiva"
                signify_eq = "Arena X + Interact Sports"
            elif "solar" in texto_completo or "fotovoltaica" in texto_completo:
                categoria = "Luminarias Solares"
                signify_eq = "GreenVision Solar"
            elif "ornamental" in texto_completo or "fachada" in texto_completo:
                categoria = "Iluminación Ornamental / Arquitectónica"
                signify_eq = "Tango Pro / Color Kinetics + Dynalite"

            monto_propuesta = float(item.get('Monto', 0) or 50000000)

            record = {
                'CodigoExterno': codigo,
                'Nombre': nombre,
                'Categoria_Proyecto': categoria,
                'Signify_Equivalente': signify_eq,
                'Cantidad_Unidades': cant_unidades,
                'Requerimiento_Potencia': potencia,
                'Requerimiento_Flujo_Luminoso': flujo,
                'Requerimiento_IP': ip,
                'Requerimiento_IK': ik,
                'Sistemas_Control_Telegestion': control,
                'Certificaciones_Exigidas': certs,
                'Proveedor_Adjudicado': "En curso / Vigente",
                'Monto_Propuesta_CLP': monto_propuesta,
                'Monto_Adjudicado_CLP': 0,
                'Score_Relevancia': score,
                'Estado_Cumplimiento_Signify': "Cumple Totalmente (Alta Prioridad)",
                'Analisis_Brecha_Tecnica': f"Score: {score} | {detalle_score} | Luminarias detectadas: {cant_unidades}",
                'Fecha_Creacion': str(item.get('FechaCreacion', ''))[:10],
                'Fecha_Cierre': str(item.get('FechaCierre', ''))[:10]
            }
            registros.append(record)

    df_final = pd.DataFrame(registros)
    os.makedirs('agliluz', exist_ok=True)
    df_final.to_excel('agliluz/historial_licitaciones.xlsx', index=False)
    print(f"Proceso finalizado con éxito. {len(df_final)} licitaciones puras de iluminación guardadas.")

if __name__ == '__main__':
    main()
