FROM ghcr.io/astral-sh/uv:python3.12-alpine AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

WORKDIR /app

RUN apk add --update --no-cache git

# install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

ADD . /app

# sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

FROM python:3.12-alpine AS runner

WORKDIR /app

# Copy the application from the builder
COPY --from=builder --chown=app:app /app/.venv .venv
COPY --from=builder --chown=app:app /app/app app

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Run the FastAPI application by default
CMD ["fastapi", "run", "app/main.py", "--proxy-headers", "--port", "3000", "--host", "0.0.0.0"]