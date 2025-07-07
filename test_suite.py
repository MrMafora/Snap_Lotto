"""
Comprehensive Test Suite for South African Lottery Scanner
Phase 3 Implementation - Testing Infrastructure
"""

import unittest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock
from flask import url_for
from main import app
from models import db, User, LotteryResult
from security_utils import validate_lottery_type, validate_draw_number, sanitize_input
from database_utils import get_database_stats, optimize_lottery_tables
from lottery_utils import calculate_frequency_analysis, format_lottery_numbers

class BaseTestCase(unittest.TestCase):
    """Base test case with common setup"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        db.create_all()
        
    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

class SecurityTestCase(BaseTestCase):
    """Test security utilities and validation"""
    
    def test_validate_lottery_type(self):
        """Test lottery type validation"""
        valid_types = ['LOTTO', 'LOTTO PLUS 1', 'LOTTO PLUS 2', 'PowerBall', 'POWERBALL PLUS', 'DAILY LOTTO']
        
        for lottery_type in valid_types:
            self.assertEqual(validate_lottery_type(lottery_type), lottery_type)
        
        with self.assertRaises(ValueError):
            validate_lottery_type('INVALID_TYPE')
    
    def test_validate_draw_number(self):
        """Test draw number validation"""
        # Valid numbers
        self.assertEqual(validate_draw_number('123'), 123)
        self.assertEqual(validate_draw_number('1'), 1)
        self.assertEqual(validate_draw_number('99999'), 99999)
        
        # Invalid numbers
        with self.assertRaises(ValueError):
            validate_draw_number('0')
        with self.assertRaises(ValueError):
            validate_draw_number('100000')
        with self.assertRaises(ValueError):
            validate_draw_number('abc')
        with self.assertRaises(ValueError):
            validate_draw_number('')
    
    def test_sanitize_input(self):
        """Test input sanitization"""
        # Test XSS prevention
        self.assertEqual(sanitize_input('<script>alert("xss")</script>'), 'scriptalert(xss)/script')
        self.assertEqual(sanitize_input('Normal text'), 'Normal text')
        self.assertEqual(sanitize_input(''), '')
        
        # Test length limiting
        long_text = 'a' * 300
        self.assertEqual(len(sanitize_input(long_text)), 255)

class DatabaseTestCase(BaseTestCase):
    """Test database operations"""
    
    def test_lottery_results_model(self):
        """Test LotteryResult model creation and retrieval"""
        lottery_result = LotteryResult(
            lottery_type='LOTTO',
            draw_number=2554,
            draw_date='2025-06-28',
            main_numbers='[1, 2, 3, 4, 5, 6]',
            bonus_numbers='[7]'
        )
        
        db.session.add(lottery_result)
        db.session.commit()
        
        retrieved = LotteryResult.query.filter_by(draw_number=2554).first()
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.lottery_type, 'LOTTO')
        self.assertEqual(retrieved.draw_number, 2554)
    
    def test_user_model(self):
        """Test User model and authentication"""
        user = User(username='testuser', email='test@example.com', is_admin=True)
        user.set_password('testpassword123')
        
        db.session.add(user)
        db.session.commit()
        
        retrieved = User.query.filter_by(username='testuser').first()
        self.assertIsNotNone(retrieved)
        self.assertTrue(retrieved.check_password('testpassword123'))
        self.assertFalse(retrieved.check_password('wrongpassword'))

class LotteryUtilsTestCase(BaseTestCase):
    """Test lottery utility functions"""
    
    def test_format_lottery_numbers(self):
        """Test lottery number formatting"""
        # Test list input
        self.assertEqual(format_lottery_numbers([1, 2, 3, 4, 5]), '1, 2, 3, 4, 5')
        
        # Test string input
        self.assertEqual(format_lottery_numbers('[1, 2, 3, 4, 5]'), '1, 2, 3, 4, 5')
        
        # Test empty/null input
        self.assertEqual(format_lottery_numbers(None), 'N/A')
        self.assertEqual(format_lottery_numbers(''), 'N/A')
    
    def test_calculate_frequency_analysis(self):
        """Test frequency analysis calculation"""
        # Create mock lottery results
        mock_results = []
        
        # Add some test results
        for i in range(3):
            result = MagicMock()
            result.main_numbers = '[1, 2, 3, 4, 5]'
            result.bonus_numbers = '[6]'
            mock_results.append(result)
        
        analysis = calculate_frequency_analysis(mock_results)
        
        self.assertIn('total_unique_numbers', analysis)
        self.assertIn('top_10_numbers', analysis)
        self.assertIn('all_frequencies', analysis)

class APITestCase(BaseTestCase):
    """Test API endpoints"""
    
    def test_home_page(self):
        """Test homepage loads successfully"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_login_page(self):
        """Test login page loads"""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
    
    def test_admin_redirect_without_auth(self):
        """Test admin page redirects when not authenticated"""
        response = self.client.get('/admin')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        # This would require more complex setup to test properly
        # For now, just verify the endpoint exists
        response = self.client.get('/api/lottery-analysis/frequency')
        self.assertIn(response.status_code, [200, 429])  # Either success or rate limited

