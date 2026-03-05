ui:
    python -m streamlit run frontend/main.py

deploy:
    docker build --platform linux/amd64 -t gcr.io/wealth-tracker-1eb4d/finance-tracker:latest .
    docker push gcr.io/wealth-tracker-1eb4d/finance-tracker:latest
    gcloud run deploy finance-tracker \
        --image gcr.io/wealth-tracker-1eb4d/finance-tracker:latest \
        --region us-central1 \
        --project wealth-tracker-1eb4d
