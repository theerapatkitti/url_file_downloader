import unittest
import os
import sys
import hashlib
from queue import Queue

ROOT_DIR = os.path.abspath("../")
sys.path.append(ROOT_DIR)

from utils.visualizer import Visualizer
from utils.filemanager import FileManager
from utils.worker import Worker

test_dest = "./test_download"

test_urls = {
    "http_small": {
        "url": "http://speedtest.tele2.net/1MB.zip",
        "path": os.path.join(test_dest, "1MB.zip"),
        "md5": "b6d81b360a5672d80c27430f39153e2c"
    },
    "ftp_small": {
        "url": "ftp://speedtest.tele2.net/1KB.zip",
        "path": os.path.join(test_dest, "1KB.zip"),
        "md5": "0f343b0931126a20f133d67c2b018a3b"
    },
    # ftps and sftp uses my computer as a source
    # change it to any source you want
    "ftps_small": {
        "url": "ftps://XXX:XXXX@localhost:21/path",
        "path": os.path.join(test_dest, "ftps_1KB.zip"),
        "md5": "0f343b0931126a20f133d67c2b018a3b"
    },
    "sftp_small": {
        "url": "sftp://XXXX:XXXX@localhost:22/path",
        "path": os.path.join(test_dest, "sftp_1KB.zip"),
        "md5": "0f343b0931126a20f133d67c2b018a3b"
    },
}

class TestIntegration(unittest.TestCase):

    def test_success_download(self):
        works = Queue(maxsize=0)
        progresses = Queue(maxsize=0)

        for i, key in enumerate(test_urls):
            works.put((i + 1, {"url": test_urls[key]["url"], "dest": test_dest}))

        for i in range(4):
            worker = Worker({"wait_task": 1, "wait_retry": 0, "max_retry": 1}, works, progresses, name="worker{}".format(i))
            worker.setDaemon(True)
            worker.start()

        visualizer = Visualizer(4, progresses, name="visualizer")
        visualizer.start()

        works.join()
        visualizer.join()
        
        self.assertTrue(works.empty())
        self.assertTrue(progresses.empty())
        self.assertEqual(visualizer.success, 4)
        self.assertEqual(visualizer.success, visualizer.task)
        self.assertTrue(not visualizer.results)
        for key in test_urls:
            self.assertTrue(os.path.exists(test_urls[key]["path"]))
            with open(test_urls[key]["path"], "rb") as f:
                data = f.read() 
                self.assertEqual(hashlib.md5(data).hexdigest(), test_urls[key]["md5"])

            FileManager.remove_file(test_urls[key]["path"])
    
    def test_fail_download(self):
        works = Queue(maxsize=0)
        progresses = Queue(maxsize=0)

        for i, key in enumerate(test_urls):
            works.put((i + 1, {"url": test_urls[key]["url"], "dest": test_dest}))

        for i in range(4):
            worker = Worker({"wait_task": 1, "wait_retry": 0, "max_retry": 1}, works, progresses, test_net=True, name="worker{}".format(i))
            worker.setDaemon(True)
            worker.start()

        visualizer = Visualizer(4, progresses, name="visualizer")
        visualizer.start()

        works.join()
        visualizer.join()
        
        self.assertTrue(works.empty())
        self.assertTrue(progresses.empty())
        self.assertEqual(visualizer.fail, 4)
        self.assertEqual(visualizer.fail, visualizer.task)
        self.assertEqual(len(visualizer.results), 4)
        self.assertTrue(len(os.listdir(test_dest)) == 0)

if __name__ == "__main__":
    unittest.main()