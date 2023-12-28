# Sistema de Conciliaciones Bancarias - Farmacias Dr Ahorro

![Farmacias Dr Ahorro Logo](ProyectoConciliaciones/ProyectoConciliaciones/static/logo.png)


## Descripción del Proyecto

Este repositorio alberga el código fuente y la documentación asociada al sistema de conciliaciones bancarias desarrollado para Farmacias Dr Ahorro. El proyecto utiliza Django para el backend y React para el frontend. El objetivo principal es proporcionar una herramienta eficiente y fácil de usar para realizar conciliaciones bancarias de manera efectiva, teniendo en cuenta múltiples bancos con los que la empresa tiene transacciones.

## Características Principales

- **Conciliaciones Multibanco:** El sistema permite realizar conciliaciones bancarias para múltiples bancos simultáneamente, facilitando la gestión de las transacciones financieras de Farmacias Dr Ahorro.

- **Interfaz Intuitiva:** La interfaz de usuario ha sido diseñada utilizando React para ser intuitiva y fácil de usar, permitiendo a los usuarios realizar conciliaciones de manera eficiente sin necesidad de conocimientos técnicos avanzados.

- **Seguridad:** Se han implementado medidas de seguridad robustas, aprovechando las capacidades de Django, para proteger la información financiera sensible durante el proceso de conciliación.

## Requisitos del Sistema

Asegúrese de tener instaladas las siguientes dependencias antes de ejecutar el sistema:

```bash
'asgiref==3.7.2'
'Django==4.2.8'
'mssql-django==1.3'
'pyodbc==5.0.1'
'python-decouple==3.8'
'pytz==2023.3.post1'
'sqlparse==0.4.4'
'typing_extensions==4.9.0'
'tzdata==2023.3'


Para instalar estas dependencias, puede usar el siguiente comando:
pip install -r requirements.txt

Guía de Instalación
1. Clone este repositorio: git clone https://github.com/tu_usuario/nombre_del_repositorio.git
2. Navegue al directorio del proyecto: cd nombre_del_repositorio
3. Instale las dependencias de Django: pip install -r requirements.txt
4.Navegue al directorio del frontend (React) y instale las dependencias: cd frontend && npm install
5. Vuelva al directorio principal: cd ..
6. Inicie la aplicación Django: python manage.py runserver
7. Inicie el servidor de desarrollo de React: cd frontend && npm start


Contribución
¡Agradecemos las contribuciones! Si desea contribuir a este proyecto, siga estos pasos:

1. Haga un fork del repositorio.
2. Cree una nueva rama para su función: git checkout -b nombre-de-la-funcion
3. Realice los cambios y haga commit: git commit -m 'Añadir nueva función'
3. Envíe los cambios a su repositorio en GitHub: git push origin nombre-de-la-funcion
4. Abra un Pull Request en este repositorio.


Licencia
Este proyecto está bajo la licencia [Farmacias Dr Ahorro]. Consulte el archivo LICENSE para obtener más detalles.

Contacto
Para cualquier pregunta o comentario, póngase en contacto con [Juan Felipe Daza] a través de [pipedaza23@email.com].