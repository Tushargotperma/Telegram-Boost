from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Optional

class InlineKeyboards:
    """Factory for creating inline keyboards."""
    
    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """Main menu keyboard."""
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton('Purchase Boosts', callback_data='purchase_boosts'),
            InlineKeyboardButton('Order Status', callback_data='order_status'),
            InlineKeyboardButton('Support', callback_data='support')
        )
        return keyboard
    
    @staticmethod
    def boost_quantities() -> InlineKeyboardMarkup:
        """Boost quantity selection keyboard."""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        buttons = [
            InlineKeyboardButton(f'{qty} Boosts', callback_data=f'qty_{qty}')
            for qty in [4, 8, 12, 50, 70]
        ]
        keyboard.add(*buttons)
        keyboard.add(
            InlineKeyboardButton('Custom Quantity', callback_data='custom_quantity'),
            InlineKeyboardButton('Main Menu', callback_data='main_menu')
        )
        return keyboard
    
    @staticmethod
    def order_summary(order_id: int) -> InlineKeyboardMarkup:
        """Order summary keyboard with payment actions."""
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton('Confirm Payment', callback_data=f'paid_{order_id}'),
            InlineKeyboardButton('Support', callback_data='support'),
            InlineKeyboardButton('Cancel Order', callback_data=f'cancel_{order_id}')
        )
        return keyboard
    
    @staticmethod
    def pending_payment(order_id: int, support_username: str) -> InlineKeyboardMarkup:
        """Pending payment verification keyboard."""
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton('Contact Support', url=f'https://t.me/{support_username}'),
            InlineKeyboardButton('Check Status', callback_data=f'check_{order_id}'),
            InlineKeyboardButton('Main Menu', callback_data='main_menu')
        )
        return keyboard
    
    @staticmethod
    def force_join(channel_username: str) -> InlineKeyboardMarkup:
        """Force join channel keyboard."""
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton('Join Channel', url=f'https://t.me/{channel_username}'),
            InlineKeyboardButton('Verify', callback_data='verify_join')
        )
        return keyboard
    
    @staticmethod
    def order_status() -> InlineKeyboardMarkup:
        """Order status navigation keyboard."""
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton('Main Menu', callback_data='main_menu'),
            InlineKeyboardButton('Contact Support', callback_data='support')
        )
        return keyboard
    
    @staticmethod
    def support() -> InlineKeyboardMarkup:
        """Support keyboard."""
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton('Main Menu', callback_data='main_menu')
        )
        return keyboard
    
    @staticmethod
    def admin_order_actions(order_id: int) -> InlineKeyboardMarkup:
        """Admin order management keyboard."""
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton('Confirm Payment', callback_data=f'admin_confirm_{order_id}'),
            InlineKeyboardButton('Reject Payment', callback_data=f'admin_reject_{order_id}')
        )
        return keyboard
