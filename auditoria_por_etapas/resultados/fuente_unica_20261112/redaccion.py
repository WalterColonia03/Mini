"""Normaliza espacios en el material de trabajo antes de su revisión documental."""
import re
from functools import lru_cache

def preparar(textos):
    words=set(re.findall(r'[a-záéíóúüñ]+', textos.lower()))
    words.update('''fixture snapshots snapshot stock stocks polling rollback commit outbox requestid fefo post get uuid ids id pg php html ui pos ruc sunat igv half up true false null queryset query token tokens log logs logo csrf ascii unicode gtin decimal numeric canario cliente servidor admin almacenero vendedor nov dic lote caja turno catálogo borrador bloquearcierre
    abrir consultar confirmar revisar restaurar probar intentar inspeccionar cambiar comparar repetir pulsar filtrar aplicar seleccionar registrar guardar ingresar modificar resetear reactivar desactivar habilitar deshabilitar avanzar reanudar sincronizar inyectar capturar controlar leer escribir buscar agregar sumar retirar quitar ordenar comprobar navegar exportar descargar actualizar reautenticar recalcular validar documentar retira retirar restablecer declarar configurar
    devuelve descarta conserva indica rechaza incluye informa genera exige permite abre cierra vuelve cumple muestra aplica registra ejecuta revalida recupera habilita duplica muta dejan deja reflejan precede reinicia permanecen permanece corresponde corresponden coinciden coincide separa redirige deniega fija revierte dispara ofrece acepta autoriza pierde sirven sirve filtra cubre distingue inventa omite reparte inventar fingir afirma certifica promete simula presenta deshabilitada reactivada computa
    codigonuevo código nuevo ficticios conocida conocido posterior posteriores previa previo verificado verificada correcta correctos correcto equivocada errónea opuesto otro otra alta activa activo activos inactiva inactivo inactivos antes después luego solo sin con por para como hasta desde entre durante ningún nunca toda todo todas todos cualquier misma mismo únicas únicos correlativo comercial interna interno fiscal aplicable exacto original originales actualizado actual nuevo nueva nuevos nuevas válido válida válidos válidas independiente independientes entero inválido inválida inválidos inválidas controlado fiable máximo mínimo excluido próximo próximos siguientes segundo primera primer segunda destino estado pendiente repetida existentes vista único temporal segura normalizado equivalente legible vacía homogéneo uniforme legítimo remanente acumulado histórico auditado transaccional protegido
    configurar reloj frasco lector teléfono email correo cantidad cantidades día días hoy mañana lunes noviembre diciembre dos tres cuatro cinco siete ocho nueve diez cero una unas unos un uno del de la el los las al y o e a ni no sí si que se su sus es en ha hay tenga tienen tiene están está ya lo le las ser son sea sea falta faltan queda quedan ve ven da van debe deben sido además misma propios propias propia propio otro otros otras más menos igual también tras ahora cuando entonces momento lugar tiempo físico físicos física físicas sin cifras campos conjuntos canónica canónico base bases conocido guardar recibir revisar conservan
    paginar recargar descartar grupo opción campo umbral secuencia código códigos precio precios costo costos montos pago comprador gaveta contados contado suficiente insuficiente responsable cobro compra entrada salida entradas salidas recibidas recibida recibidos recibido vigente vigentes vencida vencido vencidas vencidos nombre nombres apellido unidad unidades únicas mínimas mínima máximas máxima ruta botón mensaje texto badge badges ventana reparto daño robo robo vencimiento categoría categorías lácteos abarrotes arroz yogur leche entera natural producto productos proveedor proveedores pago pagos operación operaciones importe importes motivo motivos carácter caracteres límite límites rango rangos grupo grupos empresa pruebas prueba sumar comparables tiempos impuesto impuestos margen ganancia rentabilidad almacén contraseña claves clave nombre dominio inválida ciudad persona personas último última línea líneas cantidad fila filas acumuladas normal que datos ejemplo referencia referencia requerida requiere origen total impuestos impuesto efectivo dinero recepción recepción posterior inicial inventario historial venta ventas solicitud solicitudes resuelto conocida presente inexistente autenticado dueño cuerpo cliente mensaje min neto bruto falso objetivo medio forma carga unidades saldos sobrescrito manual faltante faltantes sobrante rango papel propia propio número números consultas secciones encabezado archivos valores período períodos años minuto minutos segundos vencimientos rol roles comprobante comprobantes contadores valor conocido protección permiso permisos estado estados botón control total totalizado futura futuro entero enteros automática automático automático real negativo negativa positivo positiva apto alta baja suma formato
    Norte Sol Prueba PruebaSegura PruebaNuevaSegura tienda minimarket leal teclado screenshot cierre apertura config gráfica gráfico navegador sesión sesiones sesión pestaña pestañas orden fin resultado resultados fecha fechas fecha hora muestra modificada rechazada lectura adjunta invalida desactiva resumen trazable legible ilegible requerido requerida requeridas elegibles elegible unidades nombre token total camino
    humano humana permanencia prudente componentes scripts script externos externo externa externo respuesta comparación cierre posteridad descendente ascendente admina adminb a b c d e t s q v op
    '''.lower().split())
    # No reconocer como palabras correctas las concatenaciones del material de trabajo.
    words.update('aislados indicado salvo contextos persistida rechazado rechazados conexiones conexión barrera aportado recuento desarrollar recuperable maestro excluido sintético variantes servicio cantidad declarado completa empresa anterior refinamiento definición dependencia implementación cobertura desconoce verificación ingresan históricamente automáticamente precargado plantilla simulación incompleto error esperada esperado caducado separado separada dañada distinta distintos mismo mismos abierta abierto leído lectura repetido agotada contado contados declarada conocido suspender contexto'.split())
    short={'a','e','o','y','al','de','el','en','es','ha','la','le','lo','me','mi','no','ni','se','si','su','te','tu','un','ya','yo','ir','da','ve'}
    words={w for w in words if w.isalpha() and 3<=len(w)<=24} | short
    @lru_cache(None)
    def split(word):
        low=word.lower()
        if low in words or len(word)<5:return word
        best={0:(0,[])}
        for end in range(1,len(word)+1):
            opts=[]
            for start in range(max(0,end-24),end):
                part=low[start:end]
                if start in best and part in words:
                    score,segments=best[start]
                    opts.append((score+1+(0.2 if len(part)==1 else 0),segments+[word[start:end]]))
            if opts:best[end]=min(opts,key=lambda x:x[0])
        return ' '.join(best[len(word)][1]) if len(word) in best and best[len(word)][0]<=8 else word
    def raw_clean(s):
        phrases={
         'Inyectarfallodespuésdedescontarprimerloteantescommit':'Inyectar fallo después de descontar el primer lote y antes del commit',
         'fixturesintéticoconbasecomparabledocumentada':'fixture sintético con base comparable documentada',
         'Costodesconocidoexcluidodelmargenycoberturaexpuesta':'Costo desconocido excluido del margen y cobertura expuesta',
         'Sinbasecomparableelinformeindica':'Sin base comparable el informe indica',
         'Conbasecomparabledocumentada':'Con base comparable documentada',
         'Retirarevidenciadebasecomparabledecosto':'Retirar evidencia de base comparable del costo',
         'Compararencabezadoconstanciayadvertencias':'Comparar encabezado de constancia y advertencias',
         'Noafirmaqueconsultaequivalgaaconteofísico':'No afirma que la consulta equivalga a conteo físico',
         'Participaciónmonetaria':'Participación monetaria',
         'Permisosidénticosapantalla':'Permisos idénticos a pantalla',
         'Procesardevolucióncondecisión':'Procesar devolución con decisión',
         'Reactivarconfirmando':'Reactivar confirmando','Rechazosnomutan':'Rechazos no mutan','Resueltaúltima':'Resuelta la última',
         'Revisarporcentajes':'Revisar porcentajes','Textoexplicacomprobaciónmanualexterna':'Texto explica comprobación manual externa',
         'archivopeligrosorechazadocontrolado':'archivo peligroso rechazado de forma controlada',
         'bloquearcierre':'bloquear cierre','borraventaoriginal':'borra venta original','catálogoposteriormenteeditado':'catálogo posteriormente editado',
         'codigonuevo':'código nuevo','conalmenosdígito':'con al menos un dígito','confundirventanasni':'confundir ventanas ni',
         'conviertefaltante':'convierte faltante','dañadaregistrabaja':'dañada registra baja','desbloqueani':'desbloquea ni',
         'destinorequierepolíticafuturarefinada':'destino requiere política futura refinada','díassinoperaciónnoseocultan':'días sin operación no se ocultan',
         'ejecutóunreembolso':'ejecutó un reembolso','empatesdesempatadosdeterminísticamente':'empates resueltos con orden determinista',
         'enlazaadetalleautorizadoparaaprobar':'enlaza a detalle autorizado para aprobar','envaseabierto':'envase abierto','errorlongitud':'error de longitud',
         'etiquetascoinciden':'etiquetas coinciden','existenciasnuméricas':'existencias numéricas','existenteINT':'existente INT',
         'hinformativo':'h informativo','logoausentesseñalados':'logo ausentes señalados','logoficticio':'logo ficticio',
         'niimplicarpermisoactual':'ni implicar permiso actual','noafirmaqueelsoftware':'no afirma que el software',
         'noagruparrobovencidocomovencimiento':'no agrupar robo de lote vencido como vencimiento','noevitanbloqueo':'no evitan bloqueo',
         'noexigeexpandirlíneasdentrodelalista':'no exige expandir líneas dentro de la lista','nofiltrardatosglobalesporendpointdescarga':'no filtrar datos globales por el endpoint de descarga',
         'nohayarqueo':'no hay arqueo','noprometevalidaciónbancariaautomática':'no promete validación bancaria automática',
         'novagrupaciones':'nov, agrupaciones','relojdelcliente':'reloj del cliente','repeticiónnoalterna':'repetición no alterna',
         'seisproductosconunidades':'seis productos con unidades','sinconvertir':'sin convertir','sinintegración':'sin integración',
         'sinofreceralaventa':'sin ofrecer a la venta','sinreescribir':'sin reescribir','sintruncarcolumnas':'sin truncar columnas',
         'solicitardescargacom':'solicitar descarga como ','ssinactividadhumana':'s sin actividad humana','trasreembolso':'tras reembolso',
         'usuariosnofiltran':'usuarios no filtran','yarchivopeligroso':'y archivo peligroso','yvercolumnas':'y ver columnas',
         'Íntegravigenteretornaaloteoriginal':'Íntegra vigente retorna al lote original','Últimaconstanciacom':'Última constancia como ',
         'IDsdirectoscom':'IDs directos como ','Filtrointersección':'Filtro por intersección','yalcumplir':'y al cumplir'
        }
        for a,b in sorted(phrases.items(),key=lambda x:-len(x[0])):s=re.sub(re.escape(a),b,s,flags=re.I)
        s=re.sub(r'(ALMACENERO|VENDEDOR|ADMIN|DASH|IGV|NULL|POST|GET|UUID|FEFO|SOL|POS|RUC|SUNAT|PDF|PNG|SVG|ASCII|NUL|GTIN|PG)(?=[a-záéíóúñ])',r'\1 ',s)
        s=re.sub(r'([a-záéíóúüñ])([A-ZÁÉÍÓÚÜÑ])',r'\1 \2',s)
        s=re.sub(r'([A-ZÁÉÍÓÚÜÑ]+)([A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ])',r'\1 \2',s)
        s=re.sub(r'([A-ZÁÉÍÓÚÜÑ])([a-záéíóúüñ]{3,})',lambda m:m[0],s)
        s=re.sub(r'([A-Z]{2,})([a-záéíóúüñ])',r'\1 \2',s)
        s=re.sub(r'[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+',lambda m:m[0] if m[0].isupper() else split(m[0]),s)
        s=re.sub(r'([a-záéíóúüñ])(?=\d)',r'\1 ',s)
        s=re.sub(r'(?<=\d)([a-záéíóúüñ])',r' \1',s)
        s=re.sub(r',(?=[^ \d])',', ',s)
        s=re.sub(r';(?=\S)','; ',s)
        s=re.sub(r'\.(?=[A-ZÁÉÍÓÚÜÑ])','. ',s)
        for a,b in {'Acorrecta':'A correcta','Bno':'B no','conmotivo':'con motivo','sinmotivo':'sin motivo','relóg':'reloj','Confirmaralumbral':'Confirmar al umbral','alcumplir':'al cumplir','alumbral':'al umbral','sinrecuento':'sin recuento','nocon':'no con','comA':'como A','comB':'como B','comADMIN':'como ADMIN','comVENDEDOR':'como VENDEDOR'}.items():s=s.replace(a,b)
        return s
    def clean(s):
        pattern=r'(?:[A-Za-z0-9._+-]+@[A-Za-z0-9.-]+|(?:Prueba|Clave)[A-Za-z0-9!]+|(?:HU|RN|INT|F|CP)-[A-Za-z0-9-]+|[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})'
        pieces=[];start=0
        for m in re.finditer(pattern,s):
            pieces.extend([raw_clean(s[start:m.start()]),m[0]]);start=m.end()
        pieces.append(raw_clean(s[start:]))
        return ''.join(pieces)
    return clean
