q=[]

class delCallbackObj():
    def __init__(self,index,callback,*args):
        self.index=index
        self.callback=callback
        self.active=True
        self.args=args
    def dont(self):
        self.active=False
        
    def delete(self):
        if(self.active):
            self.callback(*self.args)
            

def dispose(index,callback,*args):
    #TODO sort the q by index and implement the 
    disposeRef=delCallbackObj(index,callback,*args)
    q.append(disposeRef)
    return disposeRef

def periodicCheck(index):
    while(q and q[0].index<index):
        delObj=q.pop(0)
        if(delObj.callback):
            delObj.callback(*delObj.args)            
        
    
    