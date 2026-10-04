"""Convert a merged fine-tuned model to GGUF and register it with Ollama.

Uses llama.cpp's official converter (cloned once into MODEL_DIR/llama.cpp). Ollama's own safetensors
importer does not accept Qwen2, which is why this goes through GGUF.
Usage: python finetune/export_ollama.py --merged finetune/outputs/qwen2.5-0.5b-extract-lora/merged \
                                        --name coop-extract [--outtype q8_0]
"""

import argparse
import pathlib
import shutil
import subprocess
import sys

from coop_assistant.config import MODEL_DIR

HERE = pathlib.Path(__file__).parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--merged", required=True)
    parser.add_argument("--name", default="coop-extract")
    parser.add_argument("--outtype", default="q8_0", choices=["q8_0", "f16", "bf16", "f32"])
    args = parser.parse_args()

    merged = pathlib.Path(args.merged).resolve()
    llama = MODEL_DIR / "llama.cpp"
    if not llama.exists():
        subprocess.run(["git", "clone", "--depth", "1", "https://github.com/ggml-org/llama.cpp", str(llama)], check=True)

    gguf = merged.parent / f"{args.name}-{args.outtype}.gguf"
    subprocess.run([sys.executable, str(llama / "convert_hf_to_gguf.py"), str(merged),
                    "--outfile", str(gguf), "--outtype", args.outtype], check=True)
    print(f"GGUF: {gguf} ({gguf.stat().st_size / 1e6:.0f} MB)")

    modelfile = merged.parent / "Modelfile"
    modelfile.write_text((HERE / "Modelfile").read_text().replace("FROM ./model.gguf", f"FROM {gguf}"))
    ollama = shutil.which("ollama") or str(pathlib.Path.home() / "AppData/Local/Programs/Ollama/ollama.exe")
    subprocess.run([ollama, "create", args.name, "-f", str(modelfile)], check=True)
    print(f"Ollama model '{args.name}' created. Try: python finetune/evaluate.py --task extract --extract-model {args.name}")


if __name__ == "__main__":
    main()
