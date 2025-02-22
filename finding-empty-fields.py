import arcpy
import os
from datetime import datetime

def main():
    # Obtener parámetros de entrada
    input_gdb = arcpy.GetParameterAsText(0)
    output_txt = arcpy.GetParameterAsText(1)
    
    # Validar la entrada
    if not arcpy.Exists(input_gdb):
        arcpy.AddError("La geodatabase especificada no existe")
        return
    
    # Crear archivo de texto para el reporte
    try:
        with open(output_txt, 'w', encoding='utf-8') as f:
            # Escribir encabezado del reporte
            f.write(f"Reporte de Análisis de Valores Nulos\n")
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Geodatabase: {input_gdb}\n")
            f.write("=" * 50 + "\n\n")
            
            # Obtener lista de datasets en la geodatabase
            arcpy.env.workspace = input_gdb
            feature_classes = []
            
            # Obtener feature classes en la raíz
            feature_classes.extend(arcpy.ListFeatureClasses())
            
            # Obtener feature classes dentro de feature datasets
            for ds in arcpy.ListDatasets("", "Feature"):
                feature_classes.extend([os.path.join(ds, fc) for fc in arcpy.ListFeatureClasses(feature_dataset=ds)])
            
            # Obtener tablas
            tables = arcpy.ListTables()
            
            # Analizar feature classes
            for fc in feature_classes:
                analyze_element(fc, f, "Feature Class")
                
            # Analizar tablas
            for table in tables:
                analyze_element(table, f, "Tabla")
                
        arcpy.AddMessage(f"Reporte generado exitosamente en: {output_txt}")
        
    except Exception as e:
        arcpy.AddError(f"Error al procesar la geodatabase: {str(e)}")
        return

def analyze_element(element, file_handle, element_type):
    """Analiza un elemento (feature class o tabla) en busca de campos con valores nulos"""
    try:
        # Obtener el total de registros
        total_records = int(arcpy.GetCount_management(element)[0])
        
        file_handle.write(f"\n{element_type}: {element}\n")
        file_handle.write(f"Total de registros: {total_records}\n")
        
        if total_records == 0:
            file_handle.write("El elemento no contiene registros\n")
            return
            
        # Analizar cada campo
        fields = arcpy.ListFields(element)
        found_nulls = False
        
        for field in fields:
            # Excluir campos de sistema y geometría
            if field.type in ['OID', 'Geometry'] or field.name in ['Shape', 'SHAPE', 'OBJECTID']:
                continue
                
            # Contar valores nulos
            null_count = 0
            with arcpy.da.SearchCursor(element, [field.name]) as cursor:
                for row in cursor:
                    if row[0] is None or (isinstance(row[0], str) and row[0].strip() == ''):
                        null_count += 1
            
            # Reportar si hay valores nulos
            if null_count > 0:
                found_nulls = True
                if null_count == total_records:
                    file_handle.write(f"Campo '{field.name}': TODOS LOS REGISTROS SON NULOS\n")
                else:
                    file_handle.write(f"Campo '{field.name}': {null_count} registros nulos de {total_records} ({(null_count/total_records)*100:.1f}%)\n")
        
        if not found_nulls:
            file_handle.write("No se encontraron campos con valores nulos\n")
            
        file_handle.write("-" * 50 + "\n")
        
    except Exception as e:
        arcpy.AddWarning(f"Error al analizar {element}: {str(e)}")
        file_handle.write(f"Error al analizar el elemento: {str(e)}\n")
        file_handle.write("-" * 50 + "\n")

if __name__ == '__main__':
    main()