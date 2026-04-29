#!/bin/sh
set -e


uv run --package bancobot pytest apps/bancobot/tests --cov=bancobot --cov-report=term-missing
uv run --package classifier pytest apps/classifier/tests --cov=classifier --cov-report=term-missing
uv run --package fork_engine pytest apps/fork_engine/tests --cov=fork_engine --cov-report=term-missing
