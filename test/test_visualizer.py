import unittest
import os
import sys
from queue import Queue

ROOT_DIR = os.path.abspath("../")
sys.path.append(ROOT_DIR)

from utils.visualizer import Visualizer

class TestVisualizer(unittest.TestCase):

    def test_success_progress(self):
        q = Queue()
        q.put((0, {"filename": "name", "filepath": "path", "state": "Success", "error": "error"}))

        v = Visualizer(1, q)
        v.start()
        v.join()
        
        self.assertTrue(q.empty())
        self.assertEqual(v.success, 1)
        self.assertEqual(v.success, v.task)
        self.assertTrue(not v.results)
    
    def test_fail_progress(self):
        q = Queue()
        q.put((0, {"filename": "name", "filepath": "path", "state": "Failed", "error": "error"}))

        v = Visualizer(1, q)
        v.start()
        v.join()
        
        self.assertTrue(q.empty())
        self.assertEqual(v.fail, 1)
        self.assertEqual(v.fail, v.task)
        self.assertEqual(len(v.results), 1)

if __name__ == "__main__":
    unittest.main()