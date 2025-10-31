Infrastructure

This directory contains optional deployment and ops resources.

Structure:

- k8s/: Minimal Kubernetes manifests for local/staging experimentation

Notes:

- Dockerfiles for services live alongside each service (e.g., `backend/`, `worker/`).
- These k8s manifests are intentionally minimal; customize images, env vars, storage, and security before production use.

Quick start (kubectl):

1. kubectl apply -f k8s/namespace.yaml
2. kubectl -n gen apply -f k8s/

Namespace:

- All resources target the `gen` namespace.
