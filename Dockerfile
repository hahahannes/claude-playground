FROM python:3.11-slim AS builder

WORKDIR /app
COPY environment.yml .
RUN pip install --no-cache-dir pandas matplotlib pyyaml seaborn pytest

FROM python:3.11-slim

RUN useradd --create-home appuser
WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY plot.py plot_throughput.py test_plot_throughput.py config.yml ./

USER appuser

ENTRYPOINT ["python"]
CMD ["plot_throughput.py", "--help"]
