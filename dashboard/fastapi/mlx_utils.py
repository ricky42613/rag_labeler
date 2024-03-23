from mlx_bert import MLXBertModel
from transformers import BertConfig
import mlx.core as mx
from mlx.utils import tree_unflatten
from transformers import AutoTokenizer 
import numpy as np

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
    return seq_output.tolist(), pooled_output.tolist()

if __name__ == '__main__':
    model, tokenizer = build_model('model_cfg.json', weight_path='mlx_bert.npz')
    texts = ['今天天氣如何', 'apple is the best company in the world']
    embed1 = mlx_encode(texts[0], tokenizer, model)
    embed2 = mlx_encode(texts[1], tokenizer, model)
    from sentence_transformers import util
    print(util.cos_sim(embed1[1], embed2[1]))