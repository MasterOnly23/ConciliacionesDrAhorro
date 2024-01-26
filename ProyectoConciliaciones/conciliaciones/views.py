from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
from django.core.exceptions import ValidationError

# Create your views here.

FILE_SIZE_LIMIT = 5000 * 1024 # 5MB = 5000KB = 500000

@csrf_exempt
def upload_excel(request):
    if request.method == 'POST':
        excel_file = request.FILES['file']

        # Verifica la extensión del archivo
        if not excel_file.name.endswith('.xls') and not excel_file.name.endswith('.xlsx'):
            return JsonResponse({'error': 'Invalid file type. Only .xls and .xlsx are accepted.'})

        # Verifica el tamaño del archivo (5MB en este ejemplo)
        if excel_file.size > FILE_SIZE_LIMIT:
            return JsonResponse({'error': 'File is too large. Maximum file size is 5MB.'})

        data = pd.read_excel(excel_file)
        # Procesa los datos aquí

        return JsonResponse({'message': 'Excel file has been processed.'})
    else:
        return JsonResponse({'error': 'Invalid request method.'})