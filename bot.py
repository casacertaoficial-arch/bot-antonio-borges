import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from pyairtable import Api

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '8955757103:AAH5nlMQyB5MfhaLuvXiKfmvB5ZyIC0JuRM')
AIRTABLE_TOKEN = os.environ.get('AIRTABLE_TOKEN', 'patKVxEOab5fVUkOu.af76e942c1fb5e5bcbad19dcbef21d84bfcc40e2451556bfb7dba1d70fd9f8a2')
BASE_ID = 'app1iGVSUpnNzLGYK'
TABLE_NAME = 'unidades'

api = Api(AIRTABLE_TOKEN)
table = api.table(BASE_ID, TABLE_NAME)

ESCOLHER_ACAO, RESERVAR_UNIDADE, RESERVAR_NOME, VENDER_UNIDADE, VENDER_NOME = range(5)

logging.basicConfig(level=logging.INFO)

def get_unidades(status=None):
      records = table.all()
      if status:
                return [r for r in records if r['fields'].get('status') == status]
            return records

def formatar_unidade(r):
      f = r['fields']
    return f"Apto {f.get('unidade','?')} | Bloco {f.get('bloco','?')} | {f.get('tipo','?')} | {f.get('status','?')}"

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
      keyboard = [
          [InlineKeyboardButton("Listar unidades", callback_data="listar")],
          [InlineKeyboardButton("Disponiveis", callback_data="disponiveis")],
          [InlineKeyboardButton("Reservar unidade", callback_data="reservar")],
          [InlineKeyboardButton("Marcar como vendido", callback_data="vender")],
]
    await update.message.reply_text(
              "Sistema Antonio Borges 122\n\nEscolha uma opcao:",
              reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ESCOLHER_ACAO

async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
      query = update.callback_query
    await query.answer()
    data = query.data
    if data == "listar":
              records = get_unidades()
              texto = "\n".join([formatar_unidade(r) for r in records]) if records else "Nenhuma unidade."
              await query.edit_message_text(f"Todas as unidades:\n\n{texto}")
              return ConversationHandler.END
elif data == "disponiveis":
        records = get_unidades("DISPONIVEL")
        texto = "\n".join([formatar_unidade(r) for r in records]) if records else "Nenhuma disponivel."
        await query.edit_message_text(f"Unidades disponiveis:\n\n{texto}")
        return ConversationHandler.END
elif data == "reservar":
        records = get_unidades("DISPONIVEL")
        if not records:
                      await query.edit_message_text("Nenhuma unidade disponivel.")
                      return ConversationHandler.END
                  texto = "\n".join([f"{i+1}. {formatar_unidade(r)}" for i, r in enumerate(records)])
        ctx.user_data['records_disponiveis'] = records
        await query.edit_message_text(f"Qual unidade reservar?\n\n{texto}\n\nDigite o numero:")
        return RESERVAR_UNIDADE
elif data == "vender":
        records = get_unidades("RESERVADO")
        if not records:
                      await query.edit_message_text("Nenhuma unidade reservada.")
                      return ConversationHandler.END
                  texto = "\n".join([f"{i+1}. {formatar_unidade(r)}" for i, r in enumerate(records)])
        ctx.user_data['records_reservados'] = records
        await query.edit_message_text(f"Qual unidade foi vendida?\n\n{texto}\n\nDigite o numero:")
        return VENDER_UNIDADE

async def reservar_escolher(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
      try:
                idx = int(update.message.text.strip()) - 1
                ctx.user_data['record_selecionado'] = ctx.user_data['records_disponiveis'][idx]
                await update.message.reply_text("Nome do comprador/reservante:")
                return RESERVAR_NOME
            except:
        await update.message.reply_text("Numero invalido. Use /start.")
                      return ConversationHandler.END

async def reservar_nome(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
      nome = update.message.text.strip()
    record = ctx.user_data['record_selecionado']
    table.update(record['id'], {'status': 'RESERVADO', 'comprador': nome})
    await update.message.reply_text(f"Unidade {record['fields'].get('unidade')} reservada para {nome}!")
    return ConversationHandler.END

async def vender_escolher(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
      try:
                idx = int(update.message.text.strip()) - 1
                ctx.user_data['record_selecionado'] = ctx.user_data['records_reservados'][idx]
                await update.message.reply_text("Confirme o nome do comprador:")
                return VENDER_NOME
            except:
        await update.message.reply_text("Numero invalido. Use /start.")
        return ConversationHandler.END

async def vender_nome(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
      nome = update.message.text.strip()
    record = ctx.user_data['record_selecionado']
    table.update(record['id'], {'status': 'VENDIDO', 'comprador': nome})
    await update.message.reply_text(f"Unidade {record['fields'].get('unidade')} marcada como VENDIDA para {nome}!")
    return ConversationHandler.END

async def cancelar(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
      await update.message.reply_text("Operacao cancelada. Use /start.")
    return ConversationHandler.END

def main():
      app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    conv = ConversationHandler(
              entry_points=[CommandHandler('start', start)],
              states={
                            ESCOLHER_ACAO: [CallbackQueryHandler(button_handler)],
                            RESERVAR_UNIDADE: [MessageHandler(filters.TEXT & ~filters.COMMAND, reservar_escolher)],
                            RESERVAR_NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reservar_nome)],
                            VENDER_UNIDADE: [MessageHandler(filters.TEXT & ~filters.COMMAND, vender_escolher)],
                            VENDER_NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, vender_nome)],
              },
              fallbacks=[CommandHandler('cancelar', cancelar)],
    )
    app.add_handler(conv)
    print('Bot rodando...')
    app.run_polling()

if __name__ == '__main__':
      main()
