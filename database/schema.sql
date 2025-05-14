Table Barrios {
  id integer [primary key]
  nombre varchar
  contacto varchar
  created_at timestamp
}

Table Lotes {
  id integer [primary key]
  numero varchar
  barrio_id integer [ref: > Barrios.id]
  created_at timestamp
}

Table Propietarios {
  id integer [primary key]
  nombre varchar
  dni varchar
  email varchar
  telefono varchar
  lote_id integer [ref: > Lotes.id]
  created_at timestamp
}

Table PersonalSeguridad {
  id integer [primary key]
  nombre varchar
  dni varchar
  email varchar
  turno enum('mañana', 'tarde', 'noche')
  barrio_id integer [ref: > Barrios.id]
  created_at timestamp
}

Table Visitas {
  id integer [primary key]
  propietario_id integer [ref: > Propietarios.id]
  nombre_visitante varchar
  dni_visitante varchar
  fecha_visita date
  hora_inicio time
  hora_fin time
  estado enum('pendiente', 'ingresado', 'egresado', 'cancelado', 'vencido')
  qr_generado boolean
  qr_usado boolean
  registro_ingreso timestamp
  registro_egreso timestamp
  created_at timestamp
}

Table Movimientos {
  id integer [primary key]
  propietario_id integer [ref: > Propietarios.id]
  tipo enum('ingreso', 'egreso')
  timestamp datetime
  escaneado_por integer [ref: > PersonalSeguridad.id]
  exito boolean
}

Table ActividadesSeguridad {
  id integer [primary key]
  seguridad_id integer [ref: > PersonalSeguridad.id]
  tipo_actividad enum('escanear_qr', 'alerta_recibida', 'acceso_denegado', 'protocolo_emergencia')
  descripcion text
  timestamp datetime
}
