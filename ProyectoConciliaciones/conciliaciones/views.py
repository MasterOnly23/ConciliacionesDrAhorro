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
from openpyxl import Workbook
from django.http import HttpResponse
from io import BytesIO
from django.core.exceptions import ValidationError
from conciliaciones.models import (
    FileHeaders,
    Extractos,
    Mayor,
    Conciliacion,
    NoConciliado,
)
from datetime import datetime
import numpy as np
import logging
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone


from openpyxl.styles import Font, Border, Alignment, PatternFill
from openpyxl.utils import get_column_letter


logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
handler = logging.handlers.RotatingFileHandler(
    settings.LOGS_PATH + "conciliaciones.log", maxBytes=5 * 1024 * 1024, backupCount=5
)
logger.addHandler(handler)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
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

        newFileName = timezone.now().strftime("%Y-%m-%d") + "-" + file_name
        path = default_storage.save(
            "files/" + newFileName, ContentFile(self.excel_file.read())
        )

        data_extractos = pd.read_excel(
            self.excel_file, sheet_name="EXTRACTO", header=None
        )
        data_mayor = pd.read_excel(self.excel_file, sheet_name="MAYOR", header=None)

        self.bank_name = data_extractos.iat[0, 0].upper()  # Accede a la celda A1
        self.period = data_extractos.iat[0, 1]

        try:
            file_header = FileHeaders.objects.create(
                name=file_name,
                bank_name=self.bank_name,
                periodo=self.period,
            )
            self.create_extractos(data_extractos, file_header)
            self.create_mayor(data_mayor, file_header)
            self.conciliacion(self.bank_name)
            return JsonResponse(
                {
                    "message": "Excel file has been processed.",
                    "bank_name": self.bank_name,
                    "periodo": self.period,
                }
            )
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
                extractos_data.append(
                    Extractos(
                        file_header=file_header,
                        fecha=fecha,
                        descripcion=row[1],
                        comprobante=row[2],
                        monto=row[3],
                        codigo=row[4],
                    )
                )
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
                mayor_data.append(
                    Mayor(
                        file_header=file_header,
                        fecha=fecha,
                        descripcion=row[1],
                        monto=row[2] if not np.isnan(row[2]) else None,
                        codigo=row[3],
                    )
                )
            except Exception as e:
                logger.error(str(e))
        Mayor.objects.bulk_create(mayor_data)

    def conciliacion(self, bank_name):
        try:
            extractos = Extractos.objects.all()
            mayor = Mayor.objects.all()
            no_conciliados = []
            file_header = FileHeaders.objects.all().last()

            try:
                for e in extractos:
                    conciliado = False
                    for m in mayor:
                        if (
                            e.fecha == m.fecha
                            and e.codigo == m.codigo
                            and e.monto == m.monto
                        ):
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
                        if (
                            m.fecha == e.fecha
                            and m.codigo == e.codigo
                            and m.monto == e.monto
                        ):
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
                    # "no_conciliados": [
                    #     {
                    #         "extracto": {
                    #             "fecha": nc.extracto_fecha,
                    #             "descripcion": nc.extracto_descripcion,
                    #             "monto": nc.extracto_monto,
                    #         }if nc.extracto_fecha is not None else None,
                    #         "mayor": {
                    #             "fecha": nc.mayor_fecha,
                    #             "descripcion": nc.mayor_descripcion,
                    #             "monto": nc.mayor_monto,
                    #         }if nc.mayor_fecha is not None else None,
                    #     } for nc in no_conciliados
                    # ],
                }
            )

        except Exception as e:
            print(e)
            logger.error(str(e))
            return JsonResponse({"error": str(e)})

    def get(self, request, *args, **kwargs):
        bankName = request.GET.get("bankName")
        period = request.GET.get("period")
        if bankName and period:
            try:
                file_header = FileHeaders.objects.get(
                    bank_name=bankName, periodo=period
                )
                extractos = Extractos.objects.filter(file_header=file_header)
                mayores = Mayor.objects.filter(file_header=file_header)
                conciliaciones = Conciliacion.objects.filter(file_header=file_header)
                no_conciliados = NoConciliado.objects.filter(file_header=file_header)
                return JsonResponse(
                    {
                            "extractos": [
                                {
                                    "fecha": e.fecha,
                                    "descripcion": e.descripcion,
                                    "comprobante": e.comprobante,
                                    "monto": e.monto,
                                    "codigo": e.codigo,
                                }
                                for e in extractos
                            ],
                            "mayores": [
                                {
                                    "fecha": m.fecha,
                                    "descripcion": m.descripcion,
                                    "monto": m.monto,
                                    "codigo": m.codigo,
                                }
                                for m in mayores
                            ],
                            "conciliaciones": [
                                {
                                    "extracto": {
                                        "fecha": c.extracto.fecha,
                                        "descripcion": c.extracto.descripcion,
                                        "comprobante": c.extracto.comprobante,
                                        "monto": c.extracto.monto,
                                        "codigo": c.extracto.codigo,
                                    },
                                    "mayor": {
                                        "fecha": c.mayor.fecha,
                                        "descripcion": c.mayor.descripcion,
                                        "monto": c.mayor.monto,
                                        "codigo": c.mayor.codigo,
                                    },
                                }
                                for c in conciliaciones
                            ],
                            "no_conciliados": [
                                {
                                    "extracto": (
                                        {
                                            "fecha": nc.extracto_fecha,
                                            "descripcion": nc.extracto_descripcion,
                                            "monto": nc.extracto_monto,
                                        }
                                        if nc.extracto_fecha is not None
                                        else None
                                    ),
                                    "mayor": (
                                        {
                                            "fecha": nc.mayor_fecha,
                                            "descripcion": nc.mayor_descripcion,
                                            "monto": nc.mayor_monto,
                                        }
                                        if nc.mayor_fecha is not None
                                        else None
                                    ),
                                }
                                for nc in no_conciliados
                            ],
                    }
                )
            except FileHeaders.DoesNotExist:
                return JsonResponse(
                    {"error": "No file found for the given bank and period."}
                )


