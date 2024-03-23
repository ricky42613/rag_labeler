from mlx_bert import MLXBertModel
from transformers import BertConfig
import mlx.core as mx
from mlx.utils import tree_unflatten
from transformers import AutoTokenizer 
import numpy as np
import torch
import torch.nn.functional as F
from torch import Tensor
def _average_pool(last_hidden_states: Tensor,
    attention_mask: Tensor) -> Tensor:
    last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
    return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]

def build_model(cfg_path:str, weight_path: str):
    mlx_cfg = BertConfig.from_json_file(cfg_path)
    mlx_model = MLXBertModel(mlx_cfg)
    loaded_mlx_weight = mx.load(weight_path)
    mlx_model.update(tree_unflatten(list(loaded_mlx_weight.items())))
    mlx_model.eval()
    tokenizer = AutoTokenizer.from_pretrained(mlx_cfg.name_or_path)
    return mlx_model, tokenizer

def mlx_encode(text ,tokenizer, model):
    encoded = tokenizer(text, return_tensors="np")
    encoded['token_type_ids'] = np.zeros(encoded['attention_mask'].shape).astype(int)
    seq_output, pooled_output = model(
        mx.array(encoded['input_ids']),
        attention_mask = mx.array(encoded['attention_mask']),
        token_type_ids = mx.array(encoded['token_type_ids'])
    )
    
    mlx_embed = torch.tensor(seq_output.tolist())
    mlx_embed = _average_pool(mlx_embed, torch.tensor(encoded['attention_mask'].tolist()))
    mlx_embed = F.normalize(mlx_embed, p=2, dim=1).tolist()
    return mlx_embed

if __name__ == '__main__':
    model, tokenizer = build_model('model_cfg.json', weight_path='mlx_bert.npz')
    texts = ['今天天氣如何', '今天天氣如何']
    embed1 = mlx_encode(texts[0], tokenizer, model)
    embed2 = mlx_encode(texts[1], tokenizer, model)
    from sentence_transformers import util
    print(util.cos_sim(embed1, embed2))