from rest_framework.decorators import api_view
from rest_framework.response import Response
from .utils.optimize import optimize_data
from django.http import JsonResponse

import pandas as pd
import numpy as np

from .utils import Script_Maestro, optimize, Suma_ponderada_funciones, Bus_lex

from .utils.Script_Maestro import optimize_from_excel

@api_view(['POST'])
def optimizeScript(request):

    excel_file = request.FILES.get("excel_file")
    df = pd.read_excel(excel_file)

    if not excel_file:
        return Response({"error": "No file uploaded"}, status=400)

    # Validate the file extension
    file_extension = excel_file.name.split('.')[-1].lower()
    if file_extension not in ['xlsx', 'xls']:
        return JsonResponse({"error": "Invalid file type. Please upload an Excel file."}, status=400)

    try:
        optimized_data = optimize_from_excel(excel_file)

        return Response({"optimized_excel_file": optimized_data})

    except Exception as e:
        return Response({"error": str(e)}, status=500)