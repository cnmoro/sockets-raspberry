import socket
import time
from threading import Thread
from random import randint
import threading
import Adafruit_DHT
import RPi.GPIO as GPIO

# Socket (parte servidor)
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.bind(('', 8089))
serversocket.listen(5)

# Temperatura e cooler
temperaturaAtual = -999
coolerStatus = 0

# Variáveis de controle para IP do desktop
desktopIpFound = 0
desktopIpAddr = ''

# Semaforo
semaforo = threading.Semaphore()

# Configuração do GPIO
GPIO.setmode(GPIO.BOARD)

# Sensor de temperatura - Pino 22 - GPIO25 (Schematic)
pinoSensor = 25
sensor = Adafruit_DHT.DHT11

# Cooler - Pino 18 - GPIO24 (Schematic)
pinoCooler = 18
GPIO.setup(pinoCooler, GPIO.OUT)
GPIO.setwarnings(False)

# Flag para indicar estabilidade da conexão
estaConectado = 0

# Gerencia (reseta) flag de conexão
def connFlagManager():
    global estaConectado
    while True:
        time.sleep(60)
        estaConectado = 0

# Encontrar desktop em rede DHCP
def findServer():
    global desktopIpFound
    global desktopIpAddr
    while desktopIpFound == 0:
        print('Aguardando servidor na rede\n')
        connection, address = serversocket.accept()
        buf = connection.recv(4096)
        ipstr = str(address)
        indexVirg = ipstr.find(",")
        ipstr = ipstr[:indexVirg]
        ipstr = ipstr.replace("(", "").replace("'", "")

        if len(buf) > 0:
            if buf == b'rasp?':
                print('Servidor encontrado em ' + str(ipstr) + '\n')
                desktopIpFound = 1
                desktopIpAddr = ipstr
                respond('rasp!')

    # Thread 1 - Ler dados de temperatura do sensor
    temperatureThread = Thread(target=readTemperature)
    temperatureThread.start()

    # Thread 2 - Envio dos dados para o servidor
    sendDataThread = Thread(target=sendData)
    sendDataThread.start()

    # Thread 3 - Verificar novas mensagens do servidor
    socketThread = Thread(target=checkServerMsgs)
    socketThread.start()

    # Thread 4 - Ativar e Desativar o cooler de resfriamento
    coolerThread = Thread(target=coolerHandler)
    coolerThread.start()


# Enviar mensagem ao servidor
def respond(msg):
    global desktopIpAddr
    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientsocket.connect((desktopIpAddr, 8089))
    print('Enviando: ' + str(msg) + '\n')
    clientsocket.send(bytes(msg, 'UTF-8'))
    clientsocket.close()

# Verifica mensagens do servidor
def checkServerMsgs():
    global coolerStatus
    global estaConectado
    while True:
        connection, address = serversocket.accept()
        buf = connection.recv(4096)
        print('ip: ' + str(address))
        if len(buf) > 0:
            estaConectado = 1
            print('Recebido: ' + str(buf) + '\n')
            respond('Mensagem Recebida pelo Rasp com Sucesso!')
            if buf == b'acionarCooler':
                coolerStatus = 1
            elif buf == b'desligarCooler':
                coolerStatus = 0

# Lê a temperatura do sensor
def readTemperature():
    global semaforo
    global temperaturaAtual
    global sensor
    global pinoSensor
    while True:
        umid, temp = Adafruit_DHT.read_retry(sensor, pinoSensor)
        print('readTemperature Deseja adquirir o semáforo\n')
        semaforo.acquire()
        print('readTemperature Adquiriu o semáforo\n')
        if temp is not None:
            temperaturaAtual = temp
            print('Sensor leu: ' + str(temp) + '\n')
        else:
            temperaturaAtual = -999
        semaforo.release()
        print('readTemperature Liberou o semáforo\n')
        time.sleep(10)

# Envia a temperatura lida para o servidor
def sendData():
    global temperaturaAtual
    global semaforo
    while True:
        time.sleep(10)
        if temperaturaAtual != -999:
            print('sendData Deseja adquirir o semáforo\n')
            semaforo.acquire()
            print('sendData Adquiriu o semáforo\n')
            respond(str(temperaturaAtual))
            temperaturaAtual = -999
            semaforo.release()
            print('sendData Liberou o semáforo\n')

# Gerencia o acionamento do cooler
def coolerHandler():
    global pinoCooler
    global estaConectado
    global coolerStatus
    while True:
        time.sleep(10)
        print('Cooler handler: status = ' + str(coolerStatus) + '\n')
        #Testa para verificar se o servidor está há muito tempo sem responder
        if estaConectado == 0:
            if temperaturaAtual >= 33:
                coolerStatus = 1
                print('Ativando cooler via embarcado\n')
                GPIO.output(pinoCooler, True)
            else:
                coolerStatus = 0
                print('Desativando cooler via embarcado\n')
                GPIO.output(pinoCooler, False)
        else:
            if coolerStatus == 1:
                print('Ativando cooler via instrução do servidor\n')
                GPIO.output(pinoCooler, True)
            else:
                print('Desativando cooler via instrução do servidor\n')
                GPIO.output(pinoCooler, False)


# Thread 0.1 - Gerenciador de flag de conexão
connFlagThread = Thread(target=connFlagManager)
connFlagThread.start()

# Thread 0.2 - Encontrar servidor na rede
serverFindThread = Thread(target=findServer)
serverFindThread.start()
