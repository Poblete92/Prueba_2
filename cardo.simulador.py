import os
import random
from pymongo import MongoClient
from datetime import datetime

# Conexión a MongoDB
cliente = MongoClient("mongodb://localhost:27017/")
db = cliente["cardo"]
coleccion_partidas = db["partidas"]

# Limpia la consola
def limpiar_consola():
    os.system('cls' if os.name == 'nt' else 'clear')

# Obtener 3 cartas de diferentes categorías
def obtener_cartas_distintas():
    categorias = ["situaciones", "objetos", "emociones", "lugares"]
    cartas = []
    usadas = random.sample(categorias, 3)
    for cat in usadas:
        carta = db[cat].aggregate([{"$sample": {"size": 1}}])
        cartas.append(next(carta))
    return cartas

# Iniciar el juego
def iniciar_partida():
    print("🃏 Bienvenido a Cardo 🃏")
    jugador1 = input("Nombre del Jugador 1: ")
    jugador2 = input("Nombre del Jugador 2: ")
    
    try:
        rondas = int(input("¿Cuántas rondas jugarán? (3 a 10): "))
        if rondas < 3 or rondas > 10:
            print("Número inválido. Se jugarán 5 rondas.")
            rondas = 5
    except:
        print("Entrada inválida. Se jugarán 5 rondas.")
        rondas = 5

    # Crear registro inicial de la partida en MongoDB
    partida = {
        "jugador1": jugador1,
        "jugador2": jugador2,
        "rondas": rondas,
        "fecha_inicio": datetime.now(),
        "detalle_rondas": [],
        "puntaje": {
            jugador1: 0,
            jugador2: 0
        }
    }

    id_partida = coleccion_partidas.insert_one(partida).inserted_id

    limpiar_consola()
    print("¡Comienza la partida!")
    return jugador1, jugador2, rondas, id_partida

def jugar_rondas(j1, j2, rondas, id_partida):
    jugadores = [j1, j2]
    for ronda in range(rondas):
        print(f" **Ronda** {ronda + 1}")
        
        # Alternar roles
        cardoelector = jugadores[ronda % 2]
        cardomante = jugadores[(ronda + 1) % 2]

        # Elegir cartas
        cartas = obtener_cartas_distintas()
        print(f"\n ¡Hora de elegir!, {cardoelector}")
        for i, carta in enumerate(cartas):
            print(f"{i + 1}) {carta['descripcion']} ({carta['puntos']} pts)")

        try:
            eleccion = int(input("Elige una carta (1-3): ")) - 1
            if eleccion not in [0, 1, 2]:
                raise ValueError
        except ValueError:
            print("Elección inválida. Se seleccionará la primera carta.")
            eleccion = 0

        carta_elegida = cartas[eleccion]

        limpiar_consola()
        print(f"\n ¡Hora de adivinar!, {cardomante}")
        for i, carta in enumerate(cartas):
            print(f"{i + 1}) {carta['descripcion']} ({carta['puntos']} pts)")

        try:
            adivinanza = int(input("¿Cuál eligió el otro jugador? (1-3): ")) - 1
            if adivinanza not in [0, 1, 2]:
                raise ValueError
        except ValueError:
            print("Elección inválida. Se tomará la primera carta.")
            adivinanza = 0

        acertó = (adivinanza == eleccion)
        puntos = carta_elegida['puntos']
        if acertó:
            puntos_ganados = puntos - 1 if puntos > 1 else 1
            print(f"\n ¡Correcto! {cardomante} gana {puntos_ganados} puntos.")
            db.partidas.update_one(
                {"_id": id_partida},
                {"$inc": {f"puntaje.{cardomante}": puntos_ganados}}
            )
        else:
            print(f"\n Falló. {cardoelector} gana {puntos} puntos.")
            db.partidas.update_one(
                {"_id": id_partida},
                {"$inc": {f"puntaje.{cardoelector}": puntos}}
            )

        # Guardar detalle de la ronda
        detalle_ronda = {
            "ronda": ronda + 1,
            "cardoelector": cardoelector,
            "cardomante": cardomante,
            "cartas": cartas,
            "eleccion": carta_elegida,
            "adivinanza": cartas[adivinanza],
            "acierto": acertó
        }

        db.partidas.update_one(
            {"_id": id_partida},
            {"$push": {"detalle_rondas": detalle_ronda}}
        )

        input("\nPresiona Enter para continuar a la siguiente ronda...")
        limpiar_consola()
if __name__ == "__main__":
    jugador1, jugador2, rondas, id_partida = iniciar_partida()
    jugar_rondas(jugador1, jugador2, rondas, id_partida)

    # Mostrar resultados finales
    partida = db.partidas.find_one({"_id": id_partida})
    print("**Fin de la partida**")
    print("Puntajes finales:")
    for jugador, puntos in partida["puntaje"].items():
        print(f"{jugador}: {puntos} puntos")

    ganador = max(partida["puntaje"], key=partida["puntaje"].get)
    print(f"\n Ganador: **{ganador}**")

