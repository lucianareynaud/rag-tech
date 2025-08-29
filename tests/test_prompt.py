from app.prompts import render_user_prompt
from app.llm import LLM

def test_prompt_contains_doc_ids_and_stub():
    contexts = [
        {"doc_id":"H-500.md","score":0.812,"text":"H-500 humidifier has a 4-liter water tank and 12-hour runtime."},
        {"doc_id":"Blender-Common-Specs.md","score":0.701,"text":"All blenders are BPA-free and include safety lock."}
    ]
    user_p = render_user_prompt("What is water tank capacity?", contexts)
    assert "H-500.md" in user_p
    llm = LLM()  # stub by default
    out = llm.generate("system", user_p)
    assert "H-500.md" in out
