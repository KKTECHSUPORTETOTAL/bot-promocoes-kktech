import os
import logging
import asyncio
import requests
from datetime import datetime
import pytz
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURAÇÕES DO BOT ---
TELEGRAM_TOKEN = "8992743644:AAHdlu5_p0i1QI2B5t029Onyv9xvdgxJ7PQ"
ML_AFFILIATE_TAG = "kktechsuportetotal"

# SE SOUBER O ID NUMÉRICO (EX: "-100123456789"), COLOQUE ABAIXO.
# CASO CONTRÁRIO, ADICIONE O BOT NO GRUPO COMO ADMIN E DIGITE /id LÁ DENTRO.
CHAT_ID_GRUPO = "-1004292230252" 

PALAVRAS_NICHO = [
    # Manutenção de Celulares e Smartphones
    "tela de celular display",
    "bateria celular",
    "conector de carga celular",
    "estacao de solda",
    "separadora de lcd",
    "microscopio trinocular bancada",
    "multimetro digital profissional",
    
    # Computadores, Notebooks e Peças
    "placa mae notebook",
    "placa mae desktop",
    "processador intel amd",
    "memoria ram ddr4 ddr5",
    "ssd nvme",
    "fonte atx pc",
    "pasta termica",
    "gravador de bios eeprom",
    
    # Periféricos, Acessórios e Gadgets
    "teclado mecanico gamer",
    "mouse gamer",
    "headset gamer",
    "monitor gamer",
    "suporte articulado para monitor",
    
    # Impressoras e Suprimentos
    "cabeca de impressao",
    "kit tinta epson",
    "toner impressora laser",
    
    # Redes, Fibra Óptica e Ferramentas
    "roteador gigabit wi-fi",
    "switch de rede",
    "alicate de crimpar rj45",
    "cabo de rede cat6",
    "testador de cabo de rede",
    "caneta optica localizadora de falhas fibra"
]

INTERVALO_BUSCA = 900  # 15 Minutos

produtos_postados = set()
aviso_encerrado_enviado = False
aviso_iniciado_enviado = False

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def buscar_promocoes_nicho():
    novas_ofertas = []
    
    for termo in PALAVRAS_NICHO:
        url = f"https://api.mercadolibre.com/sites/MLB/search?q={termo}&limit=3"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            for item in data.get("results", []):
                item_id = item.get("id")
                
                if item_id in produtos_postados:
                    continue
                
                titulo = item.get("title")
                preco = item.get("price")
                link_original = item.get("permalink")
                imagem = item.get("thumbnail", "").replace("-I.jpg", "-O.jpg")
                
                link_afiliado = f"{link_original}?matt_tool=SEU_TOOL_ID&matt_word={ML_AFFILIATE_TAG}"
                
                novas_ofertas.append({
                    "id": item_id,
                    "titulo": titulo,
                    "preco": preco,
                    "link": link_afiliado,
                    "imagem": imagem
                })
                
                produtos_postados.add(item_id)
                break
                
    return novas_ofertas

# --- MENSAGEM AUTOMÁTICA DE BOAS-VINDAS ---
async def boas_vindas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            continue
            
        nome = member.first_name
        texto_boas_vindas = (
            f"👋 **Seja muito bem-vindo(a), {nome}!**\n\n"
            f"🛠️ Este é o grupo oficial de ofertas da **KKTECH Suporte Total**!\n\n"
            f"Aqui postamos diariamente as melhores promoções de:\n"
            f"• Peças de reposição e componentes eletrônicos\n"
            f"• Ferramentas de bancada e manutenção\n"
            f"• Periféricos, SSDs, memórias e computadores\n"
            f"• Equipamentos de redes e fibra óptica\n\n"
            f"⚡ *Fique atento ao grupo, enviamos achados com desconto a cada 15 minutos!*"
        )
        await update.message.reply_text(texto_boas_vindas, parse_mode="Markdown")

