import unittest
from client import create_presence, check_response
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, STATUS_CODE, STATUS


class TestClient(unittest.TestCase):

    def test_create_presence(self):
        test = create_presence()
        test[TIME] = '1.1'
        self.assertEqual(
            {ACTION: PRESENCE, TIME: '1.1', USER: {ACCOUNT_NAME: 'Guest'}}, test)

    def test_check_response_200(self):
        self.assertEqual(check_response({STATUS_CODE: 200, STATUS: 'OK'}), '200: OK')

    def test_check_response_400(self):
        self.assertEqual(check_response({STATUS_CODE: 400, STATUS: 'Bad Request'}), '400: Bad Request')


if __name__ == '__main__':
    unittest.main()
