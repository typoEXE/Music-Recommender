
## Build and Deployment

This music recommendation engine was created to be deployed via Microsoft Azure, specifically utilizing Azure Functions and Azure ML.

Start by downloading the following files: music_recommender_v6.ipynb, model_deployment.ipynb, preprocessed_data.csv, tfidf_maxtrix.pkl, tfidf_vectorizer.pkl, and azure_function.py. 

Once you have downloaded these files, you will need to create two Azure workspaces. One will be an Azure Functions workspace, the other will be an Azure ML workspace. More information about this process can be found here: https://learn.microsoft.com/en-us/azure/azure-functions/functions-create-function-app-portal and here: https://learn.microsoft.com/en-us/azure/machine-learning/quickstart-create-resources?view=azureml-api-2. 

Once you have created the workspaces, you will upload the files you downloaded earlier. The two .ipynb files will be uploaded to the ML workspace, and azure_function.py is the code for the Azure Functions workspace. Also upload the preprocessed_data.csv, and the two .pkl files to the ML workspace. 

Once you have everything uploaded, run the two .ipynb files to verify that everything is working. 

Next, we set up the azure function. To do this, we are going to have to replace some strings in azure_function.py, specifically:

```python
# Read the connection string from the environment variable
connection_string = "DefaultEndpointsProtocol=https;AccountName=YOUR_ACCOUNT_NAME;AccountKey=YOUR_ACCOUNT_KEY;EndpointSuffix=core.windows.net"
# Read the container name from the environment variable
container_name = "YOUR_CONTAINER_NAME_HERE"
```
You will have to replace "YOUR_ACCOUNT_NAME" with the name of the Azure account you utilized to create the workspaces, "YOUR_ACCOUNT_KEY" with the access key for that account, and "YOUR_CONTAINER_NAME_HERE" with the name of your container.

Finally, we need to configure the endpoint. Navigate to the Integration view for your function. Set the trigger to be an HTTP request, set inputs to no inputs defined, set the function to api_recommend, and the output to be HTTP ($return). Once completed, you should be able to send HTTP requests to the function at the the address that Azure generated for it.