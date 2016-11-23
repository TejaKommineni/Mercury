from Vehicle import Vehicle
import threading
import math
import time

class Mercury_Simulator:  
 
 def report_scheduler(self): 
     for id,vehicle in self.vehicles.items():
         last_report_time = self.vehicles[id].last_reported_time
         speed=self.vehicles[id].speed
         present_time=time.time()
         difference=present_time-last_report_time
         if(difference >8):
            if speed == 0:
               self.vehicles[id].x_location=(self.vehicles[id].x_location+1)%self.x_max
               self.vehicles[id].y_location=(self.vehicles[id].y_location)%self.y_max     
            if speed == 1:
               self.vehicles[id].x_location=(self.vehicles[id].x_location+1)%self.x_max
               self.vehicles[id].y_location=(self.vehicles[id].y_location+1)%self.y_max   
            if speed == 2:
               self.vehicles[id].x_location=(self.vehicles[id].x_location+2)%self.x_max
               self.vehicles[id].y_location=(self.vehicles[id].y_location+1)%self.y_max 
            if speed == 3:
               self.vehicles[id].x_location=(self.vehicles[id].x_location+2)%self.x_max
               self.vehicles[id].y_location=(self.vehicles[id].y_location+2)%self.y_max
           # print('Report published for vehicle id', id)       
            self.vehicles[id].last_reported_time=time.time()  
     threading.Timer(5,self.report_scheduler).start()                               
 
 def add_vehicles(self,count_vehicles):
    num_vehicles=len(self.vehicles)
    start=int(math.sqrt(num_vehicles)+1)  
    end=int(math.sqrt(count_vehicles)+1)+start
    x_last=start
    y_last=1
    max_y=1    
    while(x_last<=end and count_vehicles>0):
       while(y_last<=end and count_vehicles>0):
         self.vehicles[num_vehicles+count_vehicles]= Vehicle(num_vehicles+count_vehicles,x_last,y_last,((num_vehicles+count_vehicles)%4),time.time()) 
         count_vehicles-=1
         y_last+=1
       x_last+=1
       y_last=1
    self.x_max=end
    self.y_max=end 
    
 def event_location(self):
     print('Would you like to look at the vehicle distribution before issuing the event')
     print('1:Yes')
     print('2:No')
     choice=input('Please Choose any option:')  
     if choice=='1':
           boundary=self.x_max
           reminder=boundary%5
           start=(boundary-reminder)/5           
           clusters={}
           clusters[start]=0
           clusters[start*2]=0
           clusters[start*3]=0
           clusters[start*4]=0
           clusters[boundary]=0
           for id,vehicle in self.vehicles.items():
               for center,count in clusters.items():
                   if self.vehicles[id].x_location<=center and self.vehicles[id].y_location<=center:
                       clusters[center]=count+1
           
           print("The vehicles in the system are grouped into 5 clusters.")
           print('{:15}'.format('Cluster_Center'), '{:15}'.format('Cluster_Radius'), '{:15}'.format('Vehicle_Count'))
           for center,count in clusters.items():
               print('{:13}'.format('('+ str(center/2)+','+str(center/2)+')'), '{:13}'.format(center/2), '{:13}'.format(count))
           while True:
               print('You can custom query me to know the number of vehicles in a given region') 
               print('1:Yes')
               print('2:No')
               choice=input('Please Choose any option:')  
               if choice=='1':
                   x=int(input('Enter the x coordinates of the querying region'))
                   y=int(input('Enter the y coordinates of the querying region'))
                   radius=int(input('Enter the querying radius with center being above x,y coordinates'))
                   count=0
                   for id,vehicle in self.vehicles.items():
                        x_v=self.vehicles[id].x_location
                        y_v=self.vehicles[id].y_location
                        if(math.sqrt(math.pow((x_v-x), 2)+math.pow((y_v-y), 2))<=radius):
                          count+=1  
                   print('The count of vehicles in the queried region is', count)       
                   
               
               if choice=='2':  
                   x=int(input('Enter the x coordinates where you want to issue the event'))
                   y=int(input('Enter the y coordinates where you want to issue the event'))
                   radius=int(input('Enter the impact radius with center being above x,y coordinates'))
                   return x,y,radius 
              
           
            
     if choice=='2':  
       x=int(input('Enter the x coordinates where you want to issue the event'))
       y=int(input('Enter the y coordinates where you want to issue the event'))
       radius=int(input('Enter the impact radius with center being above x,y coordinates'))
       return x,y,radius 
 
       
 def generate_events(self):
     print('Which of the following event type would you like to simulate')
     print('1: Emergency')
     print('2: Collision')
     print('3: Moving_Objects')
     print('4: Lane_Change_Assistance')
     print('5: Obstacle')
     print('6: Congestion')
     print('7: Blocked')
     option=input('Please Choose any option:')
     if option == '2':
        x,y,r = self.event_location() 
        self.simulate_events(2,x,y,r)
              
        
     
     
 def simulate_events(self,type,x,y,r):      
     if type==2:
        count=0 
        for id,vehicle in self.vehicles.items():
            x_v=self.vehicles[id].x_location
            y_v=self.vehicles[id].y_location
            if(math.sqrt(math.pow((x_v-x), 2)+math.pow((y_v-y), 2))<=r):
               count+=1 
               print("I have seen a collision and my id is", id, x_v, y_v)   
        print("Total number of vehicles impacted is", count)   
 
 def show_options(self):   
    while True: 
        print('Hi! This is Mercury Simulator')
        print('I can perform the following two actions')
        print('1: Add Vehicles To The System')
        print('2: Simulate An Event')
        option=input('Please Choose any option:')
        if option == '1':
           print('Total number of vehicles in the system are :', len(self.vehicles))
           count_vehicles=input('Input the number of vehicles you would like to add to this system')
           self.add_vehicles(int(count_vehicles))
        elif option == '2':
           self.generate_events()
        else:
           print('Your input didnt match the given options. Kindly, select one of the given options')


 def __init__(self):
     self.vehicles={}
     self.x_max=1
     self.y_max=1
     threading.Timer(5,self.report_scheduler).start()
     self.show_options()  
        
        
simulator = Mercury_Simulator()             