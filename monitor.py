import requests
import time
import logging
import os
import re
from datetime import datetime

# =========================
# CONFIG
# =========================

URL_CONVOCACOES = "https://pss.seduc.pa.gov.br/"
URL_PAINEL = "https://pss.seduc.pa.gov.br/acompanhamento/painel.php"

ARQ_CONVOCACAO = "ultima_convocacao.txt"
ARQ_PRAZO = "prazo_detectado.txt"

INTERVALO = 60

TOKEN = "SEU_TOKEN"
CHAT_ID = "SEU_CHAT_ID"

# =========================
# LOG
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# =========================
# TELEGRAM
# =========================

def enviar_telegram(msg):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": msg
    }

    try:
        requests.post(url, data=payload, timeout=20)
    except Exception as e:
        logging.error(f"Erro Telegram: {e}")


# =========================
# CONVOCAÇÕES
# =========================

def extrair_convocacao(html):

    padrao = r'(\d+)[ªa]\s*Convoca'

    match = re.search(padrao, html, re.IGNORECASE)

    if match:
        return int(match.group(1))

    return None


def ler_ultima():

    if not os.path.exists(ARQ_CONVOCACAO):
        return 0

    with open(ARQ_CONVOCACAO, "r") as f:
        return int(f.read())


def salvar_convocacao(num):

    with open(ARQ_CONVOCACAO, "w") as f:
        f.write(str(num))


def verificar_convocacoes():

    logging.info("Verificando nova convocação...")

    r = requests.get(URL_CONVOCACOES, timeout=30)

    if r.status_code != 200:
        return

    html = r.text

    numero = extrair_convocacao(html)

    if not numero:
        return

    ultima = ler_ultima()

    if numero > ultima:

        agora = datetime.now().strftime("%d/%m/%Y %H:%M")

        mensagem = (
            "🚨 NOVA CONVOCAÇÃO DETECTADA\n\n"
            f"📄 Convocação: {numero}ª\n"
            f"⏰ Detectado em: {agora}\n\n"
            f"{URL_CONVOCACOES}"
        )

        enviar_telegram(mensagem)

        salvar_convocacao(numero)

        logging.warning(f"Nova convocação detectada: {numero}")

    else:

        logging.info("Sem novas convocações.")


# =========================
# PRAZO DOCUMENTOS
# =========================

def verificar_painel():

    logging.info("Verificando painel de documentos...")

    r = requests.get(URL_PAINEL, timeout=30)

    if r.status_code != 200:
        return

    html = r.text

    padrao = r'Prazo\s*de\s*Envio\s*da\s*Documenta'

    encontrou = re.search(padrao, html, re.IGNORECASE)

    if not encontrou:
        logging.info("Nenhum prazo detectado.")
        return

    prazo_texto = encontrou.group()

    if os.path.exists(ARQ_PRAZO):

        with open(ARQ_PRAZO, "r") as f:
            salvo = f.read()

        if salvo == prazo_texto:
            return

    agora = datetime.now().strftime("%d/%m/%Y %H:%M")

    mensagem = (
        "🚨 PRAZO PARA ENVIO DE DOCUMENTOS DETECTADO\n\n"
        "Verifique imediatamente o painel da SEDUC.\n\n"
        f"⏰ Detectado em: {agora}\n\n"
        f"{URL_PAINEL}"
    )

    enviar_telegram(mensagem)

    with open(ARQ_PRAZO, "w") as f:
        f.write(prazo_texto)

    logging.warning("Prazo de documentos detectado!")


# =========================
# LOOP
# =========================

logging.info("=== Monitor SEDUC iniciado ===")

while True:

    try:

        verificar_convocacoes()

        verificar_painel()

    except Exception as erro:

        logging.error(f"Erro geral: {erro}")

    logging.info("Aguardando próximo ciclo...\n")

    time.sleep(INTERVALO)
