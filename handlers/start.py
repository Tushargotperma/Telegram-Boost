import logging
from telebot import TeleBot
from telebot.types import Message, CallbackQuery
from database import Database
from keyboards.inline import InlineKeyboards
from config import Config

logger = logging.getLogger(__name__)

class StartHandler:
    """Handler for start command and force join verification."""
    
    def __init__(self, bot: TeleBot, db: Database):
        self.bot = bot
        self.db = db
        self.keyboards = InlineKeyboards()
    
    def register(self):
        """Register all handlers."""
        @self.bot.message_handler(commands=['start'])
        def handle_start(message: Message):
            self._handle_start_command(message)
        
        @self.bot.callback_query_handler(func=lambda call: call.data == 'verify_join')
        def handle_verify(call: CallbackQuery):
            self._handle_verify(call)
    
    def _handle_start_command(self, message: Message):
        """Handle /start command with force join check."""
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name
        
        # Save user to database
        self.db.save_user(user_id, username, first_name, last_name)
        
        # Check force join
        if not self._check_force_join(user_id):
            self._send_force_join_message(message)
            return
        
        # Welcome user
        self._send_welcome_message(message)
    
    def _check_force_join(self, user_id: int) -> bool:
        """Check if user is a member of the force channel."""
        try:
            member = self.bot.get_chat_member(f'@{Config.FORCE_CHANNEL}', user_id)
            return member.status in ['member', 'administrator', 'creator']
        except Exception as e:
            logger.error(f"Force join check failed for user {user_id}: {e}")
            return False
    
    def _send_force_join_message(self, message: Message):
        """Send force join message."""
        text = (
            "Access Restricted\n\n"
            "You must join our channel to use this bot.\n\n"
            "Please join the channel below and click Verify to continue."
        )
        
        self.bot.send_message(
            message.chat.id,
            text,
            reply_markup=self.keyboards.force_join(Config.FORCE_CHANNEL)
        )
    
    def _handle_verify(self, call: CallbackQuery):
        """Handle verify button callback."""
        user_id = call.from_user.id
        
        if self._check_force_join(user_id):
            self.bot.edit_message_text(
                "Verification Successful\n\n"
                "Welcome to the Swift's Boost Bot. You can now access all features.",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=self.keyboards.main_menu()
            )
        else:
            self.bot.answer_callback_query(
                call.id,
                "You haven't joined the channel yet. Please join and try again.",
                show_alert=True
            )
    
    def _send_welcome_message(self, message: Message):
        """Send welcome message with main menu."""
        text = (
            "Welcome to Swift's Boost Bot\n\n"
            "Purchase Telegram boosts for your channel or group.\n"
            "Select an option below to get started."
        )
        
        self.bot.send_message(
            message.chat.id,
            text,
            reply_markup=self.keyboards.main_menu()
        )