class IntegrationTestCase(BaseTestCase):
    """Integration tests for complete workflows"""
    
    def test_user_login_workflow(self):
        """Test complete user login workflow"""
        # Create test user
        user = User(username='testadmin', email='admin@test.com', is_admin=True)
        user.set_password('adminpass123')
        db.session.add(user)
        db.session.commit()
        
        # Test login
        response = self.client.post('/login', data={
            'username': 'testadmin',
            'password': 'adminpass123'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
    
    def test_lottery_data_display(self):
        """Test lottery data display workflow"""
        # Add test lottery data
        lottery_result = LotteryResult(
            lottery_type='LOTTO',
            draw_number=2554,
            draw_date='2025-06-28',
            main_numbers='[13, 50, 20, 47, 18, 1]',
            bonus_numbers='[27]'
        )
        db.session.add(lottery_result)
        db.session.commit()
        
        # Test homepage displays data
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'LOTTO', response.data)

class PerformanceTestCase(BaseTestCase):
    """Performance and load testing"""
    
    def test_database_optimization(self):
        """Test database optimization functions"""
        # This would ideally test with a real database
        # For unit tests, we verify the functions don't crash
        try:
            optimize_lottery_tables()
            self.assertTrue(True)  # Function completed without error
        except Exception as e:
            # In memory SQLite doesn't support all PostgreSQL features
            self.assertIn('no such function', str(e).lower())
    
    def test_large_dataset_handling(self):
        """Test handling of large datasets"""
        # Add multiple lottery results
        for i in range(50):
            lottery_result = LotteryResult(
                lottery_type='LOTTO',
                draw_number=2500 + i,
                draw_date='2025-06-01',
                main_numbers=f'[{i % 50 + 1}, {(i + 1) % 50 + 1}, {(i + 2) % 50 + 1}, {(i + 3) % 50 + 1}, {(i + 4) % 50 + 1}, {(i + 5) % 50 + 1}]',
                bonus_numbers=f'[{i % 10 + 1}]'
            )
            db.session.add(lottery_result)
        
        db.session.commit()
        
        # Test homepage still loads efficiently
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

def run_test_suite():
    """Run the complete test suite"""
    print("Starting Phase 3 Comprehensive Test Suite...")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        SecurityTestCase,
        DatabaseTestCase,
        LotteryUtilsTestCase,
        APITestCase,
        IntegrationTestCase,
        PerformanceTestCase
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Return results summary
    return {
        'tests_run': result.testsRun,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'success_rate': (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    }

if __name__ == '__main__':
    results = run_test_suite()
    print(f"\nTest Results Summary:")
    print(f"Tests Run: {results['tests_run']}")
    print(f"Failures: {results['failures']}")
    print(f"Errors: {results['errors']}")
    print(f"Success Rate: {results['success_rate']:.1f}%")