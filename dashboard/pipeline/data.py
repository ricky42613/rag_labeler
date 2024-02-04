from pydantic import BaseModel
from typing import List
from lxml import html
from trafilatura import extract

class RAGdata(BaseModel):
    content: str
    context: str
    question: str
    answer: str
    url: str
    user: str
    tags: List[str]
    embedding: list = None
    def extract_maintext(self):
        contentTree = html.fromstring(self.content)
        self.content = extract(contentTree)
        return self
    def encode(self, model):
        text = self.context
        embedding = model(text, to_list=True)
        self.embedding = embedding
        return self

    