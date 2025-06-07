from typing import AnyStr
from datetime import datetime as dt
from Colors import Colors

class EdcLogger:
    
    hass = 'undefined'
    
    def __init__(self, hass = 'undefined'):
        print(f"hass: {hass}")
        self.hass = hass
        
    def logAndPrint(self, message: AnyStr, color: Colors = Colors.RESET, timestamp = True):
        self.print(message, color, timestamp)
        
        if  (self.hass != 'undefined'):
            self.hass.log(message)
        
        
    def print(self, message: AnyStr, color: Colors = Colors.RESET, timestamp = True):
        timeString = ""
        if (timestamp == True):
            timeString = dt.now().strftime('%Y-%m-%d %H:%M:%S') + ": " 
        print(f"{timeString} {color}{message}{Colors.RESET}")