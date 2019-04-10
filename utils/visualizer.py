import threading
import sys
import os
import time

class Visualizer(threading.Thread):
    """
    Visualizer is a thread to show download progress. 
    It does not involve in downloading a file and only take care of showing the progress.
    It will show files that are downloaded successfully, failed, and a progress bar showing number of files downloaded.
    At the end it will print number of success and fail, as well as a reason for failure.
    """
    def __init__(self, task, progresses, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None):
        super(Visualizer, self).__init__()
        self.target = target
        self.name = name
        # Number of work
        self.task = task
        # Number of success work
        self.success = 0
        # Number of fail work
        self.fail = 0
        # Queue to get progress report from workers
        self.progresses = progresses
        # Dict to hold fail work
        self.results = {}
    
    def run(self):
        while self.task != self.success + self.fail:
            if not self.progresses.empty():
                progress = self.progresses.get()

                # If work success or failed, increment corresponding value
                if progress[1].get("state") == "Success":
                    self.success += 1
                else:
                    self.results[progress[0]] = progress[1]
                    self.fail += 1

                # Print result of file download
                print("\rDownloaded file {: <70}{: <20}".format("{}({})".format(progress[0], 
                progress[1].get("filename", "")), progress[1].get("state")))
                
                self.progresses.task_done()
            
                self.print_progress()
              
            time.sleep(0.5)
        
        sys.stdout.write('\n\n')
        
        self.print_results()
        
        return
    
    def print_progress(self):
        """
        Print progress bar showing number of file downloaded.
        """
        done = (self.success + self.fail)
        percent = int(50 * done / self.task)
        sys.stdout.write('\rDownloading [{}{}] {}/{}'.format('█' * percent, '.' * (50 - percent), done, self.task))
        sys.stdout.flush()
    
    def print_results(self):
        """
        Print final information.
        Showing number of success or failed work.
        As well as reason for failure.
        """
        print("\n{} Success, {} Failed".format(self.success, self.fail))
        print("\nFailed downloaded:")
        for i, info in self.results.items():
            print("file {}({})\t\t{}".format(i, info.get("filename", ""), info.get("error")))
        print('\nSee the reason for the error in the console.')