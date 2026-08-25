PY := .venv/bin/python

.PHONY: synth train eval evals serve bench docker-build docker-run smoke

synth:
	$(PY) synth.py --per-template 10

train:
	$(PY) train.py --train data/train.jsonl

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
