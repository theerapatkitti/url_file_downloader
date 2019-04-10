import threading
import time
import urllib.parse
import requests
import ftplib
import paramiko
from utils.filemanager import FileManager
from utils.exception import NoDestinationPathException, NoURLException, UnsupportedProtocolException
import errno

class Worker(threading.Thread):
    """
    Worker is a thread to download files in parallel. 
    Each worker take a work from a Queue to download file using given URL to specify destination.
    Support HTTP, HTTPS, FTP, FTPS, and SFTP protocol.
    """
    def __init__(self, config, works, progresses, test_net=False, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None):
        super(Worker, self).__init__()
        self.target = target
        self.name = name
        # Config
        self.config = config
        # Queue containing works to do
        self.works = works
        # Queue to report progress and work done
        self.progresses = progresses
        # Dict to contain progress for report
        self.progress = {}
        # Current work being process
        self.i = None
        
        # Only use for emulating fail download
        self.test_net = test_net

    def run(self):
        while not self.works.empty():
            # Get work
            work = self.works.get()
            info = work[1]
            self.i = work[0]
            self.progress = {}
            
            try:
                url = info.get("url")
                directory = info.get("dest")
                
                if not url:
                    raise NoURLException("file {} does not have url".format(self.i))
                if not directory:
                    raise NoDestinationPathException("file {} does not have dest".format(self.i))
                
                # Get filename and protocol from url
                split = urllib.parse.urlparse(url)
                protocol = split.scheme
                filename = FileManager.get_basename(split.path)
                
                # Create directory if the directory does not exist
                # Check whether directory has write permission
                if FileManager.is_path_creatable(directory):
                    FileManager.create_directory(directory)
                else:
                    import os
                    raise OSError(errno.EACCES, os.strerror(errno.EACCES), directory)
                
                # Download file with random filename to prevent overwritten file with same name
                filepath = FileManager.random_filepath(directory)

                self.progress["filepath"] = filepath
                self.progress["filename"] = filename
                
                if protocol in ["http", "https"]:
                    self.http_download(url, filepath)
                elif protocol in ["ftp", "ftps"]:
                    self.ftp_download(split, filepath)
                elif protocol in ["sftp"]:
                    self.sftp_download(split, info.get("key_filename"), info.get("passphrase"), filepath)
                else:
                    raise UnsupportedProtocolException("file {}({}) uses unsupported protocol".format(self.i, filename))
                
            except Exception as e:
                # Notify failed work
                self.progress["state"] = "Failed"
                self.progress["error"] = e
                self.progresses.put((self.i, self.progress.copy()))

            self.works.task_done()
            
            time.sleep(self.config.get("wait_task", 3))
            
        return
    
    def http_download(self, url, dest):
        """
        Download file using http and https protocol.

        url: url string of wanted file
        dest: destination path
        """
        # Retry loop if exception occur
        for i in range(self.config.get("max_retry", 3)):         
            try:
                with requests.get(url, stream=True, timeout=self.config.get("timeout", 10)) as r:
                    r.raise_for_status()
                    with open(dest, 'wb') as f:
                        # Download file in small chunk to prevent out of memory
                        for chunk in r.iter_content(chunk_size=self.config.get("chunk_size", 8192)): 
                            if chunk:
                                f.write(chunk)
                            # Use for unit testing to emulate fail download
                            # Can ignore
                            if self.test_net:
                                raise Exception("Testing fail download")
                
                # Rename file to correct filename
                self.rename_file(dest)
                break
                
            except requests.exceptions.HTTPError as errh:
                self.progress["error"] = errh
            except requests.exceptions.ConnectionError as errc:
                self.progress["error"] = errc
            except requests.exceptions.Timeout as errt:
                self.progress["error"] = errt
            except requests.exceptions.RequestException as err:
                self.progress["error"] = err
            except Exception as err:
                self.progress["error"] = err
                
            time.sleep(self.config.get("wait_retry", 5))
            
        else:   
            # Remove partial file
            self.remove_incomplete(dest)
    
    def ftp_download(self, url, dest):  
        """
        Download file using ftp and ftps protocol.

        url: ParseResult of url from urllib.parse.urlparse
        dest: destination path
        """         
        def callback(chunk):
            """
            Callback function which will be called from ftp.retrbinary().
            """
            if chunk:
                f.write(chunk)
            # Use for unit testing to emulate fail download
            # Can ignore
            if self.test_net:
                raise Exception("Testing fail download")

        # Retry loop if exception occur
        for i in range(self.config.get("max_retry", 3)):
            try:
                with ftplib.FTP(timeout=self.config.get("timeout", 10)) if url.scheme == "ftp" else ftplib.FTP_TLS(timeout=self.config.get("timeout", 10)) as ftp:
                    # Support url in scheme (ftps)ftp://username:password@hostname:port/path
                    ftp.connect(url.hostname, url.port if url.port else 21)
                    ftp.login(url.username, url.password)
                    with open(dest, 'wb') as f:
                        # Download file in small chunk to prevent out of memory
                        ftp.retrbinary("RETR {}".format(url.path), callback, blocksize=self.config.get("chunk_size", 8192))
                
                # Rename file to correct filename
                self.rename_file(dest)
                break

            except ftplib.error_reply as errr:
                self.progress["error"] = errr
            except ftplib.error_temp as errt:
                self.progress["error"] = errt
            except ftplib.error_perm as errp:
                self.progress["error"] = errp
            except ftplib.error_proto as errpr:
                self.progress["error"] = errpr
            except OSError as erro:
                self.progress["error"] = erro
            except Exception as err:
                self.progress["error"] = err
            
            time.sleep(self.config.get("wait_retry", 5))
            
        else:   
            # Remove partial file
            self.remove_incomplete(dest)
    
    def sftp_download(self, url, key_filename, passphrase, dest):     
        """
        Download file using sftp protocol.

        url: ParseResult of url from urllib.parse.urlparse
        key: path to private key file for authentication
        passphrase: Used for decrypting private key
        dest: destination path
        """       
        def callback(data, total):
            """
            Callback function which will be called from sftp.get().
            """
            # Use for unit testing to emulate fail download
            # Can ignore
            if self.test_net:
                raise Exception("Testing fail download")

        # Retry loop if exception occur
        for i in range(self.config.get("max_retry", 3)):
            try:
                with paramiko.SSHClient() as ssh:
                    # Support url in scheme sftp://username:password@hostname:port/path
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) 
                    ssh.connect(url.hostname, url.port if url.port else 22, url.username, url.password, 
                                key_filename=key_filename, passphrase=passphrase, timeout=self.config.get("timeout", 10))
                    with ssh.open_sftp() as sftp:
                        # Download file in small chunk to prevent out of memory
                        # This is done in the method
                        sftp.get(url.path, dest, callback)

                # Rename file to correct filename    
                self.rename_file(dest)
                break
            
            except paramiko.ssh_exception.ChannelException as errc:
                self.progress["error"] = errc
            except paramiko.ssh_exception.NoValidConnectionsError as errnc:
                self.progress["error"] = errnc
            except paramiko.ssh_exception.PasswordRequiredException as errp:
                self.progress["error"] = errp
            except paramiko.ssh_exception.PartialAuthentication as errpa:
                self.progress["error"] = errpa
            except paramiko.ssh_exception.BadHostKeyException as errbh:
                self.progress["error"] = errbh
            except paramiko.ssh_exception.BadAuthenticationType as errba:
                self.progress["error"] = errba
            except paramiko.ssh_exception.AuthenticationException as erra:
                self.progress["error"] = erra
            except paramiko.ssh_exception.SSHException as errs:
                self.progress["error"] = errs
            except OSError as erro:
                self.progress["error"] = erro
            except Exception as err:
                self.progress["error"] = err
            
            time.sleep(self.config.get("wait_retry", 5))
            
        else:   
            # Remove partial file
            self.remove_incomplete(dest)

    def rename_file(self, dest):
        """
        Rename downloaded file from random name to name identified in url.
        Filename will have incremental number at the front if filename exist.

        dest: destination path
        """
        filename = self.progress.get("filename")
        dirname = FileManager.get_dirname(dest)

        # Get filename to rename the file
        # Increment number at the front of filename if filename exist
        new_dest = FileManager.join_path(dirname, filename)
        if FileManager.is_path_exists(new_dest):
            new_dest = FileManager.generate_filepath(new_dest)

        FileManager.rename_file(dest, new_dest)

        # Notify success work
        self.progress["filename"] = FileManager.get_basename(new_dest)
        self.progress["state"] = "Success"
        self.progresses.put((self.i, self.progress.copy()))
    
    def remove_incomplete(self, dest):
        """
        Remove partial file.

        dest: destination path
        """
        # Notify failed work
        self.progress["state"] = "Failed"
        self.progresses.put((self.i, self.progress.copy()))
        
        # Retry loop if file cannot be removed
        for i in range(self.config.get("max_retry", 3)):   
            try:
                FileManager.remove_file(dest)
                break
            except:
                time.sleep(3)