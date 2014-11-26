import os.path
import re
import string
import time
import random
import tornado.auth
import smtplib
import torndb
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import unicodedata
from tornado.options import define, options
import yajl as json

import config
import periodicDeleteQueue
from tornado.ioloop import PeriodicCallback

define("port", default=8585, help="run on the given port", type=int)
define("mysql_host", default="127.0.0.1:3306", help="database host")
define("mysql_database", default="tic_tac_db", help="database name")
define("mysql_user", default="root", help="database user")
define("mysql_password", default=config.dbPassword, help="database password")



sessions={}
user_pool=[]

userCount=[0,0]
def addUserCount(x,poolType):
    if(poolType>=len(userCount)):
        return -1
    
    userCount[poolType]+=x        
    return userCount[poolType]
    
def increaseUserScore(db,uid):
    score=db.get("select * from user_score where uid=%s",uid).score
    db.execute("update user_score set score=%s where uid=%s",score+10,uid)

game_pool={"all":[]}

class _application(tornado.web.Application):
    def __init__(self):
        settings = dict(
            static_path=os.path.join(os.path.dirname(__file__), "html/"),
            cookie_secret="11oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
            login_url="/auth/login",
            autoescape=None,
        )
        static_path = dict(path=settings['static_path'], default_filename='index.html')
           
        handlers = [
            (r"/($)", tornado.web.StaticFileHandler,static_path),
            (r"/game", game),                                        
            (r"/create_fb_game", create_fb_game),                                             
            (r"/Login", fb_login if config.isServer else Login),            
            (r"/init_game", init_game),
            (r"/update_game/(.*)", update_state),
            (r"/html/(.*)", tornado.web.StaticFileHandler,static_path)
        ]
        tornado.web.Application.__init__(self, handlers, **settings)
        tornado.ioloop.PeriodicCallback(self.disposeConnections ,1000)
        # Have one global connection to the blog DB across all handlers
        self.db = torndb.Connection(
            host=options.mysql_host, database=options.mysql_database,
            user=options.mysql_user, password=options.mysql_password)
    def disposeConnections(self):
        periodicDeleteQueue.periodicCheck(int(time.time()))
    
    def send_mail(self,body_text):         
        SUBJECT = "A new article edit/posted"
        FROM = "info@collegian.in"
        text = body_text
        BODY = string.join((
                "From: %s" % FROM,
                "Subject: %s" % SUBJECT ,
                "",
                text
                ), "\r\n")
        server = smtplib.SMTP("localhost")
        server.sendmail(FROM, ["abhinavabcd@gmail.com","avinash.warrior@gmail.com"], BODY)
        server.quit()


       
class game(tornado.web.RequestHandler):
    def prepare(self):
        pass
    def get(self):
        self.post()
    def post(self):
        uid=self.get_secure_cookie("uid",None)
        if(not uid):
            #self.set_secure_cookie("uid", ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(15)))
            self.redirect("./Login")
            return
        pool_id=self.get_argument("pool_id",None)
        if(not pool_id):
            pool_id="all"

        print "attemted to join "+pool_id
        userScore = self.application.db.get("select * from user_score where uid=%s",uid)                    
        if(not userScore):
            self.application.db.execute("insert into user_score (uid,score) values(%s,%s)",uid,0)      
            userScore = self.application.db.get("select * from user_score where uid=%s",uid)                    
            
        self.render(config.TEMPLATE_MAIN_PAGE,
                    pool_id=pool_id,
                    uid=uid,
                    userScore = userScore.score                  
        )
        

