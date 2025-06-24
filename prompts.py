def construir_prompt_mejorado(fila):
  return f"""
Eres ANALISTA CX SENIOR. Evalúa esta encuesta de NPS y devuelve un diagnóstico accionable **solo en JSON** (sin comentarios ni texto adicional).  
Idioma: español.

════════════ DATOS ════════════
NPS: {fila['NPS']}      # 0-6 Detractor, 7-8 Neutro, 9-10 Promotor
Requerimiento resuelto (Sí/No): {fila['¿Tu requerimiento fue resuelto en base a lo acordado?']}
Satisfacción resolución (1-7): {fila['Satisfacción con resolución']}
Plazo de resolución cumplido (Sí/No): {fila['Plazo resolución de requerimiento']}
Nivel de esfuerzo (1-5, 1 = mucho esfuerzo): {fila['Nivel de esfuerzo cliente']}
Interacciones requeridas: {fila['Número de interacciones para resolver requerimiento']}
Tipo de caso: {fila['Tipo']}
Subfamilia: {fila['Subfamilia']}
Causa declarada: {fila['Causa']}
Comentario cliente: \"{fila['Walmart LTR - Comentario']}\" 

════════ LISTAS VÁLIDAS ════════
Categorias:
[COMUNICACION, TIEMPO_RESPUESTA, CALIDAD_SOLUCION, NIVEL_ESFUERZO,
 CUMPLIMIENTO_PROMESA, CUMPLIMIENTO_ENTREGA, PRODUCTO_CALIDAD,
 ATENCION_CLIENTE, PROCESO_INTERNO, DEVOLUCION_REEMBOLSO, OTRO]

Ejemplos de causa_principal por categoría:
- COMUNICACION → [Falta_comunicacion, Informacion_inconsistente, No_respuesta, Respuesta_tardia, Seguimiento_insuficiente]
- TIEMPO_RESPUESTA → [Demora_resolucion, Demora_inicio_respuesta, Plazo_incumplido]
- CALIDAD_SOLUCION → [Solucion_parcial, Solucion_inadecuada, Problema_no_resuelto]
- NIVEL_ESFUERZO → [Muchas_interacciones, Proceso_complejo, Autogestion_insuficiente]
- CUMPLIMIENTO_PROMESA → [Reembolso_no_realizado, Compensacion_no_entregada, Promesa_incumplida]
- CUMPLIMIENTO_ENTREGA → [Entrega_no_realizada, Entrega_tardia, Entrega_direccion_incorrecta, Entrega_producto_incorrecto]
- PRODUCTO_CALIDAD → [Producto_defectuoso, Producto_danado, Producto_faltante, Producto_distinto_descripcion]
- ATENCION_CLIENTE → [Mala_atencion_cliente, Mala_atencion_transportista, Atencion_cordial, Atencion_rapida_efectiva]
- PROCESO_INTERNO → [Cancelacion_no_procesada, Cambio_no_gestionado, Factura_incorrecta]
- DEVOLUCION_REEMBOLSO → [Demora_reembolso, Devolucion_incompleta, Retiro_no_gestionado, Proceso_devolucion_complicado]
- OTRO → [Otro]

════════ TAREAS ════════════
1. `tipo_experiencia` → Promotor | Neutro | Detractor.  
2. `categoria` → una de la lista, EXACTA y en mayúsculas.  
3. `causa_principal` → una de la lista permitida para la categoría.  
4. `detalle_analisis` → máx. 35 palabras; justifica causa citando datos.  
5. `emocion_detectada` → emoción dominante (frustracion, alivio, alegria, etc.).  
6. `es_recuperable` → Sí | No (considera NPS, emoción y si se resolvió).  
7. `recomendacion` → máx. 45 palabras; acción concreta y directiva.

════════ FORMATO DE SALIDA ════════════
{{
  "tipo_experiencia": "...",
  "categoria": "...",
  "causa_principal": "...",
  "detalle_analisis": "...",
  "emocion_detectada": "...",
  "es_recuperable": "...",
  "recomendacion": "..."
}}
"""