"""LoRA supervised fine-tuning of a small instruct model on finetune/data/*.jsonl (chat format).

Needs a CUDA GPU (a free Colab T4 is enough for 1.5B) and: pip install -e ".[finetune]"
Usage:
  python finetune/train_lora.py --config finetune/configs/qwen2.5-1.5b-lora.json
  python finetune/train_lora.py --base Qwen/Qwen2.5-1.5B-Instruct --epochs 3 --merge
"""

import argparse
import json
import pathlib

import torch
from datasets import load_dataset
from peft import LoraConfig
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import SFTConfig, SFTTrainer

HERE = pathlib.Path(__file__).parent
DEFAULTS = {
    "base": "Qwen/Qwen2.5-1.5B-Instruct",
    "train": str(HERE / "data" / "train.jsonl"),
    "eval": str(HERE / "data" / "eval.jsonl"),
    "out": str(HERE / "outputs" / "qwen2.5-1.5b-coop-lora"),
    "epochs": 3,
    "lr": 2e-4,
    "batch": 4,
    "grad_accum": 4,
    "max_len": 2048,
    "r": 16,
    "alpha": 32,
    "dropout": 0.05,
    "merge": False,
}


def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="JSON file with any of the keys below")
    for key, value in DEFAULTS.items():
        if isinstance(value, bool):
            parser.add_argument(f"--{key.replace('_', '-')}", dest=key, action="store_true", default=None)
        else:
            parser.add_argument(f"--{key.replace('_', '-')}", dest=key, type=type(value), default=None)
    args = parser.parse_args()
    cfg = dict(DEFAULTS)
    if args.config:
        cfg.update(json.loads(pathlib.Path(args.config).read_text()))
    cfg.update({k: v for k, v in vars(args).items() if k != "config" and v is not None})
    return cfg


def main():
    cfg = parse()
    print(json.dumps(cfg, indent=2))
    data = load_dataset("json", data_files={"train": cfg["train"], "eval": cfg["eval"]}).remove_columns("task")

    tokenizer = AutoTokenizer.from_pretrained(cfg["base"])
    model = AutoModelForCausalLM.from_pretrained(cfg["base"], torch_dtype="auto", device_map="auto")
    lora = LoraConfig(
        r=cfg["r"], lora_alpha=cfg["alpha"], lora_dropout=cfg["dropout"], task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    )
    bf16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
    args = SFTConfig(
        output_dir=cfg["out"],
        num_train_epochs=cfg["epochs"],
        learning_rate=cfg["lr"],
        per_device_train_batch_size=cfg["batch"],
        gradient_accumulation_steps=cfg["grad_accum"],
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        max_length=cfg["max_len"],
        logging_steps=10,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=1,
        bf16=bf16,
        fp16=torch.cuda.is_available() and not bf16,
        report_to="none",
    )
    trainer = SFTTrainer(model=model, args=args, train_dataset=data["train"], eval_dataset=data["eval"],
                         peft_config=lora, processing_class=tokenizer)
    trainer.train()
    trainer.save_model(cfg["out"])
    tokenizer.save_pretrained(cfg["out"])
    print("LoRA adapter saved to", cfg["out"])

    if cfg["merge"]:
        merged_dir = pathlib.Path(cfg["out"]) / "merged"
        trainer.model.merge_and_unload().save_pretrained(merged_dir)
        tokenizer.save_pretrained(merged_dir)
        print("Merged model saved to", merged_dir, "- convert it to GGUF next (see finetune/README.md)")


if __name__ == "__main__":
    main()