class init_game(tornado.web.RequestHandler):
    def prepare(self):
        self.active=True
        
    def get(self):
        self.post()
    @tornado.web.asynchronous
    def post(self):
        
        uid=self.uid=self.get_secure_cookie("uid")
        pool_id=self.get_argument("pool_id","all")
        print "inside game pool id: "+pool_id
        
        if(not uid):
            self.redirect("./Login")
            return        
        user2=None
        
        #if no pair key then create pair key and add this connection to pair connections , 
        #send msg to the selected friend from selected friend and wait for him
        
        #pair key is present then get user from pair key and check if he's  alive
        
        user_pool=game_pool.get(pool_id,None)
        if(not pool_id):
            self.finish({"exit":"No such Pool"})
            return
        
        while(user_pool):
            user2=user_pool.pop()
            if(user2.active):
                if(self.uid!=user2.uid):
                    print self.uid,user2.uid                
                    break
            user2=None
        
        if(not user2): 
            user_pool.append(self)
            print "sending self to queue"
            return         

        active_user=random.choice([self,user2])            
        game_session =''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(15))            
        rand_user=random.choice([self,user2])
        
        game=sessions[game_session]={
         "current_uid":rand_user.uid,
         "users":{self.uid:[],user2.uid:[]},
         "user_connections":{self.uid:None,user2.uid:None},
         "state":[False for x in range(81)],
         "disposeRef":None,
         "poolType":config.IS_GENERAL_POOL if pool_id=="all" else  config.IS_FB_POOL,
         "poolId":pool_id
        }
        
        addUserCount(2,game["poolType"])
                
        user2.finish({"game_session":game_session,"my_move":"false" if rand_user==user2 else "true" ,"users":[self.uid,user2.uid]})
        self.finish({"game_session":game_session,"my_move":"false" if rand_user==self else "true","users":[self.uid,user2.uid]})
        return

    def on_connection_close(self):
        self.active=False
        tornado.web.RequestHandler.on_connection_close(self)

def sendUpdateMessageToUser(game,uid,message,instant=False):
    try:               
        game["user_connections"][uid].finish({'updates':message})
        return True
    except:
        if(not instant):
            game["users"][uid]+=message
        return False


class update_state(tornado.web.RequestHandler):
    def prepare(self):
        pass
    
    def get(self,game_session):
        self.post(game_session)
        
    @tornado.web.asynchronous    
    def post(self,game_session):
        self.game_session=game_session
        game=sessions.get(game_session,None) 
        if(not game):#game session disposed
            self.finish({"updates":["restart"]})
            return
        
        self.uid=uid=self.get_secure_cookie("uid")
        try:
            index=int(self.get_argument("i",None))
        except:
            self.finish()            
            return
        
        if(index==-1): #request for updates
            if(game["disposeRef"]!=None and game["current_uid"]!=self.uid): # not disposed Yet , user reconnected for whom we are waiting
                game["disposeRef"].dont() #user reconnected dont dispose the session                
                game["disposeRef"]=None
                if(sendUpdateMessageToUser(game, getOtherOne(game["user_connections"].keys(),self.uid), {"updates":["player in","reconnect"]})):#send to waiting user that waiting is over 
                    disposeSession(game_session) # the other user also  left off
                    return
                
            if(not game["users"][uid]): #if no messages pending from server to user
                game["user_connections"][uid]=self
                return            
                
            self.finish({"updates":game["users"][uid]+["reconnect"]})
            game["users"][uid]=[]
            return
        elif(index==-2):
            count=0
            for i in game["state"]:
                if(i):
                    count+=1
            
            if(count==len(game["state"]) and game["current_uid"]==self.uid):
                increaseUserScore(self.application.db,self.uid)
                self.finish({"updates":["done"]})
                return
            
            self.finish({"updates":["error"]})
            return
                            
        if(game["current_uid"]!=uid): #ok update game state and send the status update for the other user and keep this user in wait mode
            if(game["state"][index]!=False):
                self.finish({"updates":["your move"]}) # he is reupdating , some hacking done by user, ban him ? no its okay to spare him
                return
            game["state"][index]=uid
            uid_other=game["current_uid"]
            
            sendUpdateMessageToUser(game, self.uid, {"updates":""},instant=True) #break any previous connection
            
            game["user_connections"][uid]=self
            game["current_uid"]=uid
            sendUpdateMessageToUser(game, uid_other, ["update "+str(index),"your move"])
            sendUpdateMessageToUser(game, uid, ["wait","reconnect"])
            return
        self.finish({"updates":["wait"]})
        
        
    def on_connection_close(self):
        #handle closing
        #inform other user the conneciton close and wait for 1 min on client side until server sends another reconnect back msg
        #dispose the session after 2 min
        print self.uid+" Closed connection"
        game=sessions[self.game_session]
        if(game["current_uid"]==self.uid):            
            userUid = getOtherOne(game["user_connections"].keys(),self.uid)                 
            sendUpdateMessageToUser(game, userUid, ["player gone wait 1 min"]) # send to him when he sends a response inside 1 min
            
            game["disposeRef"]=periodicDeleteQueue.dispose(int(time.time()+60), disposeSession,self.game_session)#set disposal after 2 min
        else:# the users whose current turn is, closed session
            userUid = getOtherOne(game["user_connections"].keys(),self.uid)                 
            sendUpdateMessageToUser(game, userUid, ["player gone wait 1 min"]) # send to him when he sends a response inside 1 min            
            game["disposeRef"]=periodicDeleteQueue.dispose(int(time.time()+60), disposeSession,self.game_session)#set disposal after 2 min

        #sendUpdateMessageToUser(game, uid_other, ["update "+str(index),"your move"])
        
        tornado.web.RequestHandler.on_connection_close(self)    

