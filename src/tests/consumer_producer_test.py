import time
import unittest
from unittest.mock import patch, MagicMock
from protocol import consumer_producer

__author__ = "Marvin Rausch"


class ConsumerProducerTest(unittest.TestCase):

    def setUp(self) -> None:
        self.ser = MagicMock()
        consumer_producer.ser = self.ser

    def test_verify_command_good(self):
        with patch.object(time, 'sleep', side_effect=InterruptedError):
            consumer_producer.q.put(('AT', ['OK']))
            self.ser.readline.return_value = consumer_producer.str_to_bytes('OK')
            try:
                consumer_producer.ConsumerThread('test_receiving').run()
            except InterruptedError:
                self.assertFalse(consumer_producer.status_q.empty())
                self.assertTrue(consumer_producer.status_q.get())

    def test_verify_command_bad(self):
        with patch.object(time, 'sleep', side_effect=InterruptedError):
            consumer_producer.q.put(('AT', ['OK']))
            self.ser.readline.side_effect = [consumer_producer.str_to_bytes('LR'), consumer_producer.str_to_bytes('OK')]
            try:
                consumer_producer.ConsumerThread('test_receiving').run()
            except InterruptedError:
                self.assertFalse(consumer_producer.status_q.empty())
                self.assertTrue(consumer_producer.status_q.get())

    def test_verify_command_bad2(self):
        with patch.object(time, 'sleep', side_effect=InterruptedError):
            consumer_producer.q.put(('AT', ['SENDING', 'SENDED']))
            self.ser.readline.side_effect = [consumer_producer.str_to_bytes('SENDING'),
                                             consumer_producer.str_to_bytes('LR'),
                                             consumer_producer.str_to_bytes('SENDED')]
            try:
                consumer_producer.ConsumerThread('test_receiving').run()
            except InterruptedError:
                self.assertFalse(consumer_producer.status_q.empty())
                self.assertTrue(consumer_producer.status_q.get())
                self.assertEqual(3, self.ser.readline.call_count)  # make sure UART query was cleared

    def test_verify_command_bad_to_many_commands_expected_for_verification(self):
        with patch.object(time, 'sleep', side_effect=InterruptedError):
            consumer_producer.q.put(('AT', ['SENDING', 'SENDED']))
            # '' would be returned from ser.readline if timeout is reached
            self.ser.readline.side_effect = [consumer_producer.str_to_bytes('SENDED'),
                                             consumer_producer.str_to_bytes('')]
            try:
                consumer_producer.ConsumerThread('test_receiving').run()
            except InterruptedError:
                self.assertFalse(consumer_producer.status_q.empty())
                self.assertFalse(consumer_producer.status_q.get())
                self.assertEqual(2, self.ser.readline.call_count)  # make sure UART query was cleared
