from app import app, db, Medico

def poblar_datos():
    with app.app_context():
        # 1. Limpiamos la base de datos (opcional, por si quieres empezar de cero)
        db.drop_all()
        db.create_all()

        # 2. Definimos una lista de médicos con sus especialidades
        datos_medicos = [
            {"nombre": "Dr. Rodolfo Sanhueza", "especialidad": "Medicina General"},
            {"nombre": "Dra. Romina Ulloa", "especialidad": "Medicina General"},
            {"nombre": "Dr. Carlos Carranza", "especialidad": "Pediatría"},
            {"nombre": "Dra. Roxana Mellado", "especialidad": "Pediatría"},
            {"nombre": "Dr. Hans Marcel", "especialidad": "Cardiología"},
            {"nombre": "Dra. Pamela Grey", "especialidad": "Cirugía"},
            {"nombre": "Dr. Maximiliano Strange", "especialidad": "Neurocirugía"}
        ]

        # 3. Los insertamos en la base de datos
        for datos in datos_medicos:
            nuevo = Medico(nombre=datos["nombre"], especialidad=datos["especialidad"])
            db.session.add(nuevo)
        
        db.session.commit()
        print("¡Base de datos poblada con éxito!")

if __name__ == '__main__':
    poblar_datos()