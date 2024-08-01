from fastapi import FastAPI, HTTPException
from datetime import datetime, timedelta
import pystac_client
import planetary_computer
from pystac.extensions.eo import EOExtension as eo
import rasterio
from rasterio import windows, features, warp
import numpy as np
import json
from pydantic import BaseModel

from typing import Dict, Any

app = FastAPI()

def load_input_data():
    with open('input.json', 'r') as file:
        data = json.load(file)
    return data

class QueryRequest(BaseModel):
    time_of_interest: str
    area_of_interest: Dict[str, Any]

class QueryResponse(BaseModel):
    min: float
    max: float
    mean: float
    median: float
    std: float

async def get_ndvi_stats(query: QueryRequest) -> QueryResponse:
    try:
        toi = query.time_of_interest
        aoi = query.area_of_interest

        catalog = pystac_client.Client.open(
            "https://planetarycomputer.microsoft.com/api/stac/v1",
            modifier = planetary_computer.sign_inplace,
        )

        search = catalog.search(
            collections = ["sentinel-2-l2a"],
            intersects = aoi,
            datetime = toi,
            query = {"eo:cloud_cover": {"lt": 10}},
        )

        items = search.item_collection()

        if len(items) == 0:
            raise HTTPException(status_code = 404, detail = "No Sentinel-2 data found for the given parameters")

        least_cloudy_item = min(items, key = lambda item: eo.ext(item).cloud_cover)

        red_asset = least_cloudy_item.assets["B04"].href
        nir_asset = least_cloudy_item.assets["B08"].href

        with rasterio.open(red_asset) as red_ds, rasterio.open(nir_asset) as nir_ds:
            aoi_bounds = features.bounds(aoi)
            warped_aoi_bounds = warp.transform_bounds("epsg:4326", red_ds.crs, *aoi_bounds)
            red_aoi_window = windows.from_bounds(transform = red_ds.transform, *warped_aoi_bounds)
            nir_aoi_window = windows.from_bounds(transform = nir_ds.transform, *warped_aoi_bounds)
            red_data = red_ds.read(1, window = red_aoi_window)
            nir_data = nir_ds.read(1, window = nir_aoi_window)

        denominator = nir_data + red_data
        ndvi = np.where(denominator != 0, (nir_data.astype(float) - red_data.astype(float)) / denominator, 0)


        ndvi_min = float(np.min(ndvi))
        ndvi_max = float(np.max(ndvi))
        ndvi_mean = float(np.mean(ndvi))
        ndvi_median = float(np.median(ndvi))
        ndvi_std = float(np.std(ndvi))

        ndvi_stats = QueryResponse(min = ndvi_min, max = ndvi_max, mean = ndvi_mean, median = ndvi_median, std = ndvi_std)

        for field in ndvi_stats.__fields__:
            value = getattr(ndvi_stats, field)
            if np.isnan(value) or np.isinf(value):
                setattr(ndvi_stats, field, None)
        
        return ndvi_stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def get_query() -> QueryResponse:
    query_data = load_input_data()
    query = QueryRequest(**query_data)
    ndvi_stats = await get_ndvi_stats(query = query)
    return ndvi_stats
    
@app.post("/query", response_model=QueryResponse)
async def post_query(query: QueryRequest):
    ndvi_stats = await get_ndvi_stats(query = query)
    return ndvi_stats