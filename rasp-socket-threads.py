import socket
import time
from threading import Thread
from random import randint

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.bind(('', 8089))
serversocket.listen(5)

lista_mensagens = []
cooler_status = 0

desktop_ip_found = 0
desktop_ip_addr = ''

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
                
    #Thread 1 - Ler dados de temperatura do sensor
    temperatureThread = Thread(target=readTemperature)
    temperatureThread.start()

    #Thread 2 - Envio dos dados para o servidor
    sendDataThread = Thread(target=sendData)
    sendDataThread.start()

    #Thread 3 - Verificar novas mensagens do servidor
    socketThread = Thread(target=connectFunc)
    socketThread.start()

    #Thread 4 - Ativar e Desativar o cooler de resfriamento
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
    while True:
        temperatura = randint(25,33)
        lista_mensagens.append(temperatura)
        global cooler_status
        if temperatura > 30:
            cooler_status = 1
            print('Ativando cooler')
        else:
            cooler_status = 0
            print('Desativando cooler')
        time.sleep(5)
        
def sendData():
    while True:
        time.sleep(4)
        if len(lista_mensagens) > 0:
            respond(str(lista_mensagens.pop()))
            
def coolerHandler():
    while True:
        time.sleep(4)
        print('Cooler handler: status = ' + str(cooler_status))
        if cooler_status == 1:
            print('Ativando cooler')
        else:
            print('Desativando cooler')
            
#Thread 0 - Encontrar servidor na rede
serverFindThread = Thread(target=findServer)
serverFindThread.start()