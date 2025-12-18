"""
Error handler for Flask app to log all errors
"""
import logging
import traceback
from flask import jsonify

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """Register error handlers for the Flask app"""
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        logger.error(f"Internal Server Error: {str(error)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal Server Error', 'message': str(error)}), 500
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        logger.warning(f"404 Not Found: {str(error)}")
        return jsonify({'error': 'Not Found'}), 404
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Handle all unhandled exceptions"""
        logger.error(f"Unhandled Exception: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500

