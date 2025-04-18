from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from .utils.optimize import optimize_data
from django.http import JsonResponse

import pandas as pd
import numpy as np

from .utils import optimize

@api_view(['POST'])
def processData(request):
    excel_file = request.FILES.get("excel_file")

    if not excel_file:
        return Response({"error": "No file uploaded"}, status=400)

    try:
        df = pd.read_excel(excel_file)

        # Reemplaza NaN por None
        df = df.replace({np.nan: None})

        # Convierte el DataFrame a una lista de diccionarios
        data = df.to_dict(orient='records')

        return Response(data, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
def optimizeData(request):
    try:
        # Get the data (which should be a list of dictionaries from processData)
        data = request.data  
        
        # Convert the list of dictionaries into a pandas DataFrame
        df = pd.DataFrame(data)

        # Call your optimization function (optimize_data)
        result = optimize_data(df)  # This will sum the "Q2 95" column (or perform other operations in the future)

        # Return the result back to the frontend
        return Response({"optimize": result}, status=200)

    except Exception as e:
        # Handle any errors that occur
        return Response({"error": str(e)}, status=500)