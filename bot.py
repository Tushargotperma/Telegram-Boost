import logging
import time
from telebot import TeleBot
from telebot.types import Message
from config import Config
from database import Database
from handlers import (
    StartHandler,
    OrderHandler,
    PaymentHandler,
    AdminHandler,
    SupportHandler
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class BoostStoreBot:
    """Main bot application class."""
    
    def __init__(self):
        # Validate configuration
        try:
            Config.validate()
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            raise
        
        # Initialize components
        self.bot = TeleBot(Config.BOT_TOKEN)
        self.db = Database()
        
        # Initialize handlers
        self.start_handler = StartHandler(self.bot, self.db)
        self.order_handler = OrderHandler(self.bot, self.db)
        self.payment_handler = PaymentHandler(self.bot, self.db)
        self.admin_handler = AdminHandler(self.bot, self.db)
        self.support_handler = SupportHandler(self.bot, self.db)
    
    def register_handlers(self):
        """Register all bot handlers."""
        self.start_handler.register()
        self.order_handler.register()
        self.payment_handler.register()
        self.admin_handler.register()
        self.support_handler.register()
        
        # Register default handlers
        @self.bot.message_handler(func=lambda m: True)
        def default_handler(message: Message):
            self._handle_default(message)
    
    def _handle_default(self, message: Message):
        """Handle unknown messages."""
        if message.from_user.id == Config.ADMIN_ID:
            return
        
        self.bot.reply_to(
            message,
            "I didn't understand that. Please use the menu buttons to navigate."
        )
    
    def run(self):
        """Start the bot."""
        try:
            logger.info("Starting Swift's Boost Bot...")
            self.register_handlers()
            
            # Remove webhook if set
            self.bot.remove_webhook()
            
            logger.info(f"Bot started successfully. Admin ID: {Config.ADMIN_ID}")
            self.bot.infinity_polling(timeout=60, long_polling_timeout=60)
            
        except KeyboardInterrupt:
            logger.info("Bot stopped by user.")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            raise
        finally:
            logger.info("Bot shutdown complete.")

def main():
    """Main entry point."""
    try:
        bot = BoostStoreBot()
        bot.run()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

if __name__ == '__main__':
    main()
