#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#  TOKENDEACCESO : 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

import requests
import base64
import json
import os
import sys
import datetime as dt
from getpass import getpass
from colorama import init, Fore, Style

# Inicializar colorama
init(autoreset=True)

# === Configuración ===
ADMIN_USER = "root"
ADMIN_PASS = "1234"
PRIORIDADES_VALIDAS = ["Baja", "Alta", "Urgente"]
ESTADOS_VALIDOS = ["Asignado", "En Curso", "Cancelado", "Finalizado"]

# Configuración de GitHub
GITHUB_TOKEN = "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"
REPO_OWNER = "JM-GV"
REPO_NAME = "HerramientaIncidencias-Python"
BRANCH = "main"  # Cambia si usas otra rama

# === Funciones de utilidad para GitHub ===
def load_json_from_github(file_name):
    """Carga un archivo JSON desde el repositorio de GitHub."""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_name}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        content = response.json()["content"]
        decoded_content = base64.b64decode(content).decode("utf-8")
        return json.loads(decoded_content)
    elif response.status_code == 404:
        # Si el archivo no existe, devuelve una lista vacía
        return []
    else:
        print(f"Error al cargar {file_name}: {response.status_code}")
        return []

def save_json_to_github(file_name, data, commit_message):
    """Guarda un archivo JSON en el repositorio de GitHub."""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_name}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    # Verifica si el archivo ya existe para obtener su SHA
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        sha = response.json()["sha"]
    else:
        sha = None

    # Codifica el contenido en base64
    encoded_content = base64.b64encode(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")).decode("utf-8")

    # Datos para la solicitud
    payload = {
        "message": commit_message,
        "content": encoded_content,
        "branch": BRANCH
    }
    if sha:
        payload["sha"] = sha

    # Realiza la solicitud PUT
    response = requests.put(url, headers=headers, json=payload)
    if response.status_code in (200, 201):
        print(f"Archivo '{file_name}' guardado exitosamente en GitHub.")
    else:
        print(f"Error al guardar {file_name}: {response.status_code}")
        print(response.json())

# === Funciones de utilidad ===
def load_tickets():
    return load_json_from_github("incidencias.json")

def save_tickets(tickets):
    save_json_to_github("incidencias.json", tickets, "Actualizando incidencias.json")

def load_users():
    return load_json_from_github("usuarios.json")

def save_users(users):
    save_json_to_github("usuarios.json", users, "Actualizando usuarios.json")

def generar_id(tickets_existentes):
    ids = sorted([int(t["id"]) for t in tickets_existentes if t["id"].isdigit()])
    for i in range(1, 100):
        if i not in ids:
            return str(i)
    raise Exception("No hay IDs disponibles (1-99 usados)")

def solicitar(texto, obligatorio=True):
    while True:
        valor = input(texto).strip()
        if not obligatorio or valor:
            return valor
        print(Fore.RED + "Este campo es obligatorio. Inténtalo de nuevo." + Style.RESET_ALL)

# === Funcionalidad de Tickets ===
def crear_ticket(usuario_actual):
    tickets = load_tickets()
    usuarios = load_users()
    if not usuarios:
        print(Fore.RED + "⚠ No hay usuarios creados en el sistema. Debes crear uno antes de asignar tickets.\n" + Style.RESET_ALL)
        return

    print("\n=== Crear Ticket ===")
    titulo = solicitar(Fore.GREEN + "Título: " + Style.RESET_ALL)
    descripcion = solicitar(Fore.GREEN + "Descripción: " + Style.RESET_ALL)

    # Validar prioridad
    while True:
        prioridad = solicitar(Fore.GREEN + f"Prioridad ({'/'.join(PRIORIDADES_VALIDAS)}): " + Style.RESET_ALL)
        if prioridad in PRIORIDADES_VALIDAS:
            break
        print(Fore.YELLOW + f"⚠ Prioridad inválida. Debe ser una de: {', '.join(PRIORIDADES_VALIDAS)}" + Style.RESET_ALL)

    # Validar usuario asignado
    nombres_usuarios = [u["usuario"] for u in usuarios]
    while True:
        asignado_a = solicitar(Fore.GREEN + f"Asignar a usuario ({', '.join(nombres_usuarios)}): "+ Style.RESET_ALL)
        if asignado_a in nombres_usuarios:
            break
        print(Fore.YELLOW + "⚠ Usuario no existe en el sistema. Intenta de nuevo." + Style.RESET_ALL)

    ticket = {
        "id": generar_id(tickets),
        "titulo": titulo,
        "descripcion": descripcion,
        "prioridad": prioridad,
        "asignado_a": asignado_a,
        "estado": "Asignado",
        "creado_en": dt.datetime.now().isoformat(timespec="seconds"),
        "historial": []
    }

    tickets.append(ticket)
    save_tickets(tickets)

    print(Fore.GREEN + "\n✅ Ticket creado con éxito." + Style.RESET_ALL)
    print(f"   ID: {ticket['id']}")
    print(f"   Estado: {ticket['estado']}")

# === Funcionalidad de Usuarios ===
def crear_usuario():
    usuarios = load_users()

    print("\n=== Crear Usuario ===")
    nombre = solicitar("Nombre de usuario: ")

    if any(u["usuario"] == nombre for u in usuarios):
        print(Fore.YELLOW + "⚠ Ya existe un usuario con ese nombre.\n" + Style.RESET_ALL)
        return

    contrasena = getpass("Contraseña: ")
    contrasena2 = getpass("Repetir contraseña: ")

    if contrasena != contrasena2:
        print(Fore.RED + "⚠ Las contraseñas no coinciden.\n" + Style.RESET_ALL)
        return

    grupo = solicitar("Grupo de trabajo: ")

    usuario = {
        "usuario": nombre,
        "password": contrasena,
        "grupo": grupo
    }

    usuarios.append(usuario)
    save_users(usuarios)

    print(Fore.GREEN + "\n✅ Usuario creado con éxito.\n" + Style.RESET_ALL)

# === Login ===
def login():
    print("\n")
    print(" *INICIO DE SESIÓN* ")
    print("\n")
    usuario = input(Fore.BLUE + "Usuario: " + Style.RESET_ALL).strip()
    contrasena = getpass(Fore.BLUE + "Contraseña: " + Style.RESET_ALL).strip()

    if usuario == ADMIN_USER and contrasena == ADMIN_PASS:
        print(Fore.GREEN + "\nBienvenido, Administrador.\n" + Style.RESET_ALL)
        return usuario

    usuarios = load_users()
    if any(u["usuario"] == usuario and u["password"] == contrasena for u in usuarios):
        print(Fore.GREEN + f"\nBienvenido, {usuario}.\n" + Style.RESET_ALL)
        return usuario

    print(Fore.RED + "\nCredenciales incorrectas. Saliendo...\n" + Style.RESET_ALL)
    return None

# === Menú principal ===
def menu_principal(usuario_actual):
    os.system('cls' if os.name == 'nt' else 'clear')  # Limpieza de pantalla
    #print(Fore.GREEN + f"Bienvenido :)" + Style.RESET_ALL)
    while True:
        print("\n")
        print(" *** Inicio ***")
        print("\n")
        if usuario_actual == ADMIN_USER:
            # Menú para el administrador
            print("1 📝  Crear Ticket")
            print("2 🗑   Borrar Ticket")
            print("3 👤  Crear Usuario")
            print("4 ❌  Borrar Usuario")
            print("5 📋  Mis Incidencias")
            print("6 🚪  Salir")
            print("\n")
            opcion = solicitar("Elige una opción (1-6): ")
        else:
            # Menú para usuarios normales
            print("1 📝  Crear Ticket")
            print("2 📋  Mis Incidencias")
            print("3 🚪  Salir")
            print("\n")
            opcion = solicitar("Elige una opción (1-3): ")

        os.system('cls' if os.name == 'nt' else 'clear')  # Limpieza de pantalla después de elegir una opción

        if opcion == "1":
            crear_ticket(usuario_actual)
        elif usuario_actual == ADMIN_USER and opcion == "2":
            borrar_ticket(usuario_actual)
        elif usuario_actual == ADMIN_USER and opcion == "3":
            crear_usuario()
        elif usuario_actual == ADMIN_USER and opcion == "4":
            borrar_usuario()
        elif (usuario_actual == ADMIN_USER and opcion == "5") or (usuario_actual != ADMIN_USER and opcion == "2"):
            gestionar_mis_tickets(usuario_actual)
        elif (usuario_actual == ADMIN_USER and opcion == "6") or (usuario_actual != ADMIN_USER and opcion == "3"):
            print("¡Hasta luego!")
            break
        else:
            print("Opción no válida. Inténtalo de nuevo.\n")

def borrar_usuario():
    usuarios = load_users()
    if not usuarios:
        print(Fore.YELLOW + "\nNo hay usuarios registrados aún.\n" + Style.RESET_ALL)
        return

    print("\n=== Borrar Usuario ===")
    nombre = solicitar("Introduce el nombre de usuario a borrar: ")

    # Buscar el índice del usuario en la lista
    idx = next((i for i, u in enumerate(usuarios) if u["usuario"] == nombre), None)
    if idx is None:
        print(Fore.RED + "⚠ No se encontró ningún usuario con ese nombre.\n" + Style.RESET_ALL)
        return

    # Mostrar los datos del usuario encontrado
    u = usuarios[idx]
    print("\nSe encontró el siguiente usuario:")
    print(json.dumps(u, ensure_ascii=False, indent=2))

    # Confirmar eliminación
    confirm = solicitar("\n¿Seguro que deseas eliminarlo? (s/n): ").lower()
    if confirm in ("s", "si", "sí"):
        usuarios.pop(idx)  # Eliminar el usuario de la lista
        save_users(usuarios)  # Guardar los cambios en GitHub
        print(Fore.GREEN + "🗑  Usuario eliminado correctamente.\n" + Style.RESET_ALL)
    else:
        print("Operación cancelada. El usuario no fue eliminado.\n")

def borrar_ticket(usuario_actual):
    tickets = load_tickets()
    if not tickets:
        print(Fore.YELLOW + "\nNo hay tickets registrados aún.\n" + Style.RESET_ALL)
        return

    print("\n=== Borrar Ticket ===")
    id_borrar = solicitar("Introduce el ID del ticket a borrar (0 para volver al Inicio): ")

    # Buscar el índice del ticket en la lista
    idx = next((i for i, t in enumerate(tickets) if t["id"] == id_borrar), None)
    if idx is None:
        print(Fore.RED + "⚠ No se encontró ningún ticket con ese ID.\n" + Style.RESET_ALL)
        return

    # Mostrar los datos del ticket encontrado
    t = tickets[idx]
    print("\nSe encontró el siguiente ticket:")
    print(json.dumps(t, ensure_ascii=False, indent=2))

    # Confirmar eliminación
    confirm = solicitar("\n¿Seguro que deseas eliminarlo? (s/n): ").lower()
    if confirm in ("s", "si", "sí"):
        tickets.pop(idx)  # Eliminar el ticket de la lista
        save_tickets(tickets)  # Guardar los cambios en GitHub
        print(Fore.GREEN + "🗑  Ticket eliminado correctamente.\n" + Style.RESET_ALL)
    else:
        print("Operación cancelada. El ticket no fue eliminado.\n")

def gestionar_mis_tickets(usuario_actual):
    tickets = load_tickets()

    print("\n=== Mis Incidencias ===")
    # Filtrar tickets asignados al usuario actual
    mis_tickets = [t for t in tickets if t["asignado_a"] == usuario_actual]
    if not mis_tickets:
        print(Fore.YELLOW + "\nNo tienes incidencias asignadas.\n" + Style.RESET_ALL)
        return

    # Mostrar información básica de cada ticket asignado
    print("\nTus incidencias:")
    for t in mis_tickets:
        print("--------------------------")
        print(Fore.BLUE + f"ID: {t['id']}" + Style.RESET_ALL)
        print(f"Título: {t['titulo']}")
        print(f"Descripción: {t['descripcion']}")
        print(f"Estado: {colorear_estado(t['estado'])}")
    print("--------------------------")

    # Solicitar al usuario que introduzca el ID de la incidencia a editar
    id_ticket = solicitar("\nIntroduce el ID de la Incidencia que quieres editar (pulsa 0 para volver al menú): ")
    if id_ticket == "0":
        return

    # Buscar el ticket por ID
    ticket = next((t for t in mis_tickets if t["id"] == id_ticket), None)
    if not ticket:
        print(Fore.RED + "⚠ No se encontró una incidencia con ese ID asignada a ti.\n" + Style.RESET_ALL)
        return

    # Mostrar el estado actual de la incidencia
    print(f"\nEstado actual de la incidencia: {colorear_estado(ticket['estado'])}")

    # Solicitar el nuevo estado
    print("\nEstados posibles:")
    for e in ESTADOS_VALIDOS:
        print(f"- {e}")

    while True:
        nuevo_estado = solicitar("Introduce el nuevo estado: ")
        if nuevo_estado in ESTADOS_VALIDOS:
            break
        print(Fore.YELLOW + f"⚠ Estado inválido. Debe ser uno de: {', '.join(ESTADOS_VALIDOS)}" + Style.RESET_ALL)

    # Solicitar un comentario
    comentario = solicitar("Introduce un comentario: ")

    # Actualizar el estado y añadir el comentario al historial
    ticket["estado"] = nuevo_estado
    ticket.setdefault("historial", []).append({
        "fecha": dt.datetime.now().isoformat(timespec="seconds"),
        "estado": nuevo_estado,
        "comentario": comentario,
        "usuario": usuario_actual
    })

    # Guardar los cambios en el archivo
    save_tickets(tickets)
    print(Fore.GREEN + "\n✅ Cambios guardados correctamente. Volviendo al menú principal...\n" + Style.RESET_ALL)

    
def colorear_estado(estado):
    """
    Devuelve el estado con un color específico dependiendo de su valor.
    """
    if estado == "Asignado":
        return Fore.YELLOW + estado + Style.RESET_ALL
    elif estado == "En Curso":
        return Fore.BLUE + estado + Style.RESET_ALL
    elif estado == "Cancelado":
        return Fore.RED + estado + Style.RESET_ALL
    elif estado == "Finalizado":
        return Fore.GREEN + estado + Style.RESET_ALL
    return estado  # Por si hay un estado no reconocido


def main():
    usuario_actual = login()
    if not usuario_actual:
        sys.exit(1)
    menu_principal(usuario_actual)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupción por teclado. Saliendo...")
        sys.exit(0)
