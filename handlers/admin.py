import logging
from telebot import TeleBot
from telebot.types import Message
from database import Database
from keyboards.inline import InlineKeyboards
from config import Config

logger = logging.getLogger(__name__)

class AdminHandler:
    """Handler for admin commands and operations."""
    
    def __init__(self, bot: TeleBot, db: Database):
        self.bot = bot
        self.db = db
        self.keyboards = InlineKeyboards()
    
    def register(self):
        """Register all handlers."""
        @self.bot.message_handler(commands=['confirm'])
        def handle_confirm(message: Message):
            self._handle_confirm_order(message)
        
        @self.bot.message_handler(commands=['done'])
        def handle_done(message: Message):
            self._handle_complete_order(message)
        
        @self.bot.message_handler(commands=['reject'])
        def handle_reject(message: Message):
            self._handle_reject_order(message)
        
        @self.bot.message_handler(commands=['stats'])
        def handle_stats(message: Message):
            self._handle_stats(message)
        
        @self.bot.message_handler(func=lambda m: m.text and m.text.startswith('https://t.me/'))
        def handle_target_link(message: Message):
            self._handle_target_link(message)
    
    def _is_admin(self, user_id: int) -> bool:
        """Check if user is admin."""
        return user_id == Config.ADMIN_ID
    
    def _handle_confirm_order(self, message: Message):
        """Handle order confirmation by admin."""
        if not self._is_admin(message.from_user.id):
            self.bot.reply_to(message, "Unauthorized command.")
            return
        
        try:
            args = message.text.split()
            if len(args) < 2:
                self.bot.reply_to(message, "Usage: /confirm ORDER_ID")
                return
            
            order_id = int(args[1])
            order = self.db.get_order(order_id)
            
            if not order:
                self.bot.reply_to(message, f"Order #{order_id} not found.")
                return
            
            if order['status'] != 'payment_review':
                self.bot.reply_to(
                    message,
                    f"Order status is {order['status']}. Cannot confirm at this stage."
                )
                return
            
            # Update status
            self.db.update_order_status(order_id, 'awaiting_target')
            
            # Notify user
            self._notify_user_payment_verified(order)
            
            self.bot.reply_to(message, f"Payment for order #{order_id} confirmed. Awaiting target link.")
            
        except ValueError:
            self.bot.reply_to(message, "Invalid ORDER_ID. Please provide a number.")
        except Exception as e:
            logger.error(f"Error in confirm order: {e}")
            self.bot.reply_to(message, f"Error confirming order: {str(e)}")
    
    def _handle_complete_order(self, message: Message):
        """Handle order completion by admin."""
        if not self._is_admin(message.from_user.id):
            self.bot.reply_to(message, "Unauthorized command.")
            return
        
        try:
            args = message.text.split()
            if len(args) < 2:
                self.bot.reply_to(message, "Usage: /done ORDER_ID")
                return
            
            order_id = int(args[1])
            order = self.db.get_order(order_id)
            
            if not order:
                self.bot.reply_to(message, f"Order #{order_id} not found.")
                return
            
            if order['status'] != 'processing':
                self.bot.reply_to(
                    message,
                    f"Order status is {order['status']}. Cannot complete at this stage."
                )
                return
            
            # Update status
            self.db.update_order_status(order_id, 'completed')
            
            # Notify user
            self._notify_user_order_completed(order)
            
            self.bot.reply_to(message, f"Order #{order_id} marked as completed.")
            
        except ValueError:
            self.bot.reply_to(message, "Invalid ORDER_ID. Please provide a number.")
        except Exception as e:
            logger.error(f"Error in complete order: {e}")
            self.bot.reply_to(message, f"Error completing order: {str(e)}")
    
    def _handle_reject_order(self, message: Message):
        """Handle order rejection by admin."""
        if not self._is_admin(message.from_user.id):
            self.bot.reply_to(message, "Unauthorized command.")
            return
        
        try:
            args = message.text.split()
            if len(args) < 2:
                self.bot.reply_to(message, "Usage: /reject ORDER_ID")
                return
            
            order_id = int(args[1])
            order = self.db.get_order(order_id)
            
            if not order:
                self.bot.reply_to(message, f"Order #{order_id} not found.")
                return
            
            if order['status'] not in ['pending_payment', 'payment_review']:
                self.bot.reply_to(
                    message,
                    f"Order status is {order['status']}. Cannot reject at this stage."
                )
                return
            
            # Update status
            self.db.update_order_status(order_id, 'rejected')
            
            # Notify user
            self._notify_user_order_rejected(order)
            
            self.bot.reply_to(message, f"Order #{order_id} rejected.")
            
        except ValueError:
            self.bot.reply_to(message, "Invalid ORDER_ID. Please provide a number.")
        except Exception as e:
            logger.error(f"Error in reject order: {e}")
            self.bot.reply_to(message, f"Error rejecting order: {str(e)}")
    
    def _handle_stats(self, message: Message):
        """Show admin statistics."""
        if not self._is_admin(message.from_user.id):
            self.bot.reply_to(message, "Unauthorized command.")
            return
        
        try:
            pending = self.db.get_orders_by_status('pending_payment')
            review = self.db.get_orders_by_status('payment_review')
            waiting = self.db.get_orders_by_status('awaiting_target')
            processing = self.db.get_orders_by_status('processing')
            completed = self.db.get_orders_by_status('completed')
            
            text = (
                "Bot Statistics\n\n"
                f"Pending Payment: {len(pending)}\n"
                f"Payment Review: {len(review)}\n"
                f"Awaiting Target: {len(waiting)}\n"
                f"Processing: {len(processing)}\n"
                f"Completed: {len(completed)}"
            )
            
            self.bot.reply_to(message, text)
            
        except Exception as e:
            logger.error(f"Error in stats: {e}")
            self.bot.reply_to(message, f"Error fetching statistics: {str(e)}")
    
    def _handle_target_link(self, message: Message):
        """Handle target link submission from user."""
        user_id = message.from_user.id
        
        # Find pending order for user
        order = self.db.get_user_active_order(user_id)
        if not order or order['status'] != 'awaiting_target':
            return
        
        target_link = message.text.strip()
        
        # Validate link
        if not target_link.startswith('https://t.me/'):
            self.bot.reply_to(message, "Invalid link. Please provide a valid Telegram link.")
            return
        
        # Update order
        self.db.update_order_target(order['order_id'], target_link)
        
        # Notify admin
        self._notify_admin_new_order(order['order_id'])
        
        self.bot.reply_to(
            message,
            "Channel/Group link received.\n\n"
            "Your order is now being processed. You will be notified when completed."
        )
    
    def _notify_user_payment_verified(self, order: dict):
        """Notify user that payment has been verified."""
        try:
            text = (
                "Payment Verified\n\n"
                "Your payment has been confirmed. "
                "Please send the channel or group invite link where you want boosts delivered.\n\n"
                "Send a link in this format:\n"
                "https://t.me/channel/group"
            )
            
            self.bot.send_message(order['user_id'], text)
        except Exception as e:
            logger.error(f"Failed to notify user {order['user_id']}: {e}")
    
    def _notify_user_order_completed(self, order: dict):
        """Notify user that order has been completed."""
        try:
            text = (
                "Order Completed\n\n"
                "Your boosts have been delivered successfully.\n\n"
                "Thank you for choosing our service!"
            )
            
            self.bot.send_message(order['user_id'], text)
        except Exception as e:
            logger.error(f"Failed to notify user {order['user_id']}: {e}")
    
    def _notify_user_order_rejected(self, order: dict):
        """Notify user that order has been rejected."""
        try:
            text = (
                "Payment Rejected\n\n"
                "Your payment could not be verified. "
                "Please contact support for assistance."
            )
            
            self.bot.send_message(order['user_id'], text)
        except Exception as e:
            logger.error(f"Failed to notify user {order['user_id']}: {e}")
    
    def _notify_admin_new_order(self, order_id: int):
        """Notify admin about new order with target link."""
        try:
            order = self.db.get_order(order_id)
            if not order:
                return
            
            text = (
                "New Order\n\n"
                f"Order ID: #{order_id:05d}\n"
                f"User: @{order['username'] or 'N/A'}\n"
                f"User ID: {order['user_id']}\n"
                f"Quantity: {order['quantity']} Boosts\n"
                f"Target: {order['target_link']}\n"
                f"Status: {order['status']}"
            )
            
            self.bot.send_message(Config.ADMIN_ID, text)
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")
