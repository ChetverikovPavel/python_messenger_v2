import unittest
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, STATUS, STATUS_CODE
from server import message_status


class TestServer(unittest.TestCase):
    err_dict = {
        STATUS_CODE: 400,
        STATUS: 'Bad Request'
    }

    ok_dict = {
        STATUS_CODE: 200,
        STATUS: 'OK'
    }

    def test_correct_presence(self):
        self.assertEqual(message_status(
            {ACTION: PRESENCE, TIME: '1.1', USER: {ACCOUNT_NAME: 'Guest'}}), self.ok_dict)

    def test_no_action(self):
        self.assertEqual(message_status(
            {TIME: '1.1', USER: {ACCOUNT_NAME: 'Guest'}}), self.err_dict)

    def test_no_time(self):
        self.assertEqual(message_status(
            {ACTION: PRESENCE, USER: {ACCOUNT_NAME: 'Guest'}}), self.err_dict)

    def test_no_user(self):
        self.assertEqual(message_status(
            {ACTION: PRESENCE, TIME: '1.1'}), self.err_dict)

    def test_wrong_account_name(self):
        self.assertEqual(message_status(
            {ACTION: PRESENCE, TIME: '1.1', USER: {ACCOUNT_NAME: 'NotGuest'}}), self.err_dict)

    def test_wrong_action(self):
        self.assertEqual(message_status(
            {ACTION: 'wrongAction', TIME: '1.1', USER: {ACCOUNT_NAME: 'Guest'}}), self.err_dict)


if __name__ == '__main__':
    unittest.main()
