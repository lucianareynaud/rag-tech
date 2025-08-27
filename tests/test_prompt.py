from app.prompts import render_user_prompt
from app.llm import LLM

def test_prompt_contains_doc_ids_and_stub():
    contexts = [
        {"doc_id":"Z-123.md","score":0.812,"text":"Z-123 blender has a 1.5L jar and 700W motor."},
        {"doc_id":"common-specs.md","score":0.701,"text":"All jars are BPA-free and include safety lock."}
    ]
    user_p = render_user_prompt("What is jar capacity?", contexts)
    assert "doc_id=Z-123.md" in user_p
    llm = LLM()  # stub by default
    out = llm.generate("system", user_p)
    assert "Z-123.md" in out
