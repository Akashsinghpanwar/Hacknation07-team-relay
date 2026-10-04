"""Local demo screen: python -m coop_assistant.apps.web_ui, then open http://127.0.0.1:7860"""

import os
import re
import socket

os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")

import gradio as gr

from coop_assistant.core.store import connect
from coop_assistant.pipeline import Assistant
from coop_assistant.speech import voice

CONN = connect()
LANGS = {"Auto-detect": None, "English": "en", "Hindi": "hi", "Swahili": "sw", "Chinese": "zh", "Korean": "ko"}
STATE_STYLE = {
    "ANSWER": ("#1b7f3b", "ANSWER: matched dated record"),
    "CLARIFY": ("#b26a00", "CLARIFY: need more detail"),
    "ABSTAIN": ("#b3261e", "ABSTAIN: not sure, no number given"),
    "REFER": ("#3949ab", "REFER: human follow-up"),
}


def internet_status():
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=1).close()
        return "**Internet: ON**"
    except OSError:
        return "**Internet: OFF** - everything below runs on this laptop"


def guess_lang(text):
    if re.search(r"[가-힯]", text):
        return "ko"
    if re.search(r"[一-鿿]", text):
        return "zh"
    if re.search(r"[ऀ-ॿ]", text):
        return "hi"
    if re.search(r"\b(bei|kahawa|shilingi|mnunuzi|daraja|kilo moja|tafadhali|huko)\b", text.lower()):
        return "sw"
    return "en"


def run(audio, typed, lang_name, bot):
    bot = bot or Assistant(CONN)
    forced = LANGS[lang_name]
    if audio:
        text, detected, _ = voice.transcribe(audio, forced)
        heard = "speech"
    else:
        text, detected, heard = (typed or "").strip(), forced or guess_lang(typed or ""), "typed"
    lang = forced or detected
    result = bot.handle(text, lang)
    d = result["decision"]
    color, label = STATE_STYLE[d["state"]]
    badge = f"<div style='background:{color};color:#fff;padding:10px 14px;border-radius:8px;font-weight:600'>{label}</div>"
    spoken, tts = voice.speak(result["reply"], result["lang"])
    meta = (f"Heard via {heard} | language: `{result['lang']}` | extraction: `{result['method']}` | "
            f"voice: `{tts}` | {internet_status()}")
    return (text, meta, badge, result["reply"], spoken,
            {"intent": d["intent"], **d["slots"]}, {"evidence_id": d["evidence_id"], **d["facts"]}, None, "", bot)


def reset(bot):
    if bot:
        bot.reset()
    return bot, "", "", "", "", None, None, None


with gr.Blocks(title="Coffee Price Check - offline demo") as demo:
    gr.Markdown("# Coffee price check (offline Small AI demo)\n"
                "Speak or type a buyer's offer in English, Hindi, Swahili, Chinese or Korean. "
                "**All prices are synthetic DEMO data.** The farmer always makes the final decision.")
    bot = gr.State(None)
    status = gr.Markdown(internet_status())
    with gr.Row():
        with gr.Column():
            audio = gr.Audio(sources=["microphone"], type="filepath", label="Speak")
            typed = gr.Textbox(label="...or type", placeholder="Buyer offered 105 shillings per kg for grade A parchment in Nyeri")
            lang = gr.Dropdown(list(LANGS), value="Auto-detect", label="Language")
            with gr.Row():
                go = gr.Button("Ask", variant="primary")
                clear = gr.Button("New conversation")
        with gr.Column():
            badge = gr.HTML()
            reply = gr.Textbox(label="Answer", lines=4)
            spoken = gr.Audio(label="Spoken answer", autoplay=True)
            transcript = gr.Textbox(label="What the AI heard")
            meta = gr.Markdown()
    with gr.Row():
        slots = gr.JSON(label="Extracted from the question")
        evidence = gr.JSON(label="Evidence record used")

    go.click(run, [audio, typed, lang, bot],
             [transcript, meta, badge, reply, spoken, slots, evidence, audio, typed, bot])
    typed.submit(run, [audio, typed, lang, bot],
                 [transcript, meta, badge, reply, spoken, slots, evidence, audio, typed, bot])
    clear.click(reset, [bot], [bot, transcript, meta, badge, reply, spoken, slots, evidence])
    demo.load(internet_status, None, status)

def main():
    demo.launch(server_name="127.0.0.1", server_port=7860)


if __name__ == "__main__":
    main()
