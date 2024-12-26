import random
import yaml
import json
import os
from copy import deepcopy
from openai import OpenAI
from gradio_client import Client
import concurrent.futures


def rndsuf(k=3):
    return "".join(chr(random.randint(65, 90)) if random.randint(0, 1) else chr(random.randint(97, 122)) for _ in range(k))

def rnd():
    return random.random()

def rndc(choose4m, k=1):
    if not isinstance(choose4m, list):
        choose4m = list(choose4m)
    return random.choice(choose4m) if k == 1 else random.sample(choose4m, k)

def get_keys(content):
    if isinstance(content, dict):
        return list(content.keys())
    
def get_values(content):
    if isinstance(content, dict):
        return list(content.values())

def yaml_print(content):
    if not isinstance(content, dict):
        content = eval(content.__repr__())
    print(yaml.safe_dump(content, allow_unicode=True))

def read_json(filename):
    with open(filename) as f:
        content = json.load(f)
    return content

def write_json(content, filename):
    with open(filename, "w") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)

def read(filename):
    with open(filename) as f:
        contet = f.read().strip()
    return contet

def write(content, filename):
    with open(filename, "w") as f:
        f.write(content.strip())
        f.write("\n")

def read_jsonl(filename):
    content = []
    with open(filename) as f:
        for line in f:
            content += [json.loads(line.strip())]
    return content

def write_jsonl(content, filename, mode="w"):
    with open(filename, mode) as f:
        for line in content:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")

def dumps(content):
    return json.dumps(content, ensure_ascii=False, indent=2)

def yamld(content):
    return yaml.dump(content, allow_unicode=True, indent=2, sort_keys=False)

def dumplist(content):
    repr = ""
    for line in content:
        if isinstance(line, list):
            repr = "\n".join([repr, ", ".join(str(e) for e in line)])
        else:
            repr = "\n".join([repr, str(line)])
    return repr.strip()


KEY = ""

def query_gpt4(prompt):
    client = OpenAI(api_key=KEY)
    if isinstance(prompt, list):
        assert isinstance(prompt[0], dict)
        assert prompt[0].get("role") and prompt[0].get("content")
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=prompt
        )
    else:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
        )
    prediction = completion.choices[0].message.content
    return prediction

def query_qwen(query, history=[]):
    response = Client("Qwen/Qwen1.5-110B-Chat-demo").predict(
        query=query,
        history=history,
        api_name="/model_chat"
    )
    return response[1][-1][-1]


def memory_to_text(m, char_id=None):
    if char_id is not None:
        m["aid"] = "你" if m["aid"] == char_id else m["aid"]
        m["bid"] = "你" if m["bid"] == char_id else m["bid"]

    if m["x"] == "-give":
        text = "{} 给了 {} {}。".format(m["aid"], m["bid"], m["cid"])
    elif m["x"] == "-speak" and m["bid"] is None:
        text = "{} 说：{}".format(m["aid"], m["content"])
    elif m["x"] == "-speak":
        text = "{} 和 {} 说：{}".format(m["aid"], m["bid"], m["content"])
    elif m["x"] == "-leave":
        text = "{} 离开了对话。".format(m["aid"])
    elif m["x"] == "-move":
        text = "{} 去了 {}。".format(m["aid"], m["bid"])
    elif m["x"] == "-scream":
        text = "{} 发出了尖叫：{}".format(m["aid"], m["content"])

    return text

def observation_to_text(o, char_id=None):
    o["interact_with"] = "你" if o["interact_with"] == char_id else o["interact_with"]

    if o["status"] == "/idle/" and o["interact_with"] is None:
        text = "{} 正空闲，在{}。".format(o["id"], o["loc"])
    elif o["status"] == "/idle/" and o["interact_with"] is not None:
        text = "{} 正在和 {} 交谈，在{}。".format(o["id"], o["interact_with"], o["loc"])
    elif o["status"] == "/faint/":
        text = "{} 晕了过去，在{}。".format(o["id"], o["loc"])

    return text


class DynamicScript:
    def __init__(self, script):
        self.script = script
        self.scene_ids = get_keys(script)
        self.p = 0
        # self._samples = {}
        # for v in get_values(self.script[self.scene_ids[self.p]]["情节"]):
        #     for li in v:
        #         k, li = li.split("$")
        #         if k in self._samples:
        #             self._samples[k] += [li]
        #         else:
        #             self._samples[k] = [li]

    @property
    def plots(self):
        return get_keys(self.script[self.scene_ids[self.p]]["情节"])
    
    @property
    def characters(self):
        return self.script[self.scene_ids[self.p]]["人物"]
    
    @property
    def mode(self):
        return self.script[self.scene_ids[self.p]]["模式"]

    @property
    def scene_id(self):
        return self.scene_ids[self.p]

    @property
    def location(self):
        return self.script[self.scene_ids[self.p]]["地点"]
    
    def __getitem__(self, x):
        return self.script[self.scene_ids[self.p]][x]

    def sample(self, x):
        x = x.split("$")[0] if x else x
        return self._samples.get(x, [])

    def dump(self, detail=False):
        if detail:
            return yaml.safe_dump(self.script, allow_unicode=True, indent=2, sort_keys=False)
        tmp_script = deepcopy(self.script)
        for scene_id, v in tmp_script.items():
            if scene_id == self.scene_ids[self.p]:
                continue
            v["情节"] = get_keys(v["情节"]) if "情节" in v else None
            v["人物"] = None
            v["模式"] = None
        return yaml.safe_dump(tmp_script, allow_unicode=True, indent=2, sort_keys=False)
