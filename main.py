# coding: utf-8

import argparse
import serial
import time
import signal
import threading
import hashlib
import string

from io import StringIO


COLOR_RED = "\033[31m"
COLOR_GRE = "\033[32m"
COLOR_END = "\033[0m"
port = 'COM4' # 시리얼 포트
baud = 921600 # 시리얼 보드레이트(통신속도)


rcv_size = 0
rcv_datas = b''

rthread = object
readThreadRun = True
isRun = True
isMain = True

# 파일을 읽어서 메모리에 저장하는 코드
def read_file_to_memory(file_path):
    try:
        with open(file_path) as file:
            data = file.read()
        return data  # 메모리에 저장된 파일 내용 반환
    except Exception as e:
        print(f"파일을 읽는 중 오류 발생: {e}")
        return None

def get_hash(data, algorithm="md5"):
    hash_func = hashlib.new(algorithm)
    hash_func.update(data)  # 해시 계산
    return hash_func.hexdigest()


#쓰레드 종료용 시그널 함수
def handler(signum, frame):
    global readThreadRun
    global isRun
    global isMain
    
    print("-----ctrl-c------")

    isMain = False
    isRun = False
    readThreadRun = False



def readThread(ser):
    global rcv_datas
    global rcv_size
    global rcv_datas
    global readThreadRun

    # 쓰레드 종료될때까지 계속 돌림
    while isRun:
        while readThreadRun:
            buf = ser.readline()
            if len(buf) > 0 :
                #데이터가 있있다면
                rcv_datas = rcv_datas + buf
                rcv_size = rcv_size + len(buf)


def fileWrite(datas):
    filename = "./received-"+port+".txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(datas.decode('utf-8'))
    f.close()
    print("write error data")

def LogWrite(datas):
    filename = "./"+port+".log"
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(datas+"\n")
    f.close()



def dbg(*msg):
    io = StringIO()
    print(*msg, file=io, end="")
    return io.getvalue()


def mainloop():
    global rthread
    global rcv_datas
    global rcv_size
    global readThreadRun
    global isMain

    test_count = 0
    fail_count = 0
    pass_count = 0
    
    #시리얼 열기
    wow = dbg(f"port={port}, baud={baud}")
    print(wow)
    LogWrite(wow)
    ser = serial.Serial(port, baud, timeout=0)

    # 전송 파일 열기
    file_content = read_file_to_memory("reboot.log")
    fil_size = len(file_content)
    fil_hash = get_hash(file_content.encode('utf-8'))

    tt = time.strftime('%Y.%m.%d-%H:%M:%S')
    wow = dbg(f"[{tt}]                file:sz={fil_size} [{fil_hash}]")
    print(wow)
    LogWrite(wow)

    rthread = threading.Thread(target=readThread, args=(ser,))
    rthread.start()

    while isMain:
        test_count = test_count + 1
        

        readThreadRun = True

        t1 = time.time()
        ts = time.strftime('%Y.%m.%d-%H:%M:%S')

        # 파일 전송
        # with open('./reboot.log', 'r') as in_file:
        #     for line in in_file.read():
        #         ser.write(line.encode('utf-8'))
        ser.write(file_content.encode('utf-8'))

        t2 = time.time()
        te = time.strftime('%Y.%m.%d-%H:%M:%S')

        time.sleep(1)
        # 쓰레드 정지
        readThreadRun = False

 
        if not isMain:
            break

        rcv_hash = get_hash(rcv_datas)
        if rcv_hash == fil_hash:
            pass_count = pass_count + 1
            wow = dbg(f"[{te}] [{pass_count:3d}/{test_count:3d}] {port} pass:sz={rcv_size} [{rcv_hash}] {(rcv_size*8)/(t2-t1):.0f} bps")
        else:
            fail_count = fail_count + 1
            wow = dbg(f"[{te}] [{fail_count:3d}/{test_count:3d}] {port} {COLOR_RED}fail{COLOR_END}:sz={rcv_size} [{rcv_hash}]")
            fileWrite(rcv_datas)

        print(wow)
        LogWrite(wow)

        rcv_datas = b''
        rcv_size = 0

    # quit sequence




def set_config():
    parser = argparse.ArgumentParser(
        prog="repeater2test full-duplex",
        description="testing program for uart2ethernet",
    )

    parser.add_argument("--arg1", "-p", "--port", type=str, help="uart port name [COMx,]", default="COM4")
    parser.add_argument("--arg2", "-b", "--baudrate", type=int, help="baudrate [9600,...,921600]", default=921600)

    return parser






if __name__ == "__main__":
    parser = set_config()
    args = parser.parse_args()

    port = args.arg1
    baud = args.arg2

    #종료 시그널 등록
    signal.signal(signal.SIGINT, handler)
    

    mainloop()
        
