import logging
from telebot import TeleBot
from telebot.types import Message, CallbackQuery
from database import Database
from keyboards.inline import InlineKeyboards
from config import Config

logger = logging.getLogger(__name__)

class OrderHandler:
    """Handler for order creation and management."""
    
    def __init__(self, bot: TeleBot, db: Database):
        self.bot = bot
        self.db = db
        self.keyboards = InlineKeyboards()
        self.user_quantities = {}  # Temporary storage for custom quantities
    
    def register(self):
        """Register all handlers."""
        @self.bot.callback_query_handler(func=lambda call: call.data == 'purchase_boosts')
        def handle_purchase(call: CallbackQuery):
            self._handle_purchase_start(call)
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('qty_'))
        def handle_quantity(call: CallbackQuery):
            self._handle_quantity_selection(call)
        
        @self.bot.callback_query_handler(func=lambda call: call.data == 'custom_quantity')
        def handle_custom(call: CallbackQuery):
            self._handle_custom_quantity(call)
        
        @self.bot.message_handler(func=lambda m: m.text and m.text.isdigit() and m.text not in ['/start', '/confirm', '/done', '/reject'])
        def handle_custom_quantity_input(message: Message):
            self._handle_custom_quantity_input(message)
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_'))
        def handle_cancel(call: CallbackQuery):
            self._handle_cancel_order(call)
    
    def _handle_purchase_start(self, call: CallbackQuery):
        """Start the purchase flow."""
        # Check if user has pending order
        user_id = call.from_user.id
        active_order = self.db.get_user_active_order(user_id)
        
        if active_order:
            self.bot.answer_callback_query(
                call.id,
                f"You have a pending order #{active_order['order_id']}. Complete or cancel it first.",
                show_alert=True
            )
            return
        
        text = "Select Boost Quantity\n\nChoose the number of boosts you want to purchase:"
        
        self.bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=self.keyboards.boost_quantities()
        )
    
    def _handle_quantity_selection(self, call: CallbackQuery):
        """Handle quantity selection from predefined options."""
        quantity = int(call.data.split('_')[1])
        self._show_order_summary(call, quantity)
    
    def _handle_custom_quantity(self, call: CallbackQuery):
        """Handle custom quantity request."""
        text = "Custom Quantity\n\nPlease enter the number of boosts you want (minimum 4):"
        
        self.bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=None
        )
        
        # Store state to handle input
        self.user_quantities[call.from_user.id] = 'waiting_for_quantity'
    
    def _handle_custom_quantity_input(self, message: Message):
        """Handle custom quantity input from user."""
        user_id = message.from_user.id
        
        if self.user_quantities.get(user_id) != 'waiting_for_quantity':
            return
        
        try:
            quantity = int(message.text)
            if quantity < 4:
                raise ValueError("Quantity must be at least 4")
            
            # Clear state
            del self.user_quantities[user_id]
            
            # Show summary
            self._show_order_summary_from_message(message, quantity)
            
        except ValueError:
            self.bot.reply_to(
                message,
                "Invalid quantity. Please enter a valid positive number."
            )
    
    def _show_order_summary(self, call: CallbackQuery, quantity: int):
        """Show order summary for callback query."""
        user = call.from_user
        amount = quantity * Config.PRICE_PER_BOOST
        
        text = (
            "Order Summary\n\n"
            f"Quantity: {quantity} Boosts\n"
            f"Amount: ${amount:.2f}\n\n"
            "Payment Address:\n"
            f"{Config.WALLET_ADDRESS}\n\n"
            "Please send the exact amount and click '
        
        # Create order in database
        order_id = self.db.create_order(
            user.id,
            user.username or user.first_name,
            quantity,
            amount
        )
        
        self.bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=self.keyboards.order_summary(order_id)
        )
    
    def _show_order_summary_from_message(self, message: Message, quantity: int):
        """Show order summary from message."""
        user = message.from_user
        amount = quantity * Config.PRICE_PER_BOOST
        
        text = (
            "Order Summary\n\n"
            f"Quantity: {quantity} Boosts\n"
            f"Amount: ${amount:.2f}\n\n"
            "Payment Address:\n"
            f"{Config.WALLET_ADDRESS}\n\n"
            "Please send the exact amount and click 'Confirm Payment' when done.(the address you are seeing that is erc20 address so send erc20 otherwise funds will be lost)"
        )"
        )
        
        # Create order in database
        order_id = self.db.create_order(
            user.id,
            user.username or user.first_name,
            quantity,
            amount
        )
        
        self.bot.send_message(
            message.chat.id,
            text,
            reply_markup=self.keyboards.order_summary(order_id)
        )
    
    def _handle_cancel_order(self, call: CallbackQuery):
        """Handle order cancellation."""
        order_id = int(call.data.split('_')[1])
        order = self.db.get_order(order_id)
        
        if not order:
            self.bot.answer_callback_query(call.id, "Order not found.")
            return
        
        if order['status'] not in ['pending_payment', 'payment_review']:
            self.bot.answer_callback_query(
                call.id,
                "Cannot cancel order at this stage.",
                show_alert=True
            )
            return
        
        # Update order status
        self.db.update_order_status(order_id, 'rejected')
        
        text = "Order Cancelled\n\nYour order has been cancelled successfully."
        
        self.bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=self.keyboards.main_menu()
        )