def DownloadPlantilla(request):
    bankName = request.GET.get("bankName")
    period = request.GET.get("period")
    try:
        wb = Workbook()
        default_sheet = wb.active
        wb.remove(default_sheet)

        ws_extracto = wb.create_sheet("EXTRACTO")
        ws_extracto["A1"] = bankName
        ws_extracto["A1"].font = Font(name="Calibri", size=20, bold=True)
        ws_extracto["A1"].alignment = Alignment(horizontal="left")

        ws_extracto["B1"] = period
        ws_extracto["B1"].font = Font(name="Calibri", size=20, bold=True)
        ws_extracto["B1"].alignment = Alignment(horizontal="left")

        header_font = Font(name="Calibri", bold=True)

        headers = ["Fecha", "Descripcion", "Comprobante", "Importe", "Codigo"]
        for col_num, header in enumerate(headers, 1):
            cell = ws_extracto.cell(row=3, column=col_num, value=header)
            cell.font = header_font

        for column in ws_extracto.columns:
            max_length = 0
            column = get_column_letter(
                column[0].column
            )  # Obtener la letra de la columna
            for cell in ws_extracto[column]:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            adjusted_width = max_length + 2
            ws_extracto.column_dimensions[column].width = adjusted_width

        # ajusta size A1 B1
        ws_extracto.column_dimensions[get_column_letter(1)].width = 30
        ws_extracto.column_dimensions[get_column_letter(2)].width = 30


        #MAYOR
        ws_mayor = wb.create_sheet("MAYOR")
        ws_mayor["A1"] = bankName
        ws_mayor["A1"].font = Font(name="Calibri", size=20, bold=True)
        ws_mayor["A1"].alignment = Alignment(horizontal="left")

        ws_mayor["B1"] = period
        ws_mayor["B1"].font = Font(name="Calibri", size=20, bold=True)
        ws_mayor["B1"].alignment = Alignment(horizontal="left")

        headers = ["Fecha", "Descripcion", "Importe", "Codigo"]
        for col_num, header in enumerate(headers, 1):
            cell = ws_mayor.cell(row=3, column=col_num, value=header)
            cell.font = header_font

        for column in ws_mayor.columns:
            max_length = 0
            column = get_column_letter(
                column[0].column
            )  # Obtener la letra de la columna
            for cell in ws_mayor[column]:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            adjusted_width = max_length + 2
            ws_mayor.column_dimensions[column].width = adjusted_width

        # ajusta size A1 B1
        ws_mayor.column_dimensions[get_column_letter(1)].width = 30
        ws_mayor.column_dimensions[get_column_letter(2)].width = 30
        

        # BytesIO guarda el objeto en memoria y no en el disco. se limpia al terminar la funcion
        output = BytesIO()

        wb.save(output)

        response = HttpResponse(
            output.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f"attachment; filename=Conciliaciones {bankName}.xlsx"
        return response
    except Exception as e:
        logger.error(str(e))
        return JsonResponse({"error": str(e)})
