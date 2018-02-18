import threading, time
import sys, os
import simu_util as myUtil
import data_sender as dataSend
import motor

show_all_info = True
show_control = False

def showUsage():
    print 'press 1 to open engine'
    print 'press 0 to close engine'
    print 'press w to turn on/off info'
    print 'press q to terminate program'
    print 'press s to press start button'

def controlMotor(bike):
    global show_all_info, show_control
    while True:
        input_char = myUtil.getch()
        if input_char == '1' and not bike.getEngineOpen():
            print 'open engine'
            bike.openEngine()
        elif input_char == '0' and bike.getEngineOpen():
            print 'close engine'
            bike.closeEngine()
        elif input_char == 'w':
            if show_control:
                show_control = False
                myUtil.clearConsole()
                showUsage()
            else:
                show_control = True
        elif input_char == 'q':
            show_all_info = False
            break
        elif input_char == 's':
            bike.pressStartButton()
        elif input_char == 'o':
            bike.openThrottle(0.5)
        elif input_char == 'l':
            bike.openThrottle(-0.5)
        elif input_char == '9':
            bike.openThrottle(10)
        elif input_char == '.':
            bike.openThrottle(-10)
        elif input_char == 'c':
            bike.pullClutch()
        elif input_char == 'i':
            bike.gearControl(1)
        elif input_char == 'k':
            bike.gearControl(-1)
        elif input_char == 'e':
            bike.controlISCVP(2)
        elif input_char == 'd':
            bike.controlISCVP(-2)
        elif input_char == 'u':
            bike.modeSelection(1)
        elif input_char == 'j':
            bike.modeSelection(2)

def simulateMotor(bike):
    global show_all_info
    while show_all_info:
        bike.recompute_attr()
        if show_control:
            print bike
        #time.sleep(0.1)
        if show_control:
            myUtil.clearConsole()

def main():
    showUsage()
    bike = motor.Motor()

    control_motor_thread = threading.Thread(target=controlMotor, args=(bike,), name='controlThread')
    show_info_thread = threading.Thread(target=simulateMotor, args=(bike,), name='showThread')
    data_send_thread = threading.Thread(target=dataSend.sending_data, args=(bike,), name='dataSendingThread')
    control_motor_thread.start()
    show_info_thread.start()
    data_send_thread.start()
    time.sleep(1)
    data_send_thread.join()
    control_motor_thread.join()
    show_info_thread.join()

if __name__ == '__main__':
    main()
    