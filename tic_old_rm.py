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



define("port", default=8887, help="run on the given port", type=int)
define("mysql_host", default="127.0.0.1:3306", help="database host")
define("mysql_database", default="news_articles_portal", help="database name")
define("mysql_user", default="root", help="database user")
define("mysql_password", default="warrior_within", help="database password")



sessions={}
user_pool=[]

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
            (r"/game", game),                                        
            (r"/init_game", init_game),
            (r"/update_game/(.*)", update_state),
            (r"/html/(.*)", tornado.web.StaticFileHandler,static_path)               
        ]
        tornado.web.Application.__init__(self, handlers, **settings)

        # Have one global connection to the blog DB across all handlers
    #    self.db = tornado.database.Connection(
    #        host=options.mysql_host, database=options.mysql_database,
    #        user=options.mysql_user, password=options.mysql_password)

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
        if(not self.get_secure_cookie("uid",None)):
            self.set_secure_cookie("uid", ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(15)))
        self.render("./www/tictac.html")       

class init_game(tornado.web.RequestHandler):
    def prepare(self):
        self.active=True
        
    def get(self):
        self.post()
    @tornado.web.asynchronous
    def post(self):
        self.uid=self.get_secure_cookie("uid")        
        user2=None
        while(user_pool):
            user2=user_pool.pop()                
            if(user2.active):
                break
        
        if(not user2): 
            user_pool.append(self)
            return         

        active_user=random.choice([self,user2])            
        game_session =''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(15))            
        rand_user=random.choice([self,user2])
        
        sessions[game_session]={
         "current_uid":rand_user.uid,
         "users":{self.uid:[],user2.uid:[]},
         "user_connections":{},
         "state":[[False for x in range(9)] for x in range(9)]
        }
        print sessions
        user2.finish({"game_session":game_session,"my_move":"false" if rand_user==user2 else "true" ,"tic":random.choice([0,1])})
        self.finish({"game_session":game_session,"my_move":"false" if rand_user==self else "true"})
        return

    def on_connection_close(self):
        self.active=False
        tornado.web.RequestHandler.on_connection_close(self)

class update_state(tornado.web.RequestHandler):
    def prepare(self):
        pass
    def get(self,game_session):
        self.post(game_session)
        
    @tornado.web.asynchronous    
    def post(self,game_session):
        self.game_session=game_session
        game=sessions[game_session]        
        uid=self.get_secure_cookie("uid")
        try:
            index=json.loads(self.get_argument("i",None))
        except:
            self.finish()            
            return
        if(not index):
            if(not game["users"][uid]):
                game["user_connections"][uid]=self
                return            
            self.finish({"updates":game["users"][uid]+["reconnect"]})
            game["users"][uid]=[]
            return
        
        if(game["current_uid"]!=uid): #ok update game state and send the status update for the other user and keep this user in wait mode
            if(game["state"][index[0]][index[1]]!=False):
                self.finish({"updates":["your move"]})
                return
            game["state"][index[0]][index[1]]=uid
            uid_other=game["current_uid"]
            game["user_connections"][uid]=self
            game["current_uid"]=uid
            try:               
                game["user_connections"][uid_other].finish({'updates':["update "+json.dumps(index),"your move"]})
            except:
                game["users"][uid_other]+=["update "+json.dumps(index),"your move"]
            self.finish({"updates":["wait","reconnect"]})
            return
        self.finish({"updates":["wait"]})
        
        
    def on_connection_close(self):
        #handle closing
        tornado.web.RequestHandler.on_connection_close(self)    
      

def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(_application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()

