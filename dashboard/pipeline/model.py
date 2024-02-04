from threading import Lock
import numpy as np
from transformers import AutoModel, AutoTokenizer
import torch.nn.functional as F
from torch import Tensor


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
    
    def __init__(self, model_path, max_input_length, device):
        self.model_path = model_path
        self._device = device
        self._max_input_length = max_input_length

        self._tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self._model = AutoModel.from_pretrained(self.model_path).to(self._device)
        self._model.eval()

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
            tokenized_text = self._tokenizer(
                [input_text],
                padding=True,
                truncation=True,
                return_tensors="pt",
                max_length=self._max_input_length,
            ).to(self._device)
        except Exception:
            return [] if to_list else np.array([])

        try:
            result = self._model(**tokenized_text)
        except Exception:
            return [] if to_list else np.array([])

        # embeddings = result.last_hidden_state[:, 0, :].cpu().detach().numpy()
        embeddings = average_pool(result.last_hidden_state, tokenized_text['attention_mask'])
        embeddings = F.normalize(embeddings, p=2, dim=1).tolist()
        return embeddings[0]
