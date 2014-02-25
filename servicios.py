# -*- coding: utf-8 -*-
"""
Created on Fri Jan 31 12:49:31 2014

@author: Adrián
"""

from bottle import route, run, response, request
import tests_no_parametricos as tnp
import re, os

lista_ficheros = {}

def leer_datos(ruta_archivo):
    """
    Función que lee el fichero de datos que contiene los datos sobre los que se aplican los tests.

    Argumentos
    ----------
    ruta_archivo: string
        Ruta absoluta del fichero a abrir.
        
    Salida
    ------
    tuple:
        palabra: string
            Palabra que sale antes de la primera coma
        nombres_conj_datos: list
            Nombres de los conjuntos de datos (diferentes).
        nombres_algoritmos: list
            Nombres de los algoritmos (diferentes).
        matriz_datos: list
            Lista de listas que contiene las listas de los diferentes conjuntos de datos.
		nombre_fichero: string
			Nombre fichero con extensión.
    descripcion_error: string
        Cadena que contiene un mensaje de error. Será la única salida en caso de error
        
    Tipos de errores
    ----------------
    Nombre algoritmo repetido\n
    Nombre conjunto datos repetido\n
    Error dato linea (El dato no es un número válido)\n
    Error formato datos (La estructura de los datos presentados no es correcta)\n
    Deben existir al menos dos algoritmos\n
    """
    patron_numeros = re.compile('^\d+(\.{1}\d+)?$')
    descripcion_error = ""
    palabra = ""
    nombres_conj_datos = []
    nombres_algoritmos = []
    matriz_datos = []
    nombre_fichero = ""
    f = open(ruta_archivo,"r")
    numero_linea = 0
    error = 0
    while not error:
        linea = f.readline()
        if not linea:
            break
        tokens = re.split(",",linea)
        if numero_linea == 0:
            for i in range(len(tokens)):
                if i == 0:
                    palabra = tokens[i]
                else:
                    nombre = tokens[i].replace("\n","")
                    if nombres_algoritmos.count(nombre) == 0:
                        nombres_algoritmos.append(nombre)
                    else:
                        descripcion_error = "Nombre algoritmo repetido"
                        error = 1
                        break
        else:
            lista_datos = []
            for i in range(len(tokens)):
                if i == 0:
                    if nombres_conj_datos.count(tokens[i]) == 0:
                        nombres_conj_datos.append(tokens[i])
                    else:
                        descripcion_error = "Nombre conjunto datos repetido"
                        error = 1
                        break
                else:
                    m = patron_numeros.match(tokens[i])
                    if m:
                        dato = float(tokens[i])
                        lista_datos.append(dato)
                    else:
                        descripcion_error = "Error dato linea" , numero_linea
                        error = 1
                        break
            matriz_datos.append(lista_datos)
        numero_linea += 1
        
    nombre_fichero = os.path.basename(ruta_archivo)

    numero_algoritmos = len(nombres_algoritmos)
    for i in matriz_datos:
        if len(i) != numero_algoritmos:
            descripcion_error = "Error formato datos"
            error = 1
            break
    if numero_algoritmos < 2:
        descripcion_error = "Deben existir al menos dos algoritmos"
        error = 1

    if not error:
        return palabra, nombres_conj_datos, nombres_algoritmos, matriz_datos, nombre_fichero
    else:
        return descripcion_error

#Servicio para la subida de ficheros.
@route('/subir', method='POST')
def subir_fichero():
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.content_type = "application/json"
    subida = request.files.get('fichero')
    nombre, extension = os.path.splitext(subida.filename)
    if extension not in ('.csv'):
        return {"fallo" : "Extension no permitida"}
    else:
        #Búsqueda del fichero en la lista de ficheros en el servidor.
        for clave in lista_ficheros.keys():
            if lista_ficheros[clave][4] == subida.filename:
                return {"fallo" : "El fichero \"" + subida.filename + "\" ya se encuentra el servidor"}
        #Si no está en el servidor se busca el directorio del archivo en /home.
        ruta = ""
        for root, dirs, files in os.walk("/home"):
            if subida.filename in files:
                ruta = os.path.join(root, subida.filename)
        #Se procesa y se guarda en el diccionario de archivos "lista_ficheros".
        datos = leer_datos(ruta)
        clave_hash = hash(subida.file)
        lista_ficheros[clave_hash] = datos
        #Devolución de la lista de ficheros (hash-nombre).
        clave_nombre = {}
        for clave in lista_ficheros.keys():
            clave_nombre[clave] = lista_ficheros[clave][4]
        return clave_nombre

