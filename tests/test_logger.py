import unittest
import logging
from unittest.mock import patch, MagicMock
import os
from utils.logger import setup_logger

class TestLogger(unittest.TestCase):
    @patch('utils.logger.os.makedirs')
    @patch('utils.logger.RotatingFileHandler')
    def test_setup_logger(self, mock_handler, mock_makedirs):
        mock_logger = MagicMock()
        with patch('utils.logger.logging.getLogger') as mock_get_logger:
            mock_get_logger.return_value = mock_logger
            logger = setup_logger('test_logger', 'test.log', level=logging.DEBUG)
            mock_makedirs.assert_called_once_with(os.path.dirname('test.log'))
            mock_handler.assert_called_once_with('test.log', maxBytes=1000000, backupCount=5)
            mock_logger.setLevel.assert_called_once_with(logging.DEBUG)
            mock_logger.addHandler.assert_called_once()
            self.assertEqual(logger, mock_logger)

    @patch('utils.logger.RotatingFileHandler')
    @patch('utils.logger.logging.getLogger')
    def test_setup_logger_directory_exists(self, mock_get_logger, mock_handler):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        with patch('utils.logger.os.path.exists', return_value=True):
            with patch('utils.logger.os.makedirs') as mock_makedirs:
                logger = setup_logger('test', 'existing/dir/log.log')
                mock_makedirs.assert_not_called()
                mock_handler.assert_called_once_with('existing/dir/log.log', maxBytes=1000000, backupCount=5)
                mock_logger.addHandler.assert_called_once()
                self.assertEqual(logger, mock_logger)

if __name__ == '__main__':
    unittest.main()