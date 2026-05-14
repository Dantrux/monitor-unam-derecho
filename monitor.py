"""
Monitor de Convocatorias — UNAM Derecho
Corre en GitHub Actions cada 5 minutos. Sin laptop. Sin límites. Gratis.
Notificación instantánea al celular vía ntfy.sh
"""

import requests
import hashlib
import os
from bs4 import BeautifulSoup

# ─────────────────────────────────────────────
# CONFIGURACIÓN — edita SOLO estas dos líneas
# ─────────────────────────────────────────────

URL = "https://www.derecho.unam.mx/diplomados/diplomados.php"

# Tu tema único en ntfy — cámbialo por algo solo tuyo (cualquier texto sin espacios)
# Ejemplo: "sergio-derecho-unam-2025-abc"
# IMPORTANTE: ponlo también en tu app ntfy al suscribirte
NTFY_TOPIC = "sergio-unam-derecho-nay-2025"  # <-- CAMBIA ESTO

# ─────────────────────────────────────────────
ARCHIVO_SNAPSHOT = "diplomados_snapshot.txt"

PALABRAS_URGENTES = [
    "preinscripción", "preinscripcion",
    "inscripción", "inscripcion",
    "convocatoria", "registro", "cupo", "abierto"
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def obtener_contenido():
    resp = requests.get(URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    lineas = [l.strip() for l in soup.get_text("\n").splitlines() if l.strip()]
    return "\n".join(lineas)


def calcular_hash(texto):
    return hashlib.md5(texto.encode("utf-8")).hexdigest()


def cargar_snapshot():
    if os.path.exists(ARCHIVO_SNAPSHOT):
        with open(ARCHIVO_SNAPSHOT, "r") as f:
            return f.read().strip()
    return ""


def guardar_snapshot(h):
    with open(ARCHIVO_SNAPSHOT, "w") as f:
        f.write(h)


def detectar_palabras(texto):
    return [p for p in PALABRAS_URGENTES if p in texto.lower()]


def notificar(titulo, mensaje, urgente=False):
    """Manda push notification al celular vía ntfy.sh"""
    prioridad = "urgent" if urgente else "high"
    etiquetas = "rotating_light,school" if urgente else "bell,school"
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=mensaje.encode("utf-8"),
            headers={
                "Title": titulo,
                "Priority": prioridad,
                "Tags": etiquetas,
            },
            timeout=10
        )
        print(f"Notificación enviada: {titulo}")
    except Exception as e:
        print(f"Error al enviar notificación: {e}")


def main():
    print(f"Revisando: {URL}")

    contenido = obtener_contenido()
    hash_actual = calcular_hash(contenido)
    hash_anterior = cargar_snapshot()

    # Primera ejecución — solo guarda snapshot, no alerta
    if not hash_anterior:
        guardar_snapshot(hash_actual)
        print("Primera ejecución: snapshot guardado.")
        return

    if hash_actual != hash_anterior:
        palabras = detectar_palabras(contenido)
        guardar_snapshot(hash_actual)

        if palabras:
            print(f"ALERTA URGENTE — palabras detectadas: {', '.join(palabras)}")
            notificar(
                titulo="CONVOCATORIA ABIERTA — UNAM Derecho",
                mensaje=(
                    f"Detectado: {', '.join(palabras)}\n"
                    f"ENTRA YA: {URL}"
                ),
                urgente=True
            )
        else:
            print("Cambio menor detectado en la página.")
            notificar(
                titulo="Cambio en página — UNAM Derecho",
                mensaje=f"La página de diplomados fue actualizada.\nRevisa: {URL}",
                urgente=False
            )
    else:
        print("Sin cambios.")


if __name__ == "__main__":
    main()
