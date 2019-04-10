import unittest
import os
import sys
import random
import hashlib
import requests
from queue import Queue

ROOT_DIR = os.path.abspath("../")
sys.path.append(ROOT_DIR)

from utils.filemanager import FileManager
from utils.worker import Worker
from utils.exception import NoDestinationPathException, NoURLException, UnsupportedProtocolException

test_dest = "./test_download"

test_urls = {
    "http_small": {
        "url": "http://speedtest.tele2.net/1MB.zip",
        "path": os.path.join(test_dest, "1MB.zip"),
        "md5": "b6d81b360a5672d80c27430f39153e2c"
    },
    "http_medium": {
        "url": "http://speedtest.tele2.net/10MB.zip",
        "path": os.path.join(test_dest, "10MB.zip"),
        "md5": "f1c9645dbc14efddc7d8a322685f26eb"
    },
    "ftp_small": {
        "url": "ftp://speedtest.tele2.net/1KB.zip",
        "path": os.path.join(test_dest, "1KB.zip"),
        "md5": "0f343b0931126a20f133d67c2b018a3b"
    },
    "ftp_medium": {
        "url": "ftp://speedtest.tele2.net/20MB.zip",
        "path": os.path.join(test_dest, "20MB.zip"),
        "md5": "8f4e33f3dc3e414ff94e5fb6905cba8c"
    },
    # ftps and sftp uses my computer as a source
    # change it to any source you want
    "ftps_small": {
        "url": "ftps://XXXX:XXXX@localhost:21/test_file/ftps_1KB.zip",
        "path": os.path.join(test_dest, "ftps_1KB.zip"),
        "md5": "0f343b0931126a20f133d67c2b018a3b"
    },
    "sftp_small": {
        "url": "sftp://XXXX:XXXXX@localhost:22/path",
        "path": os.path.join(test_dest, "sftp_1KB.zip"),
        "md5": "0f343b0931126a20f133d67c2b018a3b"
    },
    "sftp_pkey_small": {
        "url": "sftp://XXXX:XXXXX@localhost:22/path",
        "path": os.path.join(test_dest, "sftp_pkey_1KB.zip"),
        "key_filename": "/.ssh/pkey",
        "passphrase": "pass",
        "md5": "0f343b0931126a20f133d67c2b018a3b"
    },
}

