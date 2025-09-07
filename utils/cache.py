import pickle
import os
import shutil

CACHE_DIR = '.cache'
if not os.path.exists(CACHE_DIR):
    os.mkdir(CACHE_DIR)

class Meta:
    FILE_NAME = 'meta'
    
    def __init__(self, data_type):
        self.data_type = data_type

class Cache:
    @staticmethod
    def _get_file_location(key):
        return f'{CACHE_DIR}/{key}'
    
    @classmethod
    def load(cls, key):
        # check if file exists and if its chunked automatically load chunks
        final_filepath = cls._get_file_location(key)
        if not os.path.exists(final_filepath):
            return None
        if os.path.isdir(final_filepath):
            return cls._load_v2(final_filepath)
        with open(final_filepath, 'rb') as f:
            return pickle.load(f)
    
    @classmethod
    def _load_v2(cls, final_filepath):
        meta_filepath = f'{final_filepath}/{Meta.FILE_NAME}'
        with open(meta_filepath, 'rb') as f:
            meta = pickle.load(f)  # type: Meta
        
        result = []
        for chunk_name in os.listdir(final_filepath):
            if chunk_name == Meta.FILE_NAME:
                continue
            chunk_filepath = f'{final_filepath}/{chunk_name}'
            with open(chunk_filepath, 'rb') as f:
                result.append(pickle.load(f))
        
        if meta.data_type == list:
            return [item for sublist in result for item in sublist]
        elif meta.data_type == dict:
            return {key: value for sublist in result for key, value in sublist}
        else:
            raise Exception('Invalid data type')
    
    @classmethod
    def store(cls, key, data, chunk=False):
        if chunk:
            cls._store_chunk(key, data)
        else:
            cls._store(key, data)
    
    @staticmethod
    def _chunk_data(data, chunk_size):
        for i in range(0, len(data), chunk_size):
            yield data[i:i + chunk_size]
    
    @classmethod
    def _remove_existing_key(cls, key):
        """
        Remove existing cache file or directory.
        Fixed to handle non-empty directories properly.
        """
        final_filepath = cls._get_file_location(key)
        if os.path.exists(final_filepath):
            if os.path.isdir(final_filepath):
                # Use shutil.rmtree to remove directory and all contents
                shutil.rmtree(final_filepath)
            else:
                # Remove single file
                os.remove(final_filepath)
    
    @classmethod
    def _store_chunk(cls, key, data):
        final_filepath = cls._get_file_location(key)
        cls._remove_existing_key(key)
        
        converted_data = []
        if isinstance(data, dict):
            meta = Meta(dict)
            for key_item, value in data.items():
                converted_data.append((key_item, value))
        elif isinstance(data, list):
            meta = Meta(list)
            converted_data = data
        else:
            raise Exception('Invalid data type')
        
        os.mkdir(final_filepath)
        for index, chunk in enumerate(cls._chunk_data(converted_data, chunk_size=50 * 1000 * 1000)):
            with open(f'{final_filepath}/{index}', 'wb') as f:
                pickle.dump(chunk, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        with open(f'{final_filepath}/{Meta.FILE_NAME}', 'wb') as f:
            pickle.dump(meta, f, protocol=pickle.HIGHEST_PROTOCOL)
    
    @classmethod
    def _store(cls, key, data):
        final_filepath = cls._get_file_location(key)
        cls._remove_existing_key(key)
        with open(final_filepath, 'wb') as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)  