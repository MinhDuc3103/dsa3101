from dataclasses import dataclass

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class RubricItem:
    marks: int
    description: str
    item_idx: int
    file_idx: int
    question_num: int
