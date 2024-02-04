from threading import Lock
import numpy as np
from transformers import AutoModel, AutoTokenizer

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
                input_text,
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

        embeddings = result.last_hidden_state[:, 0, :].cpu().detach().numpy()
        if to_list:
            embeddings = embeddings.flatten().tolist()
        return embeddings