# --- MONITORAMENTO E AVISOS DAS 00H00 E 00H15 ---
async def tarefa_postagem_automatica(app):
    global aviso_encerrado_enviado, aviso_iniciado_enviado
    
    fuso_brasilia = pytz.timezone('America/Sao_Paulo')
    
    while True:
        try:
            if CHAT_ID_GRUPO:
                agora = datetime.now(fuso_brasilia)
                hora = agora.hour
                minuto = agora.minute
                
                # AVISO DAS 00:00 (Encerramento do dia)
                if hora == 0 and minuto == 0 and not aviso_encerrado_enviado:
                    msg_fim = (
                        "🌙 **OFERTAS DO DIA ENCERRADAS!**\n\n"
                        "Chegamos à meia-noite! As promoções do dia anterior foram finalizadas.\n"
                        "Em alguns minutos daremos início ao garimpo das ofertas da madrugada e do novo dia! 😴🛠️"
                    )
                    await app.bot.send_message(chat_id=CHAT_ID_GRUPO, text=msg_fim, parse_mode="Markdown")
                    aviso_encerrado_enviado = True
                    aviso_iniciado_enviado = False
                
                # AVISO DAS 00:15 (Início do novo dia)
                elif hora == 0 and minuto == 15 and not aviso_iniciado_enviado:
                    msg_inicio = (
                        "☀️ **RODADA DE PROMOÇÕES INICIADA!** 🚀\n\n"
                        "Já estamos a monitorar as melhores ofertas do Mercado Livre para bancada, TI e eletrónica.\n"
                        "Fique atento, as primeiras ofertas do dia já vão começar a chegar! 🔥💡"
                    )
                    await app.bot.send_message(chat_id=CHAT_ID_GRUPO, text=msg_inicio, parse_mode="Markdown")
                    aviso_iniciado_enviado = True
                    aviso_encerrado_enviado = False
                
                # Reseta as flags durante o dia
                elif hora != 0:
                    aviso_encerrado_enviado = False
                    aviso_iniciado_enviado = False
                
                # BUSCA NORMAL DE PROMOÇÕES
                print("🔍 Buscando ofertas gerais de assistência técnica e TI...")
                ofertas = buscar_promocoes_nicho()
                
                for prod in ofertas:
                    mensagem = (
                        f"🛠️ **ACHADO PARA BANCADA & TI** 💡\n\n"
                        f"📦 **{prod['titulo']}**\n\n"
                        f"💰 **Preço:** R$ {prod['preco']:.2f}\n\n"
                        f"🔗 **Garante a sua oferta aqui:** {prod['link']}\n\n"
                        f"⚡ *Dica: Item essencial para o seu laboratório ou reposição de estoque!*"
                    )
                    
                    if prod["imagem"]:
                        await app.bot.send_photo(
                            chat_id=CHAT_ID_GRUPO,
                            photo=prod["imagem"],
                            caption=mensagem,
                            parse_mode="Markdown"
                        )
                    else:
                        await app.bot.send_message(
                            chat_id=CHAT_ID_GRUPO,
                            text=mensagem,
                            parse_mode="Markdown"
                        )
                    
                    await asyncio.sleep(6)
            else:
                print("⚠️ Defina o CHAT_ID_GRUPO para iniciar o envio automático.")
                
        except Exception as e:
            logging.error(f"Erro na automação: {e}")
            
        await asyncio.sleep(INTERVALO_BUSCA)

async def post_init(application):
    asyncio.create_task(tarefa_postagem_automatica(application))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot Promoções KKTECH operando a todo vapor!")

async def pegar_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"📍 O ID deste grupo/chat é: `{chat_id}`", parse_mode="Markdown")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("id", pegar_id))
    
    # Handler para Boas-Vindas aos novos membros
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, boas_vindas))
    
    print("Bot a rodar...")
    application.run_polling()
