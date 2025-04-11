
import requests
import json
import time
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
API_KEY = os.getenv("FOOTBALL_API_KEY")

def enviar_alerta(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mensagem}
    requests.post(url, data=data)

def carregar_filtros():
    with open("filtros.json", "r") as f:
        return json.load(f)

import requests

def obter_jogos_ao_vivo():
    url = "https://api.sofascore.com/api/v1/sport/football/events/live"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json().get("events", [])
    else:
        print(f"Erro ao acessar a API da Sofascore: {response.status_code}")
        return []


def analisar_jogos(jogos, filtros):
    print(f"🎯 Número de jogos encontrados: {len(jogos)}")
    for jogo in jogos:
        try:
            print(f"👀 Analisando: {jogo['teams']['home']['name']} x {jogo['teams']['away']['name']} ({jogo['fixture']['status']['elapsed']}min)")
            status = jogo["fixture"]["status"]["elapsed"] or 0
            placar = jogo["goals"]
            estatisticas = jogo.get("statistics", [])
            times = jogo["teams"]
            home = times["home"]["name"]
            away = times["away"]["name"]
            score_home = placar["home"]
            score_away = placar["away"]

            def get_stat(time_side, stat_type):
                for bloco in estatisticas:
                    if bloco["team"]["name"] == times[time_side]["name"]:
                        for stat in bloco["statistics"]:
                            if stat["type"] == stat_type:
                                return stat["value"] or 0
                return 0

            posse_home = get_stat("home", "Ball Possession")
            posse_away = get_stat("away", "Ball Possession")
            finalizacoes_home = get_stat("home", "Total Shots")
            finalizacoes_away = get_stat("away", "Total Shots")
            chutes_gol_home = get_stat("home", "Shots on Goal")
            chutes_gol_away = get_stat("away", "Shots on Goal")
            escanteios_total = get_stat("home", "Corner Kicks") + get_stat("away", "Corner Kicks")
            defesas_goleiro_away = get_stat("away", "Goalkeeper Saves")

            # Filtro 1
            if score_home == 0 and score_away == 0 and status <= 20:
                if finalizacoes_home + finalizacoes_away >= 7:
                    enviar_alerta(f"⚠️ PRESSÃO SEM GOL ({home} x {away})\nPlacar: 0x0 aos {status}min com +7 finalizações.")

            # Filtro 2
            if status <= 45 and posse_home >= 70 and finalizacoes_home >= 6 and chutes_gol_home >= 4 and defesas_goleiro_away >= 3:
                enviar_alerta(f"🔥 MANDANTE PRESSIONANDO NO 1º TEMPO\n{home} com 70%+ posse, 6+ chutes, 4+ no gol e 3+ defesas obrigando o goleiro.")

            # Filtro 3
            if status >= 80 and escanteios_total > 10:
                if (score_home == score_away or score_home < score_away) and posse_home >= 70 and chutes_gol_home > chutes_gol_away:
                    enviar_alerta(f"🚨 ESCANTEIOS FINAIS POSSÍVEIS ({home} x {away})\nTime da casa pressionando e precisa vencer.")

            # Filtro 4
            if score_home == 0 and score_away == 0 and status <= 35:
                if posse_home >= 65 and finalizacoes_home >= 8 and chutes_gol_home >= 4 and get_stat("home", "Corner Kicks") >= 5:
                    enviar_alerta(f"💣 PRESSÃO DO MANDANTE NO HT\n{home} com 65%+ posse, 8+ chutes, 4+ no gol e 5+ escanteios.")

            # Filtro 5
            if status >= 60 and score_away > score_home:
                if posse_home >= 65 and finalizacoes_home >= 10 and chutes_gol_home >= 5 and escanteios_total >= 7:
                    enviar_alerta(f"⚔️ ZEBRA SEGURANDO PRESSÃO\n{home} pressionando muito pra empatar após os 60min.")

            # Filtro 6
            if status >= 75 and (score_home == score_away):
                if chutes_gol_home >= 6 and chutes_gol_away >= 6 and get_stat("home", "Corner Kicks") >= 3 and get_stat("away", "Corner Kicks") >= 3:
                    enviar_alerta(f"🔥 JOGO ABERTO AOS {status}min ({home} x {away})\nEmpate com ambos atacando. Pode vir gol ou canto.")

            # Filtro 7
            if status >= 80 and score_home > score_away:
                if posse_away >= 55 and chutes_gol_away >= 4 and get_stat("away", "Corner Kicks") >= 2:
                    enviar_alerta(f"🧨 PRESSÃO DA ZEBRA NO FINAL\n{away} buscando empate, jogo pode ficar aberto no fim.")

            # Filtro 8
            if status >= 55 and status <= 75 and escanteios_total >= 6 and finalizacoes_home + finalizacoes_away >= 10:
                enviar_alerta(f"🚀 JOGO ACORDOU NO 2º TEMPO ({home} x {away})\nVolume ofensivo alto após 1º tempo fraco.")

            # Filtro de TESTE (enviar alerta se tiver 1 chute no gol do mandante)
            print(f"🔍 DEBUG — {home} x {away} | Chutes no gol: {chutes_gol_home}")
            if chutes_gol_home >= 1:
                print(f"🔎 {home} x {away} | Chutes no gol do mandante: {chutes_gol_home}")
                enviar_alerta(f"🧪 TESTE: Alerta ativado com 1+ chute no gol para o mandante ({home} x {away})")

        except Exception as e:
            print(f"Erro ao analisar jogo: {e}")

if __name__ == "__main__":
    filtros = carregar_filtros()

    # Alerta de confirmação ao iniciar
    enviar_alerta("🚨 Teste de envio manual: o bot está vivo e enviando mensagens!")

    while True:
        print("🔄 Bot está rodando e checando os jogos ao vivo...")
        jogos = obter_jogos_ao_vivo()
        analisar_jogos(jogos, filtros)
        time.sleep(30)
