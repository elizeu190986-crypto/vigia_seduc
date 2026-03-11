import requests
import time
import re
import logging
from bs4 import BeautifulSoup
from datetime import datetime

# =============================
# CONFIGURAÇÕES
# =============================
URL_PAGINA = "https://www.seduc.pa.gov.br/pagina/14250-pss-07-2025---professor-nivel-superior"
INTERVALO_VERIFICACAO = 120  # segundos (2 minutos)

TELEGRAM_TOKEN = "8447403267:AAFHAXGX8Vy9D3JdNHaQ956RO0uj2IighMg"
TELEGRAM_CHAT_ID = "1088198556"

ARQUIVO_ULTIMA = "ultima_convocacao.txt"
LOG_FILE = "monitor.log"

# =============================
# LOGGING
# =============================
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# =============================
# FUNÇÕES
# =============================

def enviar_telegram(mensagem: str):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensagem,
            "parse_mode": "HTML"
        }
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        logging.error(f"Erro ao enviar Telegram: {e}")

def carregar_ultima_convocacao():
    try:
        with open(ARQUIVO_ULTIMA, "r", encoding="utf-8") as f:
            return int(f.read().strip())
    except:
        return 0

def salvar_ultima_convocacao(numero):
    with open(ARQUIVO_ULTIMA, "w", encoding="utf-8") as f:
        f.write(str(numero))

def detectar_nova_convocacao():
    try:
        response = requests.get(URL_PAGINA, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        links = soup.find_all("a")

        numeros = []

        for link in links:
            texto = link.get_text(strip=True).lower()

            # regex robusto para "17ª convocação", "17a convocação", etc
            match = re.search(r"(\d{1,2})\s*[ªa]?\s*convoca", texto)
            if match:
                numeros.append(int(match.group(1)))

        if not numeros:
            logging.warning("Não foi possível detectar número da convocação.")
            return None

        return max(numeros)

    except Exception as e:
        logging.error(f"Erro ao detectar convocação: {e}")
        return None

# =============================
# MAIN
# =============================

def main():
    logging.info("=== Monitor SEDUC iniciado ===")

    ultima_convocacao = carregar_ultima_convocacao()
    logging.info(f"Última convocação registrada: {ultima_convocacao}")

    while True:
        logging.info("Verificando nova convocação...")

        numero_atual = detectar_nova_convocacao()

        if numero_atual and numero_atual > ultima_convocacao:
            logging.warning(f"Nova convocação detectada: {numero_atual}")

            mensagem = (
                f"🚨 <b>NOVA CONVOCAÇÃO DETECTADA</b>\n\n"
                f"📄 Convocação: <b>{numero_atual}ª</b>\n"
                f"⏰ Detectado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
                f"🔗 Acesse o site da SEDUC para detalhes."
            )

            enviar_telegram(mensagem)
            salvar_ultima_convocacao(numero_atual)
            ultima_convocacao = numero_atual
        else:
            logging.info("Sem novidades.")

        logging.info("Ciclo finalizado. Aguardando próximo intervalo.")
        time.sleep(120)

# =============================
# EXECUÇÃO
# =============================
if __name__ == "__main__":
    main()
