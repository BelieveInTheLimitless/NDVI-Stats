# NDVI-Stats
A simple python script that calculates NDVI(Normalized Difference Vegetation Index) statistics of a particular region based on user query using FastAPI and Docker

## Technologies Used :

- FastAPI (Python) - To create GET/POST request
- Planetary Computer STAC API - To access Sentinel2-L2A data
- Uvicorn - A web server to handle network communication 
- Rasterio - To convert satellite image href data to readable/visualizable format
- Numpy - To calculate statistics
- Docker - Containerization


## To Build and Run the project

```
$ sudo docker build -t sentinel-api .
```

```
$ sudo docker run -p 8000:8000 sentinel-api
```

- `Open` [http://0.0.0.0:8000](http://0.0.0.0:8000) `in the browser to execute GET request from input.json`
  
- `Run below command in the terminal to execute POST request from query.txt`
  ```
  $ sh query.txt
  ```
- Note: As the satellite image contains larger number of pixels, it may take some amount of time to return the output. Patience is the key!
