import unittest

from ..intermine import query_manager as qm
qm.save_mine_and_token('mock', 'x')


class QueryManagerTest(unittest.TestCase):

    def test_get_all_query_names(self):
        # Function returns none if there is no error and mine is nonempty
        self.assertEqual(qm.get_all_query_names(), 'query1, query2')

    def test_get_query(self):
        # Function returns none if the query exists in user account
        self.assertEqual(qm.get_query('query1'), 'c1, c2')
        # Function returns a message if query doesn't exists in user account
        self.assertEqual(qm.get_query('query3'), "No such query available")

    def test_delete_query(self):
        # deletes a query 'query1' if it exists and returns a message
        self.assertEqual(qm.delete_query('query1'), "query1 is deleted")
        # returns a message if query doesn't exists in user account
        self.assertEqual(qm.delete_query('query3'), "No such query available")

    def test_post_query(self):
        # posts a query if xml is right
        self.assertEqual(qm.post_query('<query name="query3"></query>'),
                                       "query3 is posted")
        # can't post if xml is wrong and returns a message
        self.assertEqual(qm.post_query('<query name="query4"></query>'),
                                       "Incorrect xml")


if __name__ == '__main__':
    unittest.main()
