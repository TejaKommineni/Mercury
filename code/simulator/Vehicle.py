class Vehicle:    
    
    def set_location(self,x,y):
        self.x_location=x
        self.y_location=y
      
    def set_speed(self,speed):   
        self.speed=speed 
        
    def set_last_reported_time(self,time):   
        self.last_reported_time=time     
    
    def __init__(self,vehicle_id,x,y,speed,time):
        self.vehicle_id=vehicle_id
        self.x_location=x
        self.y_location=y
        self.speed=speed
        self.last_reported_time=time
        
    
    