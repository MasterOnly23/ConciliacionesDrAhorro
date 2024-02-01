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
from conciliaciones.models import FileHeaders, Extractos, Mayor, Conciliacion, NoConciliado
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
        file_name = self.excel_file.name

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

        data_extractos = pd.read_excel(self.excel_file, sheet_name="EXTRACTO", header=None)
        data_mayor = pd.read_excel(self.excel_file, sheet_name="MAYOR", header=None)

        self.bank_name = data_extractos.iat[0, 0]  # Accede a la celda A1
        self.period = data_extractos.iat[0, 1]
    

        try:
            file_header = FileHeaders.objects.create(
                name = file_name,
                periodo = self.period,
            )
            self.create_extractos(data_extractos, file_header)
            self.create_mayor(data_mayor, file_header)
            return JsonResponse({"message": "Excel file has been processed."})
        except Exception as e:
            return JsonResponse({"error": str(e)})

    def create_extractos(self, data_extractos, file_header):
        data_table_estractos = data_extractos.iloc[4:, :5]  # leemos la tabla
        extractos_data = []
        for index, row in data_table_estractos.iterrows():
            try:
                if isinstance(row[0], datetime):
                    fecha = row[0].strftime("%Y-%m-%d")
                elif isinstance(row[0], str):
                    fecha = datetime.strptime(row[0], "%d/%m/%Y").strftime("%Y-%m-%d")
                else:
                    fecha = None
                extractos_data.append(Extractos(
                    file_header=file_header,
                    fecha=fecha,
                    descripcion=row[1],
                    comprobante=row[2],
                    monto=row[3],
                    codigo=row[4],
                ))
            except Exception as e:
                logger.error(str(e))
        Extractos.objects.bulk_create(extractos_data)

    def create_mayor(self, data_mayor, file_header):
        data_table_mayor = data_mayor.iloc[4:, :4]
        mayor_data = []
        for index, row in data_table_mayor.iterrows():
            try:
                if isinstance(row[0], datetime):
                    fecha = row[0].strftime("%Y-%m-%d")
                elif isinstance(row[0], str):
                    fecha = datetime.strptime(row[0], "%d/%m/%Y").strftime("%Y-%m-%d")
                else:
                    fecha = None
                mayor_data.append(Mayor(
                    file_header=file_header,
                    fecha=fecha,
                    descripcion=row[1],
                    monto=row[2] if not np.isnan(row[2]) else None,
                    codigo=row[3],
                ))
            except Exception as e:
                logger.error(str(e))
        Mayor.objects.bulk_create(mayor_data)

    def conciliacion(self):
        try:
            extractos = Extractos.objects.all()
            mayor = Mayor.objects.all()
            no_conciliados = []
            file_header = FileHeaders.objects.all().last()

            try:
                for e in extractos:
                    conciliado = False
                    for m in mayor:
                        if e.fecha == m.fecha and e.codigo == m.codigo and e.monto == m.monto:
                            Conciliacion.objects.create(
                                file_header=file_header,
                                extracto=e,
                                mayor=m,
                            )
                            conciliado = True
                            break
                    if not conciliado:
                        no_conciliado = NoConciliado.objects.create(
                            file_header=file_header,
                            extracto_fecha=e.fecha,
                            extracto_descripcion=e.descripcion,
                            extracto_monto=e.monto,
                        )
                        no_conciliados.append(no_conciliado)
            except ValidationError as e:
                print(e)
                logger.error(str(e))
                return JsonResponse({"error": str(e)})

            try:
                for m in mayor:
                    conciliado = False
                    for e in extractos:
                        if m.fecha == e.fecha and m.codigo == e.codigo and m.monto == e.monto:
                            Conciliacion.objects.create(
                                file_header=file_header,
                                extracto=e,
                                mayor=m,
                            )
                            conciliado = True
                            break
                    if not conciliado:
                        no_conciliado = NoConciliado.objects.create(
                            file_header=file_header,
                            mayor_fecha=m.fecha,
                            mayor_descripcion=m.descripcion,
                            mayor_monto=m.monto,
                        )
                        no_conciliados.append(no_conciliado)
            except ValidationError as e:
                print(e)
                logger.error(str(e))
                return JsonResponse({"error": str(e)})

            return JsonResponse(
                {
                    "message": "Excel file has been processed.",
                    "no_conciliados": [
                        {
                            "extracto": {
                                "fecha": nc.extracto_fecha,
                                "descripcion": nc.extracto_descripcion,
                                "monto": nc.extracto_monto,
                            }if nc.extracto_fecha is not None else None,
                            "mayor": {
                                "fecha": nc.mayor_fecha,
                                "descripcion": nc.mayor_descripcion,
                                "monto": nc.mayor_monto,
                            }if nc.mayor_fecha is not None else None,
                        } for nc in no_conciliados
                    ],
                }
            )

        except Exception as e:
            print(e)
            logger.error(str(e))
            return JsonResponse({"error": str(e)})


    def get(self, request, *args, **kwargs):
        return self.conciliacion()
