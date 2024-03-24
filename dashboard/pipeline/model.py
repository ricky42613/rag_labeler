from threading import Lock
import numpy as np
from transformers import AutoModel, AutoTokenizer
import torch.nn.functional as F
from torch import Tensor
import sys
sys.path.append("../fastapi/")
import mlx_utils
def average_pool(last_hidden_states: Tensor,
                 attention_mask: Tensor) -> Tensor:
    last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
    return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]

class EmbeddingModelSingleton:
    _instances = None
    _lock = Lock()
    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instances == None:
                cls._instances = super().__new__(cls)
        return cls._instances
    
    def __init__(self, max_input_length):
        self._max_input_length = max_input_length

        self.model, self._tokenizer =  mlx_utils.build_model('../fastapi/model_cfg.json', '../fastapi/mlx_bert.npz')

    @property
    def max_input_length(self) -> int:
        """
        Returns the maximum length of input text to tokenize.

        Returns:
            int: The maximum length of input text to tokenize.
        """

        return self._max_input_length

    @property
    def tokenizer(self) -> AutoTokenizer:
        return self._tokenizer


    def __call__(self, input_text: str, to_list: bool = True):
        try:
            embeddings =  mlx_utils.mlx_encode(input_text[:self.max_input_length-2], self._tokenizer, self.model)
            return embeddings[0]
        except Exception:
            return [] if to_list else np.array([])
