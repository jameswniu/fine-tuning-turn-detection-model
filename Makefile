PY := .venv/bin/python

.PHONY: synth train threshold eval evals serve bench docker-build docker-run smoke

synth:
	$(PY) synth.py --per-template 10

train:
	$(PY) train.py --train data/train.jsonl

tier1:  ## rebuild the twelve guardrail rows from the committed data
	$(PY) make_tier1_probes.py

threshold:
	$(PY) pick_threshold.py --model-dir models/eot-distilbert-onnx-int8 --labels data/dev_set.json --constraints data/tier1_probes.jsonl --cost-ratio 5

eval:
	$(PY) evaluate.py --model models/eot-distilbert-onnx-int8 --data data/gold_set.json --report eval_report.json

evals: eval

serve:
	$(PY) -m uvicorn serve:app --host 127.0.0.1 --port 8000

bench:
	$(PY) bench.py --url http://127.0.0.1:8000/predict --n 1500 --concurrency 1,8,32 --report bench_report.json

docker-build:
	docker build -t eot-detector .

docker-run:
	docker run --rm -p 8000:8000 eot-detector

smoke:
	curl -s http://127.0.0.1:8000/healthz && curl -s -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" -d '{"context":"","text":"Okay, got it."}'

figures:  ## regenerate the README figures from their constants
	$(PY) draw_figures.py --write

figures-check:  ## fail if a committed figure drifted from its constants or the 75% type floor
	$(PY) draw_figures.py --check
