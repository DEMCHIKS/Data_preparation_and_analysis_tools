import os
from datetime import date, timedelta
import requests
import pandas as pd
import geopandas as gpd
from shapely.geometry import shape

"""Setup required variables"""
# copernicus User email
copernicus_user = ""
# copernicus User Password
copernicus_password = ""
# WKT Representation of BBOX of AOI
ft = "POLYGON((29.073321247506765 49.845775018245774, " \
     "31.986007792928522 49.845775018245774, " \
     "31.986007792928522 51.278667808079206, " \
     "29.073321247506765 51.278667808079206, " \
     "29.073321247506765 49.845775018245774))"
# Sentinel satellite that you are interested in
data_collection = "SENTINEL-2"

"""Dates of search"""
target_date = date(2019, 8, 21)  # Дата, для якої потрібно завантажити дані
date_string = target_date.strftime("%Y-%m-%d")
start_date = target_date - timedelta(days=1)
start_date_string = start_date.strftime("%Y-%m-%d")
end_date = target_date + timedelta(days=1)
end_date_string = end_date.strftime("%Y-%m-%d")

"""List of desired product identifiers"""
desired_product_ids = ["S2A_MSIL2A_20190821T085601_N0213_R007_T36UUB_20190821T115206",
                       "S2A_MSIL2A_20190821T085601_N0213_R007_T36UUA_20190821T115206"]

"""Generate access token"""
def get_keycloak(username: str, password: str) -> str:
    data = {
        "client_id": "cdse-public",
        "username": username,
        "password": password,
        "grant_type": "password",
    }
    try:
        r = requests.post(
            "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
            data=data,
        )
        r.raise_for_status()
    except Exception as e:
        raise Exception(
            f"Keycloak token creation failed. Reponse from the server was: {r.json()}"
        )
    return r.json()["access_token"]

json_ = requests.get(
    f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Collection/Name eq '{data_collection}' and OData.CSC.Intersects(area=geography'SRID=4326;{ft}') and ContentDate/Start gt {start_date_string}T00:00:00.000Z and ContentDate/Start lt {end_date_string}T00:00:00.000Z&$count=True&$top=1000"
).json()
p = pd.DataFrame.from_dict(json_["value"])  # Fetch available dataset
if p.shape[0] > 0:  # If we get data back
    p["geometry"] = p["GeoFootprint"].apply(shape)
    # Convert pandas dataframe to Geopandas dataframe by setting up geometry
    productDF = gpd.GeoDataFrame(p).set_geometry("geometry")
    # Remove L1C dataset if not needed
    productDF = productDF[~productDF["Name"].str.contains("L1C")]
    print(f" total L2A tiles found {len(productDF)}")
    productDF["identifier"] = productDF["Name"].str.split(".").str[0]
    allfeat = len(productDF)
    

    if allfeat == 0:  # If L2A tiles are not available in current query
        print(f"No tiles found for {date_string}")
    else:  # If L2A tiles are available in current query
        # download tiles with desired product IDs
        for index, feat in enumerate(productDF.iterfeatures()):
            if feat['properties']['identifier'] in desired_product_ids:
                try:
                    # Create requests session
                    session = requests.Session()
                    # Get access token based on username and password
                    keycloak_token = get_keycloak(copernicus_user, copernicus_password)

                    session.headers.update({"Authorization": f"Bearer {keycloak_token}"})
                    url = f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products({feat['properties']['Id']})/$value"
                    response = session.get(url, allow_redirects=False)
                    while response.status_code in (301, 302, 303, 307):
                        url = response.headers["Location"]
                        response = session.get(url, allow_redirects=False)
                    print(feat["properties"]["Id"])
                    file = session.get(url, verify=False, allow_redirects=True)

                    with open(
                        f"./method_SECOND/{feat['properties']['identifier']}.zip",
                        "wb",
                    ) as p:
                        print(feat["properties"]["Name"])
                        p.write(file.content)
                except Exception as e:
                    print(f"Error downloading {feat['properties']['Name']}: {str(e)}")
                    
else:  # If no tiles found for given date range and AOI
    print('no data found')
        