class TestWorker(unittest.TestCase):
    
    def test_no_url(self):
        q = Queue()
        q2 = Queue()
        q.put((0, {}))
        q.put((1, {"url": ""}))

        worker = Worker({"wait_task": 0}, q, q2)
        worker.start()
        worker.join()

        self.assertTrue(q.empty())
        self.assertIsInstance(q2.get()[1]["error"], NoURLException)
        self.assertIsInstance(q2.get()[1]["error"], NoURLException)
    
    def test_no_dest(self):
        q = Queue()
        q2 = Queue()
        q.put((0, {"url": "url"}))
        q.put((1, {"url": "url", "dest": ""}))

        worker = Worker({"wait_task": 0}, q, q2)
        worker.start()
        worker.join()

        self.assertTrue(q.empty())
        self.assertIsInstance(q2.get()[1]["error"], NoDestinationPathException)
        self.assertIsInstance(q2.get()[1]["error"], NoDestinationPathException)

    def test_unsupport_protocol(self):
        q = Queue()
        q2 = Queue()
        q.put((0, {"url": "url", "dest": test_dest}))
        q.put((1, {"url": "abc://path", "dest": test_dest}))

        worker = Worker({"wait_task": 0}, q, q2)
        worker.start()
        worker.join()

        self.assertTrue(q.empty())
        q2.get()
        self.assertIsInstance(q2.get()[1]["error"], UnsupportedProtocolException)
        q2.get()
        self.assertIsInstance(q2.get()[1]["error"], UnsupportedProtocolException)

    def test_http_download(self):        
        q = Queue()
        q2 = Queue()
        q.put((0, {"url": test_urls["http_small"]["url"], "dest": test_dest}))

        worker = Worker({"wait_task": 0}, q, q2)
        worker.start()
        worker.join()
        
        self.assertTrue(q.empty())
        self.assertTrue(os.path.exists(test_urls["http_small"]["path"]))
        with open(test_urls["http_small"]["path"], "rb") as f:
            data = f.read() 
            self.assertEqual(hashlib.md5(data).hexdigest(), test_urls["http_small"]["md5"])
        
        FileManager.remove_file(test_urls["http_small"]["path"])

    def test_ftp_download(self):
        q = Queue()
        q2 = Queue()
        q.put((0, {"url": test_urls["ftp_small"]["url"], "dest": test_dest}))
        q.put((1, {"url": test_urls["ftps_small"]["url"], "dest": test_dest}))

        worker = Worker({"wait_task": 0}, q, q2)
        worker.start()
        worker.join()

        self.assertTrue(q.empty())
        self.assertTrue(os.path.exists(test_urls["ftp_small"]["path"]))
        self.assertTrue(os.path.exists(test_urls["ftps_small"]["path"]))
        with open(test_urls["ftp_small"]["path"], "rb") as f:
            data = f.read() 
            self.assertEqual(hashlib.md5(data).hexdigest(), test_urls["ftp_small"]["md5"])
        with open(test_urls["ftps_small"]["path"], "rb") as f:
            data = f.read() 
            self.assertEqual(hashlib.md5(data).hexdigest(), test_urls["ftps_small"]["md5"])

        FileManager.remove_file(test_urls["ftp_small"]["path"])
        FileManager.remove_file(test_urls["ftps_small"]["path"])

    def test_sftp_download(self):
        q = Queue()
        q2 = Queue()
        
        q.put((0, {"url": test_urls["sftp_small"]["url"], "dest": test_dest}))
        q.put((1, {"url": test_urls["sftp_pkey_small"]["url"], "dest": test_dest, 
                    "key_filename": test_urls["sftp_pkey_small"]["key_filename"], 
                    "passphrase": test_urls["sftp_pkey_small"]["key_filename"]}))

        worker = Worker({"wait_task": 0}, q, q2)
        worker.start()
        worker.join()

        self.assertTrue(q.empty())
        self.assertTrue(os.path.exists(test_urls["sftp_small"]["path"]))
        self.assertTrue(os.path.exists(test_urls["sftp_pkey_small"]["path"]))
        with open(test_urls["sftp_small"]["path"], "rb") as f:
            data = f.read() 
            self.assertEqual(hashlib.md5(data).hexdigest(), test_urls["sftp_small"]["md5"])
        with open(test_urls["sftp_pkey_small"]["path"], "rb") as f:
            data = f.read() 
            self.assertEqual(hashlib.md5(data).hexdigest(), test_urls["sftp_pkey_small"]["md5"])
        
        FileManager.remove_file(test_urls["sftp_small"]["path"])
        FileManager.remove_file(test_urls["sftp_pkey_small"]["path"])
    
    def test_404_download(self):
        q = Queue()
        q2 = Queue()
        q.put((0, {"url": "http://google.com/blah", "dest": test_dest}))

        worker = Worker({"wait_task": 0, "wait_retry": 0}, q, q2)
        worker.start()
        worker.join()

        self.assertTrue(q.empty())
        q2.get()
        self.assertIsInstance(q2.get()[1]["error"], requests.exceptions.HTTPError)

    def test_fail_download(self):
        q = Queue()
        q2 = Queue()

        selects = {}

        for i in range(10):
            choice = random.choice(list(test_urls.keys()))
            if choice in selects.keys():
                selects[choice] += 1
            else:
                selects[choice] = 1

            q.put((i, {"url": test_urls[choice]["url"], "dest": test_dest}))
            
        worker = Worker({"wait_task": 1, "wait_retry": 0, "max_retry": 1}, q, q2, test_net=True)
        worker.start()
        worker.join()

        self.assertTrue(q.empty())
        self.assertTrue(len(os.listdir(test_dest)) == 0)

    def test_many_download(self):
        q = Queue()
        q2 = Queue()

        selects = {}

        for i in range(10):
            choice = random.choice(list(test_urls.keys()))
            if choice in selects.keys():
                selects[choice] += 1
            else:
                selects[choice] = 1

            q.put((i, {"url": test_urls[choice]["url"], "dest": test_dest}))
            
        worker = Worker({"wait_task": 1, "wait_retry": 0, "max_retry": 1}, q, q2)
        worker.start()
        worker.join()

        self.assertTrue(q.empty())
        for key, value in selects.items():
            path = test_urls[key]["path"]
            dirname = FileManager.get_dirname(path)
            basename = FileManager.get_basename(path)
            for i in range(value):
                filepath = os.path.join(dirname, "{}_{}".format(i, basename)) if i != 0 else path 
                self.assertTrue(os.path.exists(filepath))
                with open(filepath, "rb") as f:
                    data = f.read() 
                    self.assertEqual(hashlib.md5(data).hexdigest(), test_urls[key]["md5"])
                FileManager.remove_file(filepath)

if __name__ == "__main__":
    unittest.main()