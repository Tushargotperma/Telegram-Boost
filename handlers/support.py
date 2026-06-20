import logging
from telebot import TeleBot
from telebot.types import CallbackQuery, Message
from database import Database
from keyboards.inline import InlineKeyboards
from config import Config

logger = logging.getLogger(__name__)

class SupportHandler:
    """Handler for support interactions."""
    
    def __init__(self, bot: TeleBot, db: Database):
        self.bot = bot
        self.db = db
        self.keyboards = InlineKeyboards()
    
    def register(self):
        """Register all handlers."""
        @self.bot.callback_query_handler(func=lambda call: call.data == 'support')
        def handle_support(call: CallbackQuery):
            self._handle_support_request(call)
        
        @self.bot.message_handler(func=lambda m: m.text and 'support' in m.text.lower())
        def handle_support_message(message: Message):
            self._handle_support_message(message)
    
    def _handle_support_request(self, call: CallbackQuery):
        """Handle support button click."""
        text = (
            "Support\n\n"
            "For assistance with your orders or payment issues, "
            "please contact our support team.\n\n"
            f"Support Username: @{Config.SUPPORT_USERNAME}\n\n"
            "You can also use the button below to quickly reach us."
        )
        
        self.bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=self.keyboards.support()
        )
    
    def _handle_support_message(self, message: Message):
        """Handle support-related messages."""
        # Forward support messages to admin if not admin
        if message.from_user.id != Config.ADMIN_ID:
            try:
                self.bot.forward_message(
                    Config.ADMIN_ID,
                    message.chat.id,
                    message.message_id
                )
                self.bot.reply_to(
                    message,
                    "Your message has been forwarded to support. We will respond shortly."
                )
            except Exception as e:
                logger.error(f"Failed to forward support message: {e}")
                self.bot.reply_to(
                    message,
                    "Sorry, there was an error sending your message. Please try again later."
              )