#Servicio para la consula de ficheros.
@route('/consultar/<id_fichero:int>', method='GET')
def consultar_fichero(id_fichero):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.content_type = "application/json"
    #Consulta del contenido de un fichero en concreto.
    contenido = {}
    for clave in lista_ficheros.keys():
        if clave == id_fichero:
            contenido["palabra"] = lista_ficheros[clave][0]
            contenido["nombres_conj_datos"] = lista_ficheros[clave][1]
            contenido["nombres_algoritmos"] = lista_ficheros[clave][2]
            contenido["matriz_datos"] = lista_ficheros[clave][3]
            contenido["nombre_fichero"] = lista_ficheros[clave][4]
    return contenido

@route('/wilcoxon/<id_fichero:int>', method="GET")
@route('/wilcoxon/<id_fichero:int>/<alpha:float>', method="GET")
def wilcoxon_test(id_fichero, alpha=0.05):
    """
    Servicio web para el test de los rangos signados de Wilcoxon
    
    Argumentos
    ----------
    id_fichero: int
        Identificador HASH del fichero sobre el que se quiere aplicar el test
    alpha: string
        Nivel de significancia. Probabilidad de rechazar la hipótesis nula siendo cierta
        
    Salida
    ------
    resultado: dict (JSON)
        Resultado devuelto al aplicar el test de Wilcoxon
    """
    datos = lista_ficheros[id_fichero]
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.content_type = "application/json"
    resultado = tnp.wilcoxon_test(datos[3],alpha)
    return resultado
        
@route('/friedman/<id_fichero:int>', method="GET")
@route('/friedman/<id_fichero:int>/<alpha:float>', method="GET")
@route('/friedman/<id_fichero:int>/<tipo:int>', method="GET")
@route('/friedman/<id_fichero:int>/<alpha:float>/<tipo:int>', method="GET")
def friedman_test(id_fichero, alpha=0.05, tipo=0):
    """
    Servicio web para el test de Friedman
    
    Argumentos
    ----------
    id_fichero: int
        Identificador HASH del fichero sobre el que se quiere aplicar el test
    alpha: string
        Nivel de significancia. Probabilidad de rechazar la hipótesis nula siendo cierta
    tipo: string
        Indica si lo que se quiere es minimizar ("0") o maximizar ("1")
        
    Salida
    ------
    resultado: dict (JSON)
        Resultado devuelto al aplicar el test de Friedman
    """
    datos = lista_ficheros[id_fichero]
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.content_type = "application/json"
    resultado = tnp.friedman_test(datos[2],datos[3],alpha,tipo)
    return resultado

@route('/iman-davenport/<id_fichero:int>', method="GET")
@route('/iman-davenport/<id_fichero:int>/<alpha:float>', method="GET")
@route('/iman-davenport/<id_fichero:int>/<tipo:int>', method="GET")
@route('/iman-davenport/<id_fichero:int>/<alpha:float>/<tipo:int>', method="GET")
def iman_davenport_test(id_fichero, alpha=0.05, tipo=0):
    """
    Servicio web para el test de Iman-Davenport
    
    Argumentos
    ----------
    id_fichero: int
        Identificador HASH del fichero sobre el que se quiere aplicar el test
    alpha: string
        Nivel de significancia. Probabilidad de rechazar la hipótesis nula siendo cierta
    tipo: string
        Indica si lo que se quiere es minimizar ("0") o maximizar ("1")
        
    Salida
    ------
    resultado: dict (JSON)
        Resultado devuelto al aplicar el test de Iman-Davenport
    """
    datos = lista_ficheros[id_fichero]
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.content_type = "application/json"
    resultado = tnp.iman_davenport_test(datos[2],datos[3],alpha,tipo)
    return resultado

@route('/rangos-alineados/<id_fichero:int>', method="GET")
@route('/rangos-alineados/<id_fichero:int>/<alpha:float>', method="GET")
@route('/rangos-alineados/<id_fichero:int>/<tipo:int>', method="GET")
@route('/rangos-alineados/<id_fichero:int>/<alpha:float>/<tipo:int>', method="GET")
def friedman_rangos_alineados_test(id_fichero, alpha=0.05, tipo=0):
    """
    Servicio web para el test de los Rangos Alineados de Friedman
    
    Argumentos
    ----------
    id_fichero: int
        Identificador HASH del fichero sobre el que se quiere aplicar el test
    alpha: string
        Nivel de significancia. Probabilidad de rechazar la hipótesis nula siendo cierta
    tipo: string
        Indica si lo que se quiere es minimizar ("0") o maximizar ("1")
        
    Salida
    ------
    resultado: dict (JSON)
        Resultado devuelto al aplicar el test de los Rangos Alineados de Friedman
    """
    datos = lista_ficheros[id_fichero]
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.content_type = "application/json"
    resultado = tnp.friedman_rangos_alineados_test(datos[2],datos[3],alpha,tipo)
    return resultado

run(reloader=True, host='localhost', port=8080)
