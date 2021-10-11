import time
import unittest
from unittest.mock import patch, MagicMock
from lora_multihop import serial_connection

__author__ = "Marvin Rausch"


class SerialConnectionTest(unittest.TestCase):

    def setUp(self) -> None:
        self.ser = MagicMock()
        serial_connection.ser = self.ser

    def test_verify_command_good(self):
        with patch.object(time, 'sleep', side_effect=InterruptedError):
            serial_connection.writing_q.put(('AT', ['OK']))
            self.ser.readline.return_value = serial_connection.str_to_bytes('OK')
            try:
                serial_connection.WritingThread('test_receiving').run()
            except InterruptedError:
                self.assertFalse(serial_connection.status_q.empty())
                self.assertTrue(serial_connection.status_q.get())

    def test_verify_command_bad(self):
        with patch.object(time, 'sleep', side_effect=InterruptedError):
            serial_connection.writing_q.put(('AT', ['OK']))
            self.ser.readline.side_effect = [serial_connection.str_to_bytes('LR'), serial_connection.str_to_bytes('OK')]
            try:
                serial_connection.WritingThread('test_receiving').run()
            except InterruptedError:
                self.assertFalse(serial_connection.status_q.empty())
                self.assertTrue(serial_connection.status_q.get())

    def test_verify_command_bad2(self):
        with patch.object(time, 'sleep', side_effect=InterruptedError):
            serial_connection.writing_q.put(('AT', ['SENDING', 'SENDED']))
            self.ser.readline.side_effect = [serial_connection.str_to_bytes('SENDING'),
                                             serial_connection.str_to_bytes('LR'),
                                             serial_connection.str_to_bytes('SENDED')]
            try:
                serial_connection.WritingThread('test_receiving').run()
            except InterruptedError:
                self.assertFalse(serial_connection.status_q.empty())
                self.assertTrue(serial_connection.status_q.get())
                self.assertEqual(3, self.ser.readline.call_count)  # make sure UART query was cleared

    def test_verify_command_bad_to_many_commands_expected_for_verification(self):
        with patch.object(time, 'sleep', side_effect=InterruptedError):
            serial_connection.writing_q.put(('AT', ['SENDING', 'SENDED']))
            # '' would be returned from ser.readline if timeout is reached
            self.ser.readline.side_effect = [serial_connection.str_to_bytes('SENDED'),
                                             serial_connection.str_to_bytes('')]
            try:
                serial_connection.WritingThread('test_receiving').run()
            except InterruptedError:
                self.assertFalse(serial_connection.status_q.empty())
                self.assertFalse(serial_connection.status_q.get())
                self.assertEqual(2, self.ser.readline.call_count)  # make sure UART query was cleared
