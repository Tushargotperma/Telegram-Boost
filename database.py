import sqlite3
import datetime
from typing import Optional, Dict, List, Any
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class Database:
    """Database handler for the bot."""
    
    def __init__(self, db_path: str = 'data/orders.db'):
        self.db_path = db_path
        self._initialize_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _initialize_database(self):
        """Create tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Orders table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    quantity INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    target_link TEXT,
                    status TEXT DEFAULT 'pending_payment',
                    payment_transaction_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at)')
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    def save_user(self, user_id: int, username: Optional[str] = None, 
                  first_name: Optional[str] = None, last_name: Optional[str] = None):
        """Save or update user information."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, last_activity)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, username, first_name, last_name))
            conn.commit()
    
    def create_order(self, user_id: int, username: str, quantity: int, amount: float) -> int:
        """Create a new order and return the order ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO orders (user_id, username, quantity, amount)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, quantity, amount))
            order_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Order #{order_id} created for user {user_id}")
            return order_id
    
    def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Get order details by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT order_id, user_id, username, quantity, amount, 
                       target_link, status, created_at, updated_at, completed_at
                FROM orders
                WHERE order_id = ?
            ''', (order_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_order_status(self, order_id: int, status: str):
        """Update order status with timestamp."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE orders
                SET status = ?, updated_at = CURRENT_TIMESTAMP,
                    completed_at = CASE WHEN ? IN ('completed', 'rejected') 
                                        THEN CURRENT_TIMESTAMP ELSE completed_at END
                WHERE order_id = ?
            ''', (status, status, order_id))
            conn.commit()
            logger.info(f"Order #{order_id} status updated to {status}")
    
    def update_order_target(self, order_id: int, target_link: str):
        """Update order with target link and change status to processing."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE orders
                SET target_link = ?, status = 'processing', updated_at = CURRENT_TIMESTAMP
                WHERE order_id = ?
            ''', (target_link, order_id))
            conn.commit()
            logger.info(f"Order #{order_id} target link set: {target_link}")
    
    def get_user_orders(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent orders for a user."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT order_id, quantity, amount, status, target_link, created_at
                FROM orders
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_orders_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get all orders with a specific status."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT order_id, user_id, username, quantity, amount, created_at
                FROM orders
                WHERE status = ?
                ORDER BY created_at ASC
            ''', (status,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_user_active_order(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Check if user has any active (non-completed) orders."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT order_id, status
                FROM orders
                WHERE user_id = ? AND status NOT IN ('completed', 'rejected')
                ORDER BY created_at DESC
                LIMIT 1
            ''', (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
