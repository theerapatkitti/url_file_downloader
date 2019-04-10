from queue import Queue
import argparse
import yaml
import errno
import os
from utils.worker import Worker
from utils.visualizer import Visualizer
from utils.filemanager import FileManager

def get_input(filepath):
    """
    Get inputs from file.

    filepath: path to file containing inputs

    Returns:
    inputs: dict of inputs and its attributes
    """
    with open(filepath, 'r') as stream:
        try:
            inputs = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    
    return inputs

def get_config(filepath):
    """
    Get config from file.

    filepath: path to file containing config

    Returns:
    config: dict of config
    """
    with open(filepath, 'r') as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    
    return config

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Download files from different sources with different protocols.')
    parser.add_argument('--input', required=True,
                        metavar="/path/to/input/",
                        help='Path to input .yml file')
    parser.add_argument('--config', required=True,
                        metavar="/path/to/config/",
                        help='Path to configurate .yml file')
    args = parser.parse_args()

    try:
        if not FileManager.is_path_exists(args.input):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), args.input)
        if not FileManager.is_path_exists(args.config):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), args.config)

        inputs = get_input(args.input)
        config  = get_config(args.config)

        # Quit if inputs is empty
        if not inputs:
            raise Exception("No inputs given")

        works = Queue(maxsize=0)
        progresses = Queue(maxsize=0)

        # Put work to Queue
        for i, info in enumerate(inputs.values()):
            works.put((i + 1, info))

        # Setup workers
        num_threads = min(config.get("max_worker", 5), len(inputs))
        for i in range(num_threads):
            worker = Worker(config, works, progresses, name="worker{}".format(i))
            worker.setDaemon(True)
            worker.start()

        # Setup visualizer
        visualizer = Visualizer(len(inputs), progresses, name="visualizer")
        visualizer.start()

        # Wait until works Queue and visualizer finished
        works.join()
        visualizer.join()

    except FileNotFoundError as errf:
        print(errf)
    except Exception as e:
        print(e)