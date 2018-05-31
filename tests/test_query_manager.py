from intermine import query_manager as qm

import unittest
qm.save_mine_and_token('flymine','k136n1HfFd31n6O4han1')

class QueryManagerTest(unittest.TestCase):
    def test_save_mine_and_token(self):
        #Function returns none if there is no error
        self.assertIsNone(qm.save_mine_and_token('flymine','k136n1HfFd31n6O4han1'))

    def test_get_all_query_names(self):
        #Function returns none if there is no error
        self.assertIsNone(qm.get_all_query_names())

    def test_get_query(self):
        #to delete any existing query named 'yyy' if existing previously
        qm.delete_query('yyy')
        #posting a query named 'yyy'
        qm.post_query('<query name="yyy" model="genomic" view="Gene.secondaryIdentifier Gene.symbol Gene.pathways.identifier " sortOrder="Gene.secondaryIdentifier ASC" >  <constraint path="Gene" op="LOOKUP" value="bsk" extraValue="D. melanogaster" code="A" /> </query>')
        #Function returns none if the query exists in user account
        self.assertEqual(qm.get_query('yyy'), None)
        #Function returns a message if query doesn't exists in user account
        self.assertEqual(qm.get_query('xxx'), "No such query available")
        #deletes the query 'yyy' we created to return to original state
        qm.delete_query('yyy')

    def test_delete_query(self):
        #to delete any existing query named 'xx' if existing previously
        qm.delete_query('xx')
        #posting a query named 'xx'
        qm.post_query('<query name="xx" model="genomic" view="Gene.secondaryIdentifier Gene.symbol Gene.pathways.identifier " sortOrder="Gene.secondaryIdentifier ASC" >  <constraint path="Gene" op="LOOKUP" value="bsk" extraValue="D. melanogaster" code="A" /> </query>')
        #deletes a query 'xx' if it exists and returns a message
        self.assertEqual(qm.delete_query('xx'), "xx is deleted")
        #returns a message if query doesn't exists in user account
        self.assertEqual(qm.delete_query('xxx'), "No such query available")

    def test_post_query(self):
        #to delete any existing query named 'xx' if existing previously
        qm.delete_query('xx')
        #posts a query and if xml is right, returns a message
        self.assertEqual(qm.post_query('<query name="xx" model="genomic" view="Gene.secondaryIdentifier Gene.symbol Gene.pathways.identifier " sortOrder="Gene.secondaryIdentifier ASC" >  <constraint path="Gene" op="LOOKUP" value="bsk" extraValue="D. melanogaster" code="A" /> </query>'),'xx is posted')
        #deletes the query 'xx' we created to return to original state
        qm.delete_query('xx')
        #can't post if xml is wrong and retrurns a message
        self.assertEqual(qm.post_query('<query name="xxy" model="gnomic" view="Gene.secondaryIdentifier Gene.symbol Gene.pathways.identifier " sortOrder="Gene.secondaryIdentifier ASC" >  <constraint path="Gene" op="LOOKUP" value="bsk" extraValue="D. melanogaster" code="A" /> </query>'),"Incorrect xml")

if __name__ == '__main__':
    unittest.main()
