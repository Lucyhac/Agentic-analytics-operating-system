from pathlib import Path

from fastapi import APIRouter, File, UploadFile

from app.models.schemas import UploadResponse
from app.services.dataset_service import dataset_service


router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_dataset(file: UploadFile = File(...)) -> UploadResponse:
    saved_path = await dataset_service.save_upload(file)
    dataframe = dataset_service.load_dataframe(saved_path)
    profile = dataset_service.build_profile(
        dataframe=dataframe,
        dataset_id=Path(saved_path).stem,
        filename=file.filename or saved_path.name,
    )
    return UploadResponse(message="Dataset uploaded and analyzed successfully.", profile=profile)
