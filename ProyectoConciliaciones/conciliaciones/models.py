from django.db import models

# Create your models here.


class Extractos(models.Model):
    id = models.AutoField(primary_key=True)
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
    fecha_conciliacion = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Conciliación: {self.extracto} - {self.mayor}"

    class Meta:
        verbose_name_plural = "Conciliaciones"
