# Backend

Run the API with:

```console
cd backend
uvicorn backend.app.main:app --reload --port 8000
```

The app module is `backend.app.main`, so run from the workspace root with `uvicorn backend.app.main:app ...` (not `uvicorn main:app ...`).
