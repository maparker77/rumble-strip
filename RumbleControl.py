import pyfirmata
import socket
from shapely.geometry import Point, Polygon
import struct
import time
import pygame

polygons = [Polygon([(7.6, 0.5), (190, 0.5), (190, -0.5), (7.6, -0.5)])]
leftPin = 0
rightPin = 0
leftRumble = None
rightRumble = None
bothRumble = None

# set up the audio files so they can be run quickly later
def setup_sound():
    global leftRumble
    global rightRumble
    global bothRumble
    pygame.mixer.init()
    leftRumble = pygame.mixer.Sound("Rumble_Left.wav")
    rightRumble = pygame.mixer.Sound("Rumble_Right.wav")
    bothRumble = pygame.mixer.Sound("Rumble_Both.wav")

# connect to the aruino and establish pins
def setup_arduino():
    port = "COM7"
    board = pyfirmata.Arduino(port)
    it = pyfirmata.util.Iterator(board)
    it.start()
    time.sleep(1)
    board.digital[9].mode = pyfirmata.OUTPUT
    board.digital[10].mode = pyfirmata.OUTPUT
    time.sleep(1)
    print("Aruino Connected")
    return board

# disconnect from the arduino
def exit_arduino(board):
    board.exit

# write value to given pin on the arduino
def write_pin(board, pin, value):
    global leftPin
    global rightPin
    if pin == 9 and leftPin != value:
        leftPin = value
        board.digital[pin].write(value)
    elif pin == 10 and rightPin != value:
        rightPin = value
        board.digital[pin].write(value)

# establish udp connection
def udp_connect():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 7000))
    sock.settimeout(1.0)
    print("Listening to Port")
    return sock

# read data from udp port
def read_socket(sock):
    while True:
        try:
            data, addr = sock.recvfrom(48)
            return struct.unpack('12f', data)
        except Exception:
            pass

# activate rumble strips when in position
def actionMapper(xPosFL, yPosFL, xPosFR, yPosFR, xPosRL, yPosRL, xPosRR, yPosRR, board):
    FR = Point((xPosFR, yPosFR))
    FL = Point((xPosFL, yPosFL))
    RR = Point((xPosRR, yPosRR))
    RL = Point((xPosRL, yPosRL))

    activateLeft = False
    activateRight = False
    for polygon in polygons:
        if polygon.contains(FR) or polygon.contains(RR):
            activateRight = True
        if polygon.contains(FL) or polygon.contains(RL):
            activateLeft = True

    if activateRight and not(activateLeft):
        write_pin(board, 10, 1)
        write_pin(board, 9, 0)
        rightRumble.play()
    elif activateLeft and not(activateRight):
        write_pin(board, 9, 1)
        write_pin(board, 10, 0)
        leftRumble.play()
    elif activateRight and activateLeft:
        write_pin(board, 9, 1)
        write_pin(board, 10, 1)
        bothRumble.play()
    else:
        write_pin(board, 9, 0)
        write_pin(board, 10, 0) 

if __name__ == "__main__":
    setup_sound()
    board = setup_arduino()
    sock = udp_connect()

    while True:
        data = read_socket(sock)
        actionMapper(data[0], data[1], data[3], data[4], data[6], data[7], data[9], data[10], board)

    exit_arduino(board)