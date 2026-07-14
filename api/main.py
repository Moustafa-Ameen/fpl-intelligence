from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import backtest, chips, fixtures, fpl_live, planner, players, predictions

app = FastAPI(title="FPL Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(players.router)
app.include_router(fixtures.router)
app.include_router(predictions.router)
app.include_router(planner.router)
app.include_router(fpl_live.router)
app.include_router(backtest.router)
app.include_router(chips.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
