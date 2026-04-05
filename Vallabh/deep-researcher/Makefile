.PHONY: setup test run run-deep ui clean

# Setup
setup:
	python -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	cp -n .env.example .env || true
	@echo "✅ Setup complete. Edit .env with your API keys."

# Run tests
test:
	pytest tests/ -v

# Quick research
run:
	python main.py --query "$(QUERY)" --depth standard

# Deep research with export
run-deep:
	python main.py --query "$(QUERY)" --depth deep --export-report report.md --output results.json

# Streamlit UI
ui:
	streamlit run ui/app.py

# Clean
clean:
	rm -rf __pycache__ */__pycache__ */*/__pycache__
	rm -rf .pytest_cache
	rm -f results.json report.md
