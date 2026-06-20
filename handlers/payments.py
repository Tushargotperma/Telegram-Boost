import logging
from telebot import TeleBot
from telebot.types import CallbackQuery, Message
from database import Database
from keyboards.inline import InlineKeyboards
from config import Config

logger = logging.getLogger(__name__)

class PaymentHandler:
    """Handler for payment verification and processing."""
    
    def __init__(self, bot: TeleBot, db: Database):
        self.bot = bot
        self.db = db
        self.keyboards = InlineKeyboards()
    
    def register(self):
        """Register all handlers."""
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('paid_'))
        def handle_paid(call: CallbackQuery):
            self._handle_payment_confirmation(call)
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('check_'))
        def handle_check(call: CallbackQuery):
            self._handle_status_check(call)
        
        @self.bot.callback_query_handler(func=lambda call: call.data == 'order_status')
        def handle_order_status(call: CallbackQuery):
            self._handle_order_status_request(call)
    
    def _handle_payment_confirmation(self, call: CallbackQuery):
        """Handle payment confirmation from user."""
        order_id = int(call.data.split('_')[1])
        order = self.db.get_order(order_id)
        
        if not order:
            self.bot.answer_callback_query(call.id, "Order not found.")
            return
        
        if order['status'] != 'pending_payment':
            self.bot.answer_callback_query(
                call.id,
                f"Order status is already {order['status']}",
                show_alert=True
            )
            return
        
        # Update order status
        self.db.update_order_status(order_id, 'payment_review')
        
        text = (
            "Payment Pending Verification\n\n"
            "If you have completed the payment, please contact support "
            "and send the payment screenshot for verification.\n\n"
            f"Order ID: #{order_id:05d}"
        )
        
        self.bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=self.keyboards.pending_payment(order_id, Config.SUPPORT_USERNAME)
        )
        
        # Notify admin
        self._notify_admin_new_payment(order)
        
        self.bot.answer_callback_query(call.id, "Payment confirmation sent for review.")
    
    def _handle_status_check(self, call: CallbackQuery):
        """Check and display order status."""
        order_id = int(call.data.split('_')[1])
        order = self.db.get_order(order_id)
        
        if not order:
            self.bot.answer_callback_query(call.id, "Order not found.")
            return
        
        status_text = self._get_status_text(order['status'])
        
        text = (
            "Order Status\n\n"
            f"Order ID: #{order_id:05d}\n"
            f"Quantity: {order['quantity']} Boosts\n"
            f"Amount: ${order['amount']:.2f}\n"
            f"Status: {status_text}\n"
            f"Created: {order['created_at']}"
        )
        
        self.bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=self.keyboards.order_status()
        )
    
    def _handle_order_status_request(self, call: CallbackQuery):
        """Show all user orders."""
        user_id = call.from_user.id
        orders = self.db.get_user_orders(user_id)
        
        if not orders:
            text = "No Orders\n\nYou don't have any orders yet."
            self.bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=self.keyboards.main_menu()
            )
            return
        
        text = "Your Orders\n\n"
        for order in orders[:5]:  # Show 5 most recent
            status_text = self._get_status_text(order['status'])
            text += (
                f"#{order['order_id']:05d} - "
                f"{order['quantity']} boosts - "
                f"{status_text}\n"
            )
        
        text += f"\nShowing 5 most recent orders out of {len(orders)} total."
        
        self.bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=self.keyboards.order_status()
        )
    
    def _notify_admin_new_payment(self, order: dict):
        """Notify admin about new payment confirmation."""
        try:
            text = (
                "Payment Confirmation Received\n\n"
                f"Order ID: #{order['order_id']:05d}\n"
                f"User: @{order['username'] or 'N/A'}\n"
                f"User ID: {order['user_id']}\n"
                f"Quantity: {order['quantity']} Boosts\n"
                f"Amount: ${order['amount']:.2f}"
            )
            
            self.bot.send_message(
                Config.ADMIN_ID,
                text,
                reply_markup=self.keyboards.admin_order_actions(order['order_id'])
            )
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")
    
    def _get_status_text(self, status: str) -> str:
        """Get human-readable status text."""
        status_map = {
            'pending_payment': 'Pending Payment',
            'payment_review': 'Payment Review',
            'awaiting_target': 'Awaiting Target',
            'processing': 'Processing',
            'completed': 'Completed',
            'rejected': 'Rejected'
        }
        return status_map.get(status, status)
