from typing import Any
import os
from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
import pandas as pd
from django.core.exceptions import ValidationError
from conciliaciones.models import Extractos, Mayor, Conciliacion, NoConciliado
from datetime import datetime
import numpy as np
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
handler = logging.handlers.RotatingFileHandler(settings.LOGS_PATH + 'conciliaciones.log', maxBytes=5*1024*1024, backupCount=5)
logger.addHandler(handler)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Create your views here.


@method_decorator(csrf_exempt, name="dispatch")
class ConciliacionesView(View):
    FILE_SIZE_LIMIT = 5 * 1024 * 1024  # 5MB

    def post(self, request):
        self.excel_file = request.FILES["file"]

        # Verifica la extensión del archivo
        if not self.excel_file.name.endswith(
            ".xls"
        ) and not self.excel_file.name.endswith(".xlsx"):
            return JsonResponse(
                {"error": "Invalid file type. Only .xls and .xlsx are accepted."}
            )

        # Verifica el tamaño del archivo (5MB en este ejemplo)
        if self.excel_file.size > self.FILE_SIZE_LIMIT:
            return JsonResponse(
                {"error": "File is too large. Maximum file size is 5MB."}
            )

        data_extractos = pd.read_excel(self.excel_file, sheet_name="EXTRACTO")
        data_mayor = pd.read_excel(self.excel_file, sheet_name="MAYOR")

        self.bank_name = data_extractos.iat[0, 0]  # Accede a la celda A1
        self.period = data_extractos.iat[0, 1]

        try:
            self.create_extractos(data_extractos)
            self.create_mayor(data_mayor)
            return JsonResponse({"message": "Excel file has been processed."})
        except Exception as e:
            return JsonResponse({"error": str(e)})

    def create_extractos(self, data_extractos):
        data_table_estractos = data_extractos.iloc[4:, :5]  # leemos la tabla
        for index, row in data_table_estractos.iterrows():
            try:
                if isinstance(row[0], datetime):
                    fecha = row[0].strftime("%Y-%m-%d")
                elif isinstance(row[0], str):
                    fecha = datetime.strptime(row[0], "%d/%m/%Y").strftime("%Y-%m-%d")
                else:
                    fecha = None
                Extractos.objects.create(
                    fecha=fecha,
                    descripcion=row[1],
                    comprobante=row[2],
                    monto=row[3],
                    codigo=row[4],
                )
            except Exception as e:
                logger.error(str(e))

    def create_mayor(self, data_mayor):
        data_table_mayor = data_mayor.iloc[4:, :4]
        for index, row in data_table_mayor.iterrows():
            try:
                if isinstance(row[0], datetime):
                    fecha = row[0].strftime("%Y-%m-%d")
                elif isinstance(row[0], str):
                    fecha = datetime.strptime(row[0], "%d/%m/%Y").strftime("%Y-%m-%d")
                else:
                    fecha = None
                Mayor.objects.create(
                    fecha=fecha,
                    descripcion=row[1],
                    monto=row[2] if not np.isnan(row[2]) else None,
                    codigo=row[3],
                )
            except Exception as e:
                logger.error(str(e))

    def conciliacion(self):
        try:
            # Use iterators en lugar de obtener todas las instancias de Extractos y Mayor en memoria
            extractos = Extractos.objects.all().iterator()
            mayor = Mayor.objects.all().iterator()

            # Use un diccionario como conjunto de hash para almacenar los objetos Mayor y buscarlos más rápidamente
            mayor_dict = {(m.fecha, m.codigo): m for m in mayor}
            no_conciliados = []

            # Iterate sobre los extractos y busque en el diccionario de mayores en lugar de iterar sobre todos los mayores en cada iteración
            for e in extractos:
                if (e.fecha, e.codigo) in mayor_dict:
                    Conciliacion.objects.create(
                        extracto=e, mayor=mayor_dict[(e.fecha, e.codigo)]
                    )
                else:
                    extracto_no_conciliado = NoConciliado.objects.create(
                        extracto_fecha=e.fecha,
                        extracto_descripcion=e.descripcion,
                        extracto_monto=e.monto,
                    )
                    no_conciliados.append(extracto_no_conciliado)

            # Iterate sobre los mayores que no se conciliaron y cree un objeto NoConciliado para ellos
            for m in Mayor.objects.filter(
                id__not_in=[
                    conciliacion.mayor_id for conciliacion in Conciliacion.objects.all()
                ]
            ):
                try:
                    NoConciliado.objects.create(
                        mayor_fecha=m.fecha,
                        mayor_descripcion=m.descripcion,
                        mayor_monto=m.monto,
                    )
                except ValidationError as e:
                    print(e)
                    logger.error(str(e))
                    return JsonResponse({"error": str(e)})

            # Use JsonResponse en lugar de crear una lista de diccionarios y pasarlo a un objeto JsonResponse
            return JsonResponse(
                {
                    "message": "Excel file has been processed.",
                    "no_conciliados": [
                        {
                            "extracto": {
                                "fecha": nc.extracto_fecha,
                                "descripcion": nc.extracto_descripcion,
                                "monto": nc.extracto_monto,
                            }
                            if nc.extracto_fecha is not None
                            else None,
                            "mayor": {
                                "fecha": nc.mayor_fecha,
                                "descripcion": nc.mayor_descripcion,
                                "monto": nc.mayor_monto,
                            }
                            if nc.mayor_fecha is not None
                            else None,
                        }
                        for nc in no_conciliados
                    ],
                }
            )

        except Exception as e:
            print(e)
            logger.error(str(e))
            return JsonResponse({"error": str(e)})

    def get(self, request, *args, **kwargs):
        return self.conciliacion()
