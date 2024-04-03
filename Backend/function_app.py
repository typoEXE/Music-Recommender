import azure.functions as func
import os
import json
import logging
from azure.storage.blob import BlobServiceClient
from sklearn.metrics.pairwise import linear_kernel
from io import BytesIO
import joblib
import pandas as pd

# Read the connection string from the environment variable
connection_string = "DefaultEndpointsProtocol=https;AccountName=musicrecommend8158579953;AccountKey=slIeV18IKjoUAHhWMeNSBEchWxYIxi3M3lEEH2BsOjVHsvXwHc3C4k0YQ6SrGR7WM54lGq9Jp12J+AStc6S2cw==;EndpointSuffix=core.windows.net"
# Read the container name from the environment variable
container_name = "music-rec-container"

# Initialize BlobServiceClient using your Azure Storage account connection string
blob_service_client = BlobServiceClient.from_connection_string(connection_string)


app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="api_recommend", methods=["POST"])
def api_recommend(req: func.HttpRequest) -> func.HttpResponse:
    try:
        json_input = req.get_json()
        data = json_input
        logging.info("Successfully obtained JSON input.")
    except ValueError:
        logging.info("JSON DATA ERROR")
        return func.HttpResponse("Invalid JSON data in the request body.", status_code=400)

    try:
        logging.info("Attempting to load from blob storage")
        df = load_csv_data()
        tfidf_vectorizer = load_model_from_blob('tfidfvectorizer.pkl')
        tfidf_matrix = load_model_from_blob('tfidfmatrix.pkl')

        if df is None:
            logging.info("preprocesseddata no info")
            return func.HttpResponse("Error loading CSV data.", status_code=500)
        if tfidf_vectorizer is None:
            logging.info("tfidf_vectorizer no info")
            return func.HttpResponse("Error loading model tfidfvectorizer.", status_code=500)
        if tfidf_matrix is None:
            logging.info("tfidf_matrix no info")
            return func.HttpResponse("Error loading model tfidfmatrix.", status_code=500)

        logging.info("Successfully loaded Storage Blob Files")

        logging.info("Attempting process_input")
        data = process_input(data)
        logging.info(f"process_input executed {data}")
        logging.info("Attempting get_recommendations")
        recommendations = get_recommendations(data, tfidf_vectorizer, tfidf_matrix, df)
        logging.info(f"get_recommendations executed {recommendations}")

        # Extracting "track_uri" values from the recommendations
        track_uris = [item["track_uri"] for item in recommendations]

        return func.HttpResponse(
            body=json.dumps(track_uris),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        # Add more logging statements to capture additional information
        logging.error(f"Data: {data}")
        logging.error(f"tfidf_vectorizer: {tfidf_vectorizer}")
        logging.error(f"tfidf_matrix: {tfidf_matrix}")
        logging.info("HIT LAST EXCEPTION BLOCK")
        return func.HttpResponse("An unexpected error occurred.", status_code=500)


def load_blob_data(blob_client):
    try:
        blob_data = blob_client.download_blob()
        return blob_data.readall()
    except Exception as e:
        logging.error(f"Error loading blob data: {str(e)}")
        return None

def load_data_from_blob(blob_name):
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    return load_blob_data(blob_client)

def load_csv_data():
    blob_data = load_data_from_blob('preprocesseddata.csv')
    if blob_data:
        try:
            return pd.read_csv(BytesIO(blob_data))
        except Exception as e:
            logging.error(f"Error loading CSV data from blob: {str(e)}")
    return None

def load_model_from_blob(model_name):
    model_blob_client = blob_service_client.get_blob_client(container=container_name, blob=model_name)
    model_data = load_blob_data(model_blob_client)
    if model_data:
        try:
            return joblib.load(BytesIO(model_data))
        except Exception as e:
            logging.error(f"Error loading model from blob: {str(e)}")
    return None

# Takes in json input as a dataframe
def process_input(data):
    # Perform the required transformations
    data["artists_genres"] = [genre.replace(" ", "") for genre in data["artists_genres"]]
    data["artists_names"] = [name.replace(" ", "") for name in data["artists_names"]]

    for key in data.keys():
        # Check for "null" values and replace with None
        if data[key] == "null":
            data[key] = None
        # Skip the specified keys
        elif key not in ["artists_genres", "artists_names", "release_date"]:
            # Convert to lowercase and replace spaces with an empty string
            data[key] = data[key].lower().replace(" ", "")

    # Additional transformations for "valence" key
    valence_mapping = {
        "sad": "lowvalence",
        "neutral": "moderatevalence",
        "happy": "highvalence"
    }
    data["valence"] = valence_mapping.get(data["valence"], data["valence"])

    # Additional transformations for "tempo" key
    tempo_mapping = {
        "slow-tempo": "lowtempo",
        "moderate-tempo": "moderatetempo",
        "fast-tempo": "hightempo"
    }
    data["tempo"] = tempo_mapping.get(data["tempo"], data["tempo"])

    # Additional transformation for "release_date" key
    if isinstance(data["release_date"], int):
        data["release_date"] = str(data["release_date"])

    return data

def get_recommendations(input_data, tfidf_vectorizer, tfidf_matrix, df):
    # Perform necessary transformations
    text_input_features = ' '.join(map(str, input_data.values()))
    input_vector = tfidf_vectorizer.transform([text_input_features])

    # Perform recommendation based on the transformed input
    cosine_scores = linear_kernel(input_vector, tfidf_matrix).flatten()
    related_indices = cosine_scores.argsort()[::-1]

    # Return top recommendations
    top_recommendations = df.iloc[related_indices[:5]]
    result = top_recommendations.to_dict(orient='records')

    return result