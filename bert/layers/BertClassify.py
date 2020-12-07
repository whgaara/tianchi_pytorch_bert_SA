import torch.nn as nn

from config import *
from bert.layers.Transformer import Transformer
from bert.layers.BertEmbeddings import TokenEmbedding, PositionEmbedding, BertEmbeddings
from bert.layers.Classify import Classify


class BertClassify(nn.Module):
    def __init__(self,
                 kinds_num,
                 vocab_size=VocabSize,
                 hidden=HiddenSize,
                 max_len=SentenceLength,
                 num_hidden_layers=HiddenLayerNum,
                 attention_heads=AttentionHeadNum,
                 dropout_prob=DropOut,
                 intermediate_size=IntermediateSize
                 ):
        super(BertClassify, self).__init__()
        self.vocab_size = vocab_size
        self.kinds_num = kinds_num
        self.hidden_size = hidden
        self.max_len = max_len
        self.num_hidden_layers = num_hidden_layers
        self.attention_head_num = attention_heads
        self.dropout_prob = dropout_prob
        self.attention_head_size = hidden // attention_heads
        self.intermediate_size = intermediate_size

        # 申明网络
        self.token_emb = TokenEmbedding()
        self.position_emb = PositionEmbedding()
        # self.bert_emb = BertEmbeddings(vocab_size=self.vocab_size, max_len=self.max_len, hidden_size=self.hidden_size)
        self.transformer_blocks = nn.ModuleList(
            Transformer(
                hidden_size=self.hidden_size,
                attention_head_num=self.attention_head_num,
                attention_head_size=self.attention_head_size,
                intermediate_size=self.intermediate_size).to(device)
            for _ in range(self.num_hidden_layers)
        )
        self.classify = Classify(self.hidden_size, self.kinds_num)

    @staticmethod
    def gen_attention_masks(segment_ids):
        def gen_attention_mask(segment_id):
            dim = segment_id.size()[-1]
            attention_mask = torch.zeros([dim, dim], dtype=torch.int64)
            end_point = 0
            for i, segment in enumerate(segment_id.tolist()):
                if segment:
                    end_point = i
                else:
                    break
            for i in range(end_point + 1):
                for j in range(end_point + 1):
                    attention_mask[i][j] = 1
            return attention_mask
        attention_masks = []
        segment_ids = segment_ids.tolist()
        for segment_id in segment_ids:
            attention_mask = gen_attention_mask(torch.tensor(segment_id))
            attention_masks.append(attention_mask.tolist())
        return torch.tensor(attention_masks)

    def forward(self, input_token, segment_ids):
        # embedding
        embedding_x = self.token_emb(input_token) + self.position_emb()
        # embedding_x = self.bert_emb(input_token)
        if AttentionMask:
            attention_mask = self.gen_attention_masks(segment_ids).to(device)
        else:
            attention_mask = None
        feedforward_x = None
        # transformer
        for i in range(self.num_hidden_layers):
            if i == 0:
                feedforward_x = self.transformer_blocks[i](embedding_x, attention_mask)
            else:
                feedforward_x = self.transformer_blocks[i](feedforward_x, attention_mask)
        # classify
        output = self.classify(feedforward_x)
        return output
