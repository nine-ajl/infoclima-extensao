import os
import requests
from datetime import datetime
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe  # Usado para colocar borda preta nos textos
import contextily as cx
from shapely.geometry import Point, MultiPoint

load_dotenv()

NASA_MAP_KEY = os.getenv("NASA_MAP_KEY")
WA_INSTANCE_ID = os.getenv("WA_INSTANCE_ID")
WA_API_TOKEN = os.getenv("WA_API_TOKEN")
WA_GROUP_ID = os.getenv("WA_GROUP_ID")

# BBOX original focado na sua região
BBOX = os.getenv("BBOX", "-59.35,-3.25,-58.95,-2.85")

def obter_focos_recentes():
    """Consulta múltiplas fontes da NASA nas últimas 48h"""
    fontes_satelite = ['VIIRS_SNPP_NRT', 'VIIRS_NOAA20_NRT', 'MODIS_NRT']
    dias_busca = 2 
    focos_coords = []
    
    for fonte in fontes_satelite:
        url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{NASA_MAP_KEY}/{fonte}/{BBOX}/{dias_busca}"
        try:
            response = requests.get(url, timeout=12)
            if response.status_code == 200:
                linhas = response.text.strip().split('\n')
                if len(linhas) > 1:
                    for linha in linhas[1:]:
                        partes = linha.split(',')
                        if len(partes) >= 2:
                            try:
                                lat = float(partes[0])
                                lon = float(partes[1])
                                focos_coords.append((lat, lon))
                            except ValueError:
                                continue
        except Exception as e:
            print(f"Erro ao consultar {fonte}: {e}")
            
    focos_unicos = list(set(focos_coords))
    return focos_unicos, len(focos_unicos)

def gerar_mapa_satelite_alta_res(focos_coords):
    """Gera o mapa de satélite focado na ameaça mais próxima da comunidade"""
    caminho_arquivo = "mapa_queimadas.png"
    
    try:
        w, s, e, n = [float(x) for x in BBOX.split(',')]
    except Exception:
        w, s, e, n = -59.35, -3.25, -58.95, -2.85

    fig, ax = plt.subplots(figsize=(10, 8), dpi=180)

    # 1. Desenha manchas de perigo INDIVIDUAIS para cada foco
    if focos_coords:
        for lat, lon in focos_coords:
            pt_buffer = Point(lon, lat).buffer(0.015) # Raio de perigo de aprox. 1.5km
            x_b, y_b = pt_buffer.exterior.xy
            ax.fill(x_b, y_b, color='#FF0000', alpha=0.35, zorder=3)
            ax.plot(x_b, y_b, color='#FF3300', linestyle='--', linewidth=1.5, alpha=0.9, zorder=4)

        # 2. Algoritmo de "Ameaça Mais Próxima"
        # Calcula qual foco está mais perto das coordenadas de Novo Remanso
        lat_comunidade, lon_comunidade = -3.1415, -58.8210
        foco_mais_proximo = min(focos_coords, key=lambda p: (p[0] - lat_comunidade)**2 + (p[1] - lon_comunidade)**2)
        centro_y, centro_x = foco_mais_proximo[0], foco_mais_proximo[1]

        lats = [p[0] for p in focos_coords]
        lons = [p[1] for p in focos_coords]
        
        # Plota os pontos exatos do satélite
        ax.scatter(lons, lats, c='#FFCC00', s=60, zorder=6, edgecolors='#FF0000', linewidths=1.2)
        
        # Aponta o alerta exclusivamente para o foco mais próximo
        ax.annotate('⚠️ FOCO MAIS PRÓXIMO', 
                    xy=(centro_x, centro_y), xytext=(20, 20), textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='#111827', edgecolor='#FF0000', alpha=0.85),
                    fontsize=8, fontweight='bold', color='#FFFFFF', zorder=7,
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.1', color='#FF0000', lw=1.5))
    else:
        centro_x, centro_y = (w + e) / 2, (s + n) / 2

    # 3. Pontos de Referência Locais
    referencias_locais = {
        "Novo Remanso": (-3.1415, -58.8210),
        "Nova Brasília": (-3.18, -58.70),
        "Itacoatiara": (-3.1333, -58.4442),
        "Rio Amazonas": (-3.05, -58.90)
    }

    for nome, (lat, lon) in referencias_locais.items():
        if s <= lat <= n and w <= lon <= e:
            if "Rio" not in nome:
                ax.plot(lon, lat, marker='o', color='cyan', markersize=6, zorder=8, markeredgecolor='black')
            
            texto = ax.text(lon, lat + 0.005, nome, color='white', fontsize=10, 
                            fontweight='bold', ha='center', va='bottom', zorder=9)
            texto.set_path_effects([pe.withStroke(linewidth=3, foreground='black')])

    ax.set_xlim(w, e)
    ax.set_ylim(s, n)

    # 4. Fundo de Satélite Real
    try:
        cx.add_basemap(ax, crs='EPSG:4326', source=cx.providers.Esri.WorldImagery, alpha=1.0, zorder=1) # type: ignore
    except Exception as err:
        print(f"Erro no basemap: {err}")

    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    plt.tight_layout()
    plt.savefig(caminho_arquivo, dpi=180, bbox_inches='tight')
    plt.close()
    
    # Gera o link do GPS apontando para a ameaça mais próxima
    link_google_maps = f"https://www.google.com/maps/search/?api=1&query={centro_y},{centro_x}"
    
    return caminho_arquivo, link_google_maps

def enviar_alerta_whatsapp(caminho_imagem, texto_alerta):
    if caminho_imagem and os.path.exists(caminho_imagem):
        url = f"https://api.green-api.com/waInstance{WA_INSTANCE_ID}/sendFileByUpload/{WA_API_TOKEN}"
        payload = {'chatId': WA_GROUP_ID, 'caption': texto_alerta}
        files = [('file', ('mapa_queimadas.png', open(caminho_imagem, 'rb'), 'image/png'))]
        requests.post(url, data=payload, files=files)

def main():
    focos_coords, total_focos = obter_focos_recentes()
    data_hora = datetime.now().strftime("%d/%m/%Y às %H:%M")

    # Força a geração para visualizar no VS Code, mesmo sem focos novos
    # Em produção (GitHub), você pode colocar "if total_focos > 0:"
    imagem, link_maps = gerar_mapa_satelite_alta_res(focos_coords)
    
    alerta_texto = f"""🚨 *ALERTA URGENTE: FOCO DE INCÊNDIO* 🚨
⏰ *Atualização:* {data_hora}

🔥 *Detecção (NASA):*
• *{total_focos} focos* identificados nas últimas 48h.
• Veja os pontos amarelos/vermelhos na foto de satélite.

📍 *Distância até sua casa:*
Toque no link abaixo para abrir o *Google Maps* e ver exatamente onde está o fogo:
👉 {link_maps}

⚠️ *Recomendações:*
• Mantenha-se afastado e evite inalar fumaça.
_Sistema de Alerta Comunitário - Projeto de Extensão_"""

    enviar_alerta_whatsapp(imagem, alerta_texto)
    print("Boletim com localização exata processado!")

if __name__ == "__main__":
    main()