import socket
import time
from threading import Thread
from random import randint
import threading

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.bind(('', 8089))
serversocket.listen(5)

temperatura_atual = -999
cooler_status = 0

desktop_ip_found = 0
desktop_ip_addr = ''

semaforo = threading.Semaphore()

def findServer():
    global desktop_ip_found
    global desktop_ip_addr
    while desktop_ip_found == 0:
        print('Aguardando servidor na rede')
        connection, address = serversocket.accept()
        buf = connection.recv(4096)
        ipstr = str(address)
        indexVirg = ipstr.find(",")
        ipstr = ipstr[:indexVirg]
        ipstr = ipstr.replace("(", "").replace("'", "")

        if len(buf) > 0:
            if buf == b'rasp?':
                print('Servidor encontrado em ' + str(ipstr))
                desktop_ip_found = 1
                desktop_ip_addr = ipstr
                respond('rasp!')

    # Thread 1 - Ler dados de temperatura do sensor
    temperatureThread = Thread(target=readTemperature)
    temperatureThread.start()

    # Thread 2 - Envio dos dados para o servidor
    sendDataThread = Thread(target=sendData)
    sendDataThread.start()

    # Thread 3 - Verificar novas mensagens do servidor
    socketThread = Thread(target=connectFunc)
    socketThread.start()

    # Thread 4 - Ativar e Desativar o cooler de resfriamento
    coolerThread = Thread(target=coolerHandler)
    coolerThread.start()


def respond(msg):
    global desktop_ip_addr
    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientsocket.connect((desktop_ip_addr, 8089))
    print('Enviando: ' + str(msg) + '\n')
    clientsocket.send(bytes(msg, 'UTF-8'))
    clientsocket.close()


def connectFunc():
    while True:
        connection, address = serversocket.accept()
        buf = connection.recv(4096)
        print('ip: ' + str(address))
        if len(buf) > 0:
            print('Recebido: ' + str(buf) + '\n')
            respond('Mensagem Recebida pelo Rasp com Sucesso!')


def readTemperature():
    global semaforo
    global cooler_status
    global temperatura_atual
    while True:
        print('readTemperature Deseja adquirir o semáforo')
        semaforo.acquire()
        print('readTemperature Adquiriu o semáforo')
        temperatura_atual = randint(25, 42)
        semaforo.release()
        print('readTemperature Liberou o semáforo')
        if temperatura_atual > 30:
            cooler_status = 1
            print('Ativando cooler')
        else:
            cooler_status = 0
            print('Desativando cooler')
        time.sleep(5)


def sendData():
    global temperatura_atual
    global semaforo
    while True:
        time.sleep(4)
        if temperatura_atual != -999:
            print('sendData Deseja adquirir o semáforo')
            semaforo.acquire()
            print('sendData Adquiriu o semáforo')
            respond(str(temperatura_atual))
            temperatura_atual = -999
            semaforo.release()
            print('sendData Liberou o semáforo')


def coolerHandler():
    while True:
        time.sleep(4)
        print('Cooler handler: status = ' + str(cooler_status))
        if cooler_status == 1:
            print('Ativando cooler')
        else:
            print('Desativando cooler')


# Thread 0 - Encontrar servidor na rede
serverFindThread = Thread(target=findServer)
serverFindThread.start()
