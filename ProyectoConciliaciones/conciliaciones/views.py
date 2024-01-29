from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
import pandas as pd
from django.core.exceptions import ValidationError
from conciliaciones.models import Extractos, Mayor, Conciliacion
from datetime import datetime
import numpy as np

# Create your views here.

@method_decorator(csrf_exempt, name='dispatch')
class UploadExcelView(View):
    FILE_SIZE_LIMIT = 5 * 1024 * 1024  # 5MB

    def post(self, request):
        excel_file = request.FILES["file"]

        # Verifica la extensión del archivo
        if not excel_file.name.endswith(".xls") and not excel_file.name.endswith(".xlsx"):
            return JsonResponse(
                {"error": "Invalid file type. Only .xls and .xlsx are accepted."}
            )

        # Verifica el tamaño del archivo (5MB en este ejemplo)
        if excel_file.size > self.FILE_SIZE_LIMIT:
            return JsonResponse({"error": "File is too large. Maximum file size is 5MB."})

        data_extractos = pd.read_excel(excel_file, sheet_name="EXTRACTO")
        data_mayor = pd.read_excel(excel_file, sheet_name="MAYOR")

        bank_name = data_extractos.iat[0, 0]  # Accede a la celda A1
        period = data_extractos.iat[0, 1]

        self.create_extractos(data_extractos)
        self.create_mayor(data_mayor)

        return JsonResponse({"message": "Excel file has been processed."})

    def create_extractos(self, data_extractos):
        data_table_estractos = data_extractos.iloc[4:, :5]  # leemos la tabla
        for index, row in data_table_estractos.iterrows():
            if isinstance(row[0], datetime):
                fecha = row[0].strftime('%Y-%m-%d')
            elif isinstance(row[0], str):
                fecha = datetime.strptime(row[0], '%d/%m/%Y').strftime('%Y-%m-%d')
            else:
                fecha = None
            Extractos.objects.create(
                fecha=fecha,
                descripcion=row[1],
                comprobante=row[2],
                monto=row[3],
                codigo=row[4],
            )

    def create_mayor(data_mayor):
        data_table_mayor = data_mayor.iloc[4:, :4]
        for index, row in data_table_mayor.iterrows():
            if isinstance(row[0], datetime):
                fecha = row[0].strftime('%Y-%m-%d')
            elif isinstance(row[0], str):
                fecha = datetime.strptime(row[0], '%d/%m/%Y').strftime('%Y-%m-%d')
            else:
                fecha = None

            monto = row[2] if not np.isnan(row[2]) else None
            Mayor.objects.create(
                fecha=fecha,
                descripcion=row[1],
                monto=monto,
                codigo=row[3],
            )