import zlib
import pickle

class CacheCompression:
    @staticmethod
    def compress_data(data):
        """壓縮數據"""
        pickled = pickle.dumps(data)
        compressed = zlib.compress(pickled)
        return compressed

    @staticmethod
    def decompress_data(compressed_data):
        """解壓數據"""
        decompressed = zlib.decompress(compressed_data)
        return pickle.loads(decompressed) 