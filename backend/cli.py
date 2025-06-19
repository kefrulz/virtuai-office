import uvicorn


def main() -> None:
    """Run the VirtuAI Office backend using uvicorn."""
    uvicorn.run("backend.backend:app", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
