import RPi.GPIO as GPIO
class encoder():
                
    def __init__(self,count,mul,pin1,pin2):
        self.counter=count
        self.multiply=mul
        self.gpio1=pin1
        self.gpio2=pin2
        GPIO.setup(self.gpio1,GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.gpio2,GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.gpio1, GPIO.BOTH, self.handler1)
        GPIO.add_event_detect(self.gpio2, GPIO.BOTH, self.handler2)
    
    
    def value(self):
        return (self.counter)*(self.multiply)/1000 #przelcizenie z mikrometrow na milimetry

    
    def clear(self):
        counter=0
        return self.counter

    def handler1(self,channel):
        if GPIO.input(self.gpio1):
            if GPIO.input(self.gpio2):
                self.counter=self.counter+1
            else:
                self.counter=self.counter-1
        else:
            if GPIO.input(self.gpio2):
                self.counter=self.counter-1
            else:
                self.counter=self.counter+1

    def handler2(self,channel):
        if GPIO.input(self.gpio2):
            if GPIO.input(self.gpio1):
                self.counter=self.counter-1
            else:
                self.counter=self.counter+1
        else:
            if GPIO.input(self.gpio1):
                self.counter=self.counter+1
            else:
                self.counter=self.counter-1

    

        

            
    
    
