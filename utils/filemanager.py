import os
import uuid

class FileManager:
    def __init__(self):
        pass
    
    @staticmethod
    def create_directory(path):
        if not FileManager.is_path_exists(path):
            os.makedirs(path, exist_ok=True)
            
    @staticmethod
    def remove_file(file_path):
        if os.path.exists(file_path):
            return os.remove(file_path)
    
    @staticmethod
    def rename_file(old, new):
        if os.path.exists(old):
            os.rename(old, new)

    @staticmethod
    def random_filepath(path):
        file_path = os.path.join(path, "{}".format(uuid.uuid4()))
        if os.path.exists(file_path):
            return FileManager.random_filepath(path)
        return file_path

    @staticmethod
    def generate_filepath(file_path, i=1):
        new_file_path = os.path.join(os.path.dirname(file_path), "{}_{}".format(i, os.path.basename(file_path)))
        if os.path.exists(new_file_path):
            return FileManager.generate_filepath(file_path, i + 1)
        return new_file_path
    
    @staticmethod
    def join_path(path, file):
        return os.path.join(path, file)

    @staticmethod
    def get_basename(file_path):
        return os.path.basename(file_path)
    
    @staticmethod
    def get_dirname(file_path):
        return os.path.dirname(file_path)

    @staticmethod
    def is_path_creatable(path):
        dirname = os.path.dirname(path) or os.getcwd()
        return os.access(dirname, os.W_OK)
    
    @staticmethod
    def is_path_exists(path):
        return os.path.exists(path)