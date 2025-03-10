# LLM-based Interactive Drama

This is the Chinese demonstration for the ACL 2024 paper ([From Role-Play to Drama-Interaction: An LLM Solution](https://aclanthology.org/2024.findings-acl.196.pdf)).

Our secondary work discusses the immersion-agency paradigm towards a nice interactive experience ([Towards Enhanced Immersion and Agency for LLM-based Interactive Drama](https://arxiv.org/pdf/2502.17878)).



### Demonstration

《候车室里的7个人》 adapted from *Detective Conan*

The player will play the role of *Conan*.

![pv](assets/screen.png)

1. Add your openai key in `openai_key.txt`

```bash
vi openai_key.txt
```

2. Start the backend

```bash
python app.py
```

3. Open the web on the localhost http://localhost:8000/

```bash
python -m http.server 8000
```


**To play**

Every moment, you have two options.

* Stay and see other NPCs' reaction by pressing "Tab" on your keyboard.
* Interact with other NPCs by clicking the avatar of him/her and input the content. Press "Enter" or "确认" to calculate the result based on your input. 

**Move**

Use ←, →, ↑, ↓.

**To the next scene**

Press the "去往下一个场景" button to jump to the next scene.

**Holdings**

There are some items in the drama. Press the "持有物" button to check.


---

In this demonstration, each role agents is based on GPT-4o.

There are only three scenes available now, also in Chinese, apologized. We are still working on the script.

If you like our project, come join us!


### Drama Details

**Characters**

![pv](assets/profiles.png)

**Script**

Scene 1——候车室的7个人

Scene 2——危险的预告

Scene 3——有限调查

There are two modes in the drama. In Scene 1 and Scene 2, the narrative is scripted. The player can engage the roundtable discussion. In Scene 3, the play can explore the characters in person.



## Todo

1. Complete the story
2. Generalize to English
