"""Single-game predictor."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.schemas.predict import PredictRequest, PredictResponse
from api.services import predict as predict_service

router = APIRouter(prefix="/predict", tags=["predict"])


@router.post("", response_model=PredictResponse)
def predict(req: PredictRequest) -> PredictResponse:
    try:
        return predict_service.predict_matchup(req.home_abbr, req.away_abbr)
    except KeyError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err