def getOtherOne(l,a):
    if(len(l)>1):
        if(l[0]!=a):
            return l[0]
        return l[1]

def disposeSession(session):
    addUserCount(-2,sessions[session]["poolType"])
    del sessions[session]

class create_fb_game(tornado.web.RequestHandler):
    # create pair pool key and wait in the queue
    def prepare(self):
        pass
    def get(self):
        self.post()
    def post(self):
        if(not self.get_secure_cookie("uid",None)):
            self.redirect("./Login")
            return
        pool_id=''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(15))
        game_pool[pool_id]=[]
        
        print "created pool and redrected to"+pool_id
        self.redirect("./game?pool_id="+pool_id)        
        
class Login(tornado.web.RequestHandler):    
    def prepare(self):
        pass     
    def get(self):
        self.set_secure_cookie("uid",''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(15)))
        self.render('./html/play_game.html',userCountGeneral=userCount[config.IS_GENERAL_POOL],userCountFb=userCount[config.IS_FB_POOL]) # finish called here
    def post(self):
        pass
    
class fb_login(tornado.web.RequestHandler,tornado.auth.FacebookGraphMixin):
    def prepare(self):
        pass
    @tornado.web.asynchronous
    def get(self):
        if self.get_argument("code", False):
            self.settings["facebook_api_key"]="562371140470794"
            self.settings["facebook_secret"]="12630b784bcb280942915a0380a089e4"
            self.get_authenticated_user(
                redirect_uri='http://www.tic-tac-toe-multiplayer.com/Login',
                client_id=self.settings["facebook_api_key"],
                client_secret=self.settings["facebook_secret"],
                code=self.get_argument("code"),
                callback=self.async_callback(
                self._on_login))
            return
        
        self.authorize_redirect(redirect_uri='http://www.tic-tac-toe-multiplayer.com/Login',
            client_id="562371140470794",
            extra_params={"scope": "read_stream,user_photos"})
        

    def _on_login(self, user):
        if(not user):
            self.redirect("/")
            return
        # set session user_name , etc 
        self.set_secure_cookie("uid",user['id'])        
        self.render('./html/play_game.html',userCountGeneral=userCount[config.IS_GENERAL_POOL],userCountFb=userCount[config.IS_FB_POOL]) # finish called here   
        #user_info=self.get_user_info(user['username']) # user parameters here 
        #if(not user_info)
        #    self.application.db.execute('insert into user_info(user_name,user_info) values(user['user_name'],json.dumps(user))')


def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(_application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()

