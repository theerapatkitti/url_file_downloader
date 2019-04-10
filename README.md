# URL File Downloader

The program will download files from different sources to a configurable location. The list of sources will be given as input in the form of URLs. The program supports following protocols: HTTP, HTTPS, FTP, FTPS, SFTP.

## Getting Started

### Prerequisites

* [Python 3.6](https://www.python.org/downloads/)

### Setup

Install python modules

```
pip install -r requirements.txt
```

## Usage

### Input

To use the program, create a yaml file listing wanted download files. The format of inputs yaml file should look like follows:

```
file1:
	url: <URL of wanted files>
	dest: <configurable destination location>
	key_filename: <path to private key for using public key authentication in sftp>
	passphrase: <to decrypt private key>
file2:
    ...
...
```

Only url and dest is required to be filled. key_filename and passphrase is only needed if using SFTP protocol and required public key authentication.

### Configuration

The program requires config yaml file to control different properties of the program. The format of config yaml can have the following configuration:

```
chunk_size: <size of chunk to read and save, prevent memory problem>
wait_task: <sleep time for worker to wait for next task>
max_retry: <number of retry attempt after failed download>
timeout: <timeout for attempting connection>
wait_retry: <time to wait before next attempt>
max_worker: <number of workers to use>
```

### Calling Program

```
python download_files.py --input=/path/to/input.yml --config=/path/to/config.yml
```