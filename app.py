from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, time

app = Flask(__name__)
# Usamos centromed.db como habías configurado
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///centromed.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS DE BASE DE DATOS ---

class Medico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    especialidad = db.Column(db.String(100), nullable=False)
    citas = db.relationship('Cita', backref='medico', lazy=True)

class Paciente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    rut = db.Column(db.String(12), unique=True, nullable=False)
    correo = db.Column(db.String(100))
    celular = db.Column(db.String(20))
    citas = db.relationship('Cita', backref='paciente', lazy=True)
    
class Cita(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha_hora = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'), nullable=False)    
    medico_id = db.Column(db.Integer, db.ForeignKey('medico.id'), nullable=False)

# --- RUTAS DE NAVEGACIÓN ---

@app.route('/')
@app.route('/')
def home():
    """ Página de Dashboard con estadísticas reales """
    hoy = date.today()
    
    citas_hoy = Cita.query.filter(db.func.date(Cita.fecha_hora) == hoy).all()
    
    # Buscamos todos los médicos para el contador de especialistas
    todos_los_medicos = Medico.query.all()
    
    # Enviamos los datos al index.html
    return render_template('index.html', 
                           citas=citas_hoy, 
                           medicos=todos_los_medicos)

@app.route('/seccion-reservas')
def seccion_reservas():
    """ Página con el formulario de reserva """
    todos_los_medicos = Medico.query.all()
    # Especialidades únicas para el filtro
    especialidades = [e[0] for e in db.session.query(Medico.especialidad).distinct().all()]
    # Citas para mostrar el listado
    todas_las_citas = Cita.query.all()
    hoy = date.today().strftime('%Y-%m-%d')
    
    return render_template('reservar.html', 
                           medicos=todos_los_medicos, 
                           especialidades=especialidades, 
                           citas=todas_las_citas,
                           fecha_actual=hoy)

# --- RUTAS DE LÓGICA (API) ---


@app.route('/reservar', methods=['POST'])
def reservar():
    # Obtener datos del formulario
    nombre = request.form.get('nombre_paciente')
    rut = request.form.get('rut_paciente')
    correo = request.form.get('correo_paciente')
    celular = request.form.get('celular_paciente')
    medico_id = request.form.get('medico_id_final')
    hora_str = request.form.get('hora_seleccionada')

    try:
        # Manejar Paciente 
        paciente = Paciente.query.filter_by(rut=rut).first()
        if not paciente:
            paciente = Paciente(nombre=nombre, rut=rut, correo=correo, celular=celular)
            db.session.add(paciente)
        else:
            # Actualizamos datos por si cambiaron
            paciente.correo = correo
            paciente.celular = celular
        
        db.session.commit() # Guardamos paciente para asegurar tener su ID

        # Crear Cita
        fecha_completa = datetime.combine(date.today(), time.fromisoformat(hora_str))
        nueva_cita = Cita(fecha_hora=fecha_completa, paciente_id=paciente.id, medico_id=medico_id)
        
        db.session.add(nueva_cita)
        db.session.commit()

        return redirect(url_for('home', success=1, email=correo))

    except Exception as e:
        db.session.rollback() # Si algo falla, deshacemos cambios
        return f"Error al reservar: {e}"

@app.route('/horas-disponibles/<int:medico_id>')
def horas_disponibles(medico_id):
    # Bloques de atención de 1 hora
    bloques_teoricos = ["09:00", "10:00", "11:00", "12:00", "13:00", "15:00", "16:00", "17:00"]
    
    hoy = date.today()
    citas_hoy = Cita.query.filter(
        Cita.medico_id == medico_id,
        db.func.date(Cita.fecha_hora) == hoy
    ).all()
    
    horas_ocupadas = [c.fecha_hora.strftime("%H:%M") for c in citas_hoy]
    disponibles = [h for h in bloques_teoricos if h not in horas_ocupadas]
    
    return jsonify(disponibles)
# --- GESTIÓN DE RESERVAS (EDITAR / ELIMINAR) ---

@app.route('/mis-reservas')
def mis_reservas():
    citas = Cita.query.order_by(Cita.fecha_hora.asc()).all()
    return render_template('mis_reservas.html', citas=citas)

@app.route('/eliminar-cita/<int:id>')
def eliminar_cita(id):
    cita = Cita.query.get_or_404(id)
    db.session.delete(cita)
    db.session.commit()
    return redirect(url_for('mis_reservas'))

@app.route('/editar-cita/<int:id>', methods=['POST'])
def editar_cita(id):
    cita = Cita.query.get_or_404(id)
    nueva_hora = request.form.get('nueva_hora')
    
    # Actualizamos la fecha/hora manteniendo la fecha de hoy
    cita.fecha_hora = datetime.combine(date.today(), time.fromisoformat(nueva_hora))
    db.session.commit()
    return redirect(url_for('mis_reservas'))

# --- INICIO DE LA APP ---

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8000)