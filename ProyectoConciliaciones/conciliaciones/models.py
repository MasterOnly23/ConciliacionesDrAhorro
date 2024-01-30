from django.db import models
from django.core.exceptions import ValidationError
import re

class FileHeaders(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    periodo = models.CharField(max_length=7)  # Año y mes en formato 'YYYY/MM'
    date_created = models.DateField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def clean(self):
        super().clean()
        if not re.match(r'\d{4}/\d{2}', self.periodo):
            raise ValidationError({'periodo': 'Periodo debe estar en formato YYYY/MM'})

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "File Headers"


class Extractos(models.Model):
    id = models.AutoField(primary_key=True)
    file_header = models.ForeignKey(FileHeaders, on_delete=models.CASCADE, related_name='extractos', null=True,)
    fecha = models.DateField(null=True, blank=True)
    descripcion = models.CharField(max_length=100)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    comprobante = models.CharField(max_length=50)
    codigo = models.CharField(max_length=50)
    observaciones = models.CharField(max_length=100, null=True, blank=True)
    fecha_creacion = models.DateField(auto_now_add=True)
    fecha_modificacion = models.DateField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.descripcion

    class Meta:
        verbose_name_plural = "Extractos"


class Mayor(models.Model):
    id = models.AutoField(primary_key=True)
    file_header = models.ForeignKey(FileHeaders, on_delete=models.CASCADE, related_name='mayores', null=True)
    fecha = models.DateField(null=True, blank=True)
    descripcion = models.CharField(max_length=100)
    monto = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    codigo = models.CharField(max_length=50)
    observaciones = models.CharField(max_length=100, null=True, blank=True)
    fecha_creacion = models.DateField(auto_now_add=True)
    fecha_modificacion = models.DateField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.descripcion

    class Meta:
        verbose_name_plural = "Mayor"


class Conciliacion(models.Model):
    extracto = models.ForeignKey(Extractos, on_delete=models.CASCADE)
    mayor = models.ForeignKey(Mayor, on_delete=models.CASCADE)
    fecha = models.DateField(null=True, blank=True)
    fecha_conciliacion = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Conciliación: {self.extracto} - {self.mayor}"

    class Meta:
        verbose_name_plural = "Conciliaciones"


class NoConciliado(models.Model):
    extracto_fecha = models.DateField(null=True, blank=True)
    extracto_descripcion = models.CharField(max_length=255)
    extracto_monto = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    mayor_fecha = models.DateField(null=True, blank=True)
    mayor_descripcion = models.CharField(max_length=255)
    mayor_monto = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
