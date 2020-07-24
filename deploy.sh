#!/bin/bash

set -exo pipefail

gcloud config set project utf8-xyz
gcloud builds submit --tag gcr.io/utf8-xyz/website
gcloud beta run deploy website \
    --image gcr.io/utf8-xyz/website \
    --platform=managed \
    --region=us-central1 \
    --timeout=10 \
    --memory=512Mi \
    --allow-unauthenticated
